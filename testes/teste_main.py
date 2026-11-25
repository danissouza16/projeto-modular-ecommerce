"""
Módulo testador do Main (módulo principal)
Responsável: grupo

O T2 não define casos de teste para o Main na seção 5; estes casos cobrem
as funções descritas na seção 3.1 (menu, fluxo_catalogo, fluxo_carrinho,
fluxo_compra e fluxo_relatorios) e os requisitos que só o Main garante:
controle de acesso por perfil (RNF02) e aviso da quantidade disponível (RF05).

Organização
- Uma classe de teste por função do Main (M.1 a M.5); cada método é um caso Cn.
- As entradas do usuário são simuladas com unittest.mock.patch em input, e
  a saída da tela é capturada para conferência.
- Os quatro módulos de negócio são os reais (teste de integração), mas ANTES
  DE CADA TESTE o cenário é recriado em uma pasta temporária: os arquivos de
  dados/ nunca são alterados e os relatórios exportados ficam nessa pasta.

Cenário inicial
    Produtos:  P001 Camiseta Basica 49.90 (estoque 10) | P002 Caneca 30.10 (estoque 3)
    Usuários:  admin@loja.com / admin (perfil admin)
               Maria 12345678901 maria@test.com / 123, carrinho P001 x2
               João  98765432100 joao@test.com / 789, carrinho vazio
    Pedidos:   nenhum

Como executar (a partir da pasta raiz do projeto):
    python -m unittest testes.teste_main -v
  ou
    python testes/teste_main.py
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

# Permite rodar o arquivo diretamente (python testes/teste_main.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main                                                   # noqa: E402
from modulos import catalogo_produtos as catalogo             # noqa: E402
from modulos import gerenciador_clientes as clientes          # noqa: E402
from modulos import processador_pedidos as pedidos            # noqa: E402

CPF_MARIA = "12345678901"
CPF_JOAO = "98765432100"

PRODUTOS = [
    {"codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
     "categoria": "Roupas", "preco": 49.90, "estoque": 10},
    {"codigo": "P002", "nome": "Caneca", "descricao": "Ceramica 300ml",
     "categoria": "Utilidades", "preco": 30.10, "estoque": 3},
]

CLIENTES = [
    {"cpf": "00000000001", "nome": "Administrador", "email": "admin@loja.com",
     "senha": "admin", "endereco": "Sede", "perfil": "admin", "carrinho": []},
    {"cpf": CPF_MARIA, "nome": "Maria", "email": "maria@test.com", "senha": "123",
     "endereco": "Rua A", "perfil": "cliente",
     "carrinho": [{"codigo": "P001", "quantidade": 2}]},
    {"cpf": CPF_JOAO, "nome": "João", "email": "joao@test.com", "senha": "789",
     "endereco": "Rua C", "perfil": "cliente", "carrinho": []},
]


def _gravar(pasta, nome, dados):
    caminho = os.path.join(pasta, nome)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return caminho


class BaseMain(unittest.TestCase):
    """Recria o cenário inicial em uma pasta temporária antes de cada teste."""

    def setUp(self):
        originais = (catalogo._CAMINHO_ARQUIVO, clientes._CAMINHO_ARQUIVO,
                     pedidos._CAMINHO_ARQUIVO, os.getcwd())
        self.pasta = tempfile.mkdtemp()

        catalogo._CAMINHO_ARQUIVO = _gravar(self.pasta, "produtos.json", PRODUTOS)
        clientes._CAMINHO_ARQUIVO = _gravar(self.pasta, "clientes.json", CLIENTES)
        pedidos._CAMINHO_ARQUIVO = _gravar(self.pasta, "pedidos.json", [])
        catalogo.CarregarCatalogoDoArq()
        clientes._carregar_clientes_do_arq()
        pedidos._carregar_pedidos_do_arq()
        os.chdir(self.pasta)                 # relatórios exportados ficam aqui

        def restaurar():
            (catalogo._CAMINHO_ARQUIVO, clientes._CAMINHO_ARQUIVO,
             pedidos._CAMINHO_ARQUIVO, pasta_original) = originais
            os.chdir(pasta_original)
            shutil.rmtree(self.pasta, ignore_errors=True)
        self.addCleanup(restaurar)

    def executar(self, funcao, entradas, *args):
        """Chama a função do Main com as entradas simuladas e devolve tudo
        o que foi escrito na tela. Falha se sobrar ou faltar entrada."""
        restantes = list(entradas)

        def falso_input(_mensagem=""):
            if not restantes:
                self.fail("O Main pediu mais entradas do que o teste previu.")
            return restantes.pop(0)

        saida = io.StringIO()
        with patch("builtins.input", side_effect=falso_input), redirect_stdout(saida):
            funcao(*args)
        self.assertEqual(restantes, [], "Sobraram entradas que o Main não leu.")
        return saida.getvalue()

    def pagar_pedido_da_maria(self):
        """Gera e paga por Pix o pedido do carrinho da Maria (P001 x2, 109.80)."""
        pedido = pedidos.CriarPedido(CPF_MARIA)
        self.assertTrue(pedidos.SimularPagamento(pedido, "pix"))
        return pedido


# ==========================================================================
# M.1 menu() -> void
# ==========================================================================

class Teste_M_1_Menu(BaseMain):

    def test_01_login_admin_mostra_relatorios(self):
        print("M.1 C1 - Login do administrador mostra o menu de relatorios")
        tela = self.executar(main.menu, ["1", "admin@loja.com", "admin", "0", "0"])
        self.assertIn("Menu Administrador", tela)
        self.assertIn("Relatórios Gerenciais", tela)

    def test_02_login_cliente_sem_relatorios(self):
        print("M.1 C2 - Login do cliente nao mostra relatorios (RNF02)")
        tela = self.executar(main.menu, ["1", "maria@test.com", "123", "0", "0"])
        self.assertIn("Menu Cliente (Maria)", tela)
        self.assertIn("Compras e Pedidos", tela)
        self.assertNotIn("Relatórios Gerenciais", tela)

    def test_03_credenciais_invalidas(self):
        print("M.1 C3 - Login com senha incorreta")
        tela = self.executar(main.menu, ["1", "maria@test.com", "errada", "0"])
        self.assertIn("E-mail ou senha inválidos.", tela)
        self.assertNotIn("Menu Cliente", tela)

    def test_04_cadastro_de_cliente(self):
        print("M.1 C4 - Cadastro de novo cliente pelo menu inicial")
        tela = self.executar(main.menu, ["2", "11122233344", "Ana", "ana@test.com",
                                         "456", "Rua E", "0"])
        self.assertIn("Cadastro realizado com sucesso!", tela)
        self.assertEqual(clientes.AutenticarCliente("ana@test.com", "456")["perfil"],
                         "cliente")

    def test_05_opcao_invalida(self):
        print("M.1 C5 - Opcao inexistente no menu inicial")
        tela = self.executar(main.menu, ["9", "0"])
        self.assertIn("Opção inválida.", tela)


# ==========================================================================
# M.2 fluxo_catalogo(perfil) -> void
# ==========================================================================

class Teste_M_2_FluxoCatalogo(BaseMain):

    def test_01_cliente_nao_ve_manutencao(self):
        print("M.2 C1 - Cliente nao ve nem executa a manutencao do catalogo (RNF02)")
        tela = self.executar(main.fluxo_catalogo, ["4", "0"], "cliente")
        self.assertNotIn("Cadastrar produto", tela)
        self.assertIn("Opção inválida.", tela)

    def test_02_admin_cadastra_produto(self):
        print("M.2 C2 - Administrador cadastra produto (preco com virgula)")
        tela = self.executar(main.fluxo_catalogo,
                             ["4", "P003", "Bone", "Aba reta", "Acessorios", "39,90", "5", "0"],
                             "admin")
        self.assertIn("Produto cadastrado.", tela)
        self.assertEqual(catalogo.BuscarProduto("P003")["preco"], 39.90)

    def test_03_admin_repoe_estoque(self):
        print("M.2 C3 - Administrador repoe estoque")
        tela = self.executar(main.fluxo_catalogo, ["7", "P002", "5", "0"], "admin")
        self.assertIn("Estoque reposto.", tela)
        self.assertEqual(catalogo.ConsultarEstoque("P002"), 8)

    def test_04_busca_por_nome(self):
        print("M.2 C4 - Busca por parte do nome mostra preco e estoque (RF03)")
        tela = self.executar(main.fluxo_catalogo, ["3", "cami", "0"], "cliente")
        self.assertIn("[P001] Camiseta Basica", tela)
        self.assertIn("estoque: 10", tela)


# ==========================================================================
# M.3 fluxo_carrinho(cpf) -> void
# ==========================================================================

class Teste_M_3_FluxoCarrinho(BaseMain):

    def test_01_adicionar_item(self):
        print("M.3 C1 - Adicao valida de item ao carrinho")
        tela = self.executar(main.fluxo_carrinho, ["2", "P002", "1", "0"], CPF_JOAO)
        self.assertIn("Item adicionado ao carrinho.", tela)
        self.assertEqual(clientes.ObterCarrinho(CPF_JOAO)[0]["codigo"], "P002")

    def test_02_adicionar_sem_estoque_informa_disponivel(self):
        print("M.3 C2 - Adicao acima do estoque informa a quantidade disponivel (RF05)")
        tela = self.executar(main.fluxo_carrinho, ["2", "P002", "5", "0"], CPF_JOAO)
        self.assertIn("Quantidade disponível de Caneca: 3 (no seu carrinho: 0).", tela)
        self.assertEqual(clientes.ObterCarrinho(CPF_JOAO), [])

    def test_03_alterar_sem_estoque_informa_disponivel(self):
        print("M.3 C3 - Alteracao acima do estoque informa a quantidade disponivel (RF05)")
        tela = self.executar(main.fluxo_carrinho, ["3", "P001", "50", "0"], CPF_MARIA)
        self.assertIn("Quantidade disponível de Camiseta Basica: 10 (no seu carrinho: 2).", tela)

    def test_04_ver_carrinho_com_subtotal(self):
        print("M.3 C4 - Visualizacao do carrinho com subtotal")
        tela = self.executar(main.fluxo_carrinho, ["1", "0"], CPF_MARIA)
        self.assertIn("Subtotal do carrinho: R$ 99.80", tela)


# ==========================================================================
# M.4 fluxo_compra(cpf) -> void
# ==========================================================================

class Teste_M_4_FluxoCompra(BaseMain):

    def test_01_compra_aprovada(self):
        print("M.4 C1 - Finaliza a compra e paga por Pix (RF06 a RF08)")
        tela = self.executar(main.fluxo_compra, ["1", "pix", "0"], CPF_MARIA)
        self.assertIn("Pagamento aprovado! Pedido nº 1 pago.", tela)
        self.assertEqual(pedidos.ListarPedidosCliente(CPF_MARIA)[0]["status"], "Pago")
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 8)
        self.assertEqual(clientes.ObterCarrinho(CPF_MARIA), [])

    def test_02_pagamento_recusado(self):
        print("M.4 C2 - Boleto abaixo do minimo e recusado: pedido cancelado, estoque igual")
        self.assertTrue(clientes.AdicionarItemCarrinho(CPF_JOAO, "P002", 1))  # total 40.10
        tela = self.executar(main.fluxo_compra, ["1", "boleto", "0"], CPF_JOAO)
        self.assertIn("Pagamento recusado (boleto).", tela)
        self.assertEqual(pedidos.ListarPedidosCliente(CPF_JOAO)[0]["status"], "Cancelado")
        self.assertEqual(catalogo.ConsultarEstoque("P002"), 3)
        self.assertEqual(len(clientes.ObterCarrinho(CPF_JOAO)), 1)

    def test_03_pagar_depois_bloqueia_novo_pedido(self):
        print("M.4 C3 - Pedido aguardando pagamento impede gerar outro igual")
        tela = self.executar(main.fluxo_compra, ["1", "", "1", "0"], CPF_MARIA)
        self.assertIn("Pedido nº 1 continua aguardando pagamento.", tela)
        self.assertIn("Você já tem o pedido nº 1 aguardando", tela)
        self.assertEqual(len(pedidos.ListarPedidosCliente(CPF_MARIA)), 1)

    def test_04_pagar_pedido_pendente(self):
        print("M.4 C4 - Pagamento posterior de pedido pendente")
        tela = self.executar(main.fluxo_compra, ["1", "", "2", "1", "cartao", "0"], CPF_MARIA)
        self.assertIn("Pagamento aprovado! Pedido nº 1 pago.", tela)
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 8)

    def test_05_cancelar_pedido_pago(self):
        print("M.4 C5 - Cancelamento de pedido pago devolve o estoque (RF09)")
        tela = self.executar(main.fluxo_compra, ["1", "pix", "4", "1", "0"], CPF_MARIA)
        self.assertIn("Pedido nº 1 cancelado.", tela)
        self.assertEqual(pedidos.ListarPedidosCliente(CPF_MARIA)[0]["status"], "Cancelado")
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 10)

    def test_06_nao_cancela_pedido_de_outro_cliente(self):
        print("M.4 C6 - Cliente nao consegue cancelar pedido de outro cliente")
        self.assertTrue(clientes.AdicionarItemCarrinho(CPF_JOAO, "P002", 1))
        pedido_joao = pedidos.CriarPedido(CPF_JOAO)                # pedido nº 1
        self.assertTrue(pedidos.SimularPagamento(pedido_joao, "pix"))
        self.assertTrue(pedidos.CriarPedido(CPF_MARIA))            # pedido nº 2
        tela = self.executar(main.fluxo_compra, ["4", "1", "0"], CPF_MARIA)
        self.assertIn("Pedido não encontrado entre os seus pedidos.", tela)
        self.assertEqual(pedidos.ListarPedidosCliente(CPF_JOAO)[0]["status"], "Pago")

    def test_07_forma_de_pagamento_invalida(self):
        print("M.4 C7 - Forma de pagamento invalida e pedida de novo")
        tela = self.executar(main.fluxo_compra, ["1", "dinheiro", "pix", "0"], CPF_MARIA)
        self.assertIn("Forma de pagamento inválida.", tela)
        self.assertIn("Pagamento aprovado!", tela)


# ==========================================================================
# M.5 fluxo_relatorios() -> void
# ==========================================================================

class Teste_M_5_FluxoRelatorios(BaseMain):

    def test_01_faturamento(self):
        print("M.5 C1 - Faturamento por periodo")
        self.pagar_pedido_da_maria()
        tela = self.executar(main.fluxo_relatorios,
                             ["1", "2000-01-01", "2100-12-31", "n", "0"])
        self.assertIn("Faturamento de 2000-01-01 a 2100-12-31: R$ 109.80", tela)

    def test_02_ticket_medio(self):
        print("M.5 C2 - Ticket medio por periodo")
        self.pagar_pedido_da_maria()
        tela = self.executar(main.fluxo_relatorios,
                             ["2", "2000-01-01", "2100-12-31", "n", "0"])
        self.assertIn("Ticket médio de 2000-01-01 a 2100-12-31: R$ 109.80", tela)

    def test_03_mais_vendidos_com_exportacao(self):
        print("M.5 C3 - Mais vendidos exportado para arquivo (RF10)")
        self.pagar_pedido_da_maria()
        tela = self.executar(main.fluxo_relatorios,
                             ["3", "5", "s", "mais_vendidos.txt", "0"])
        self.assertIn("1º [P001] Camiseta Basica - 2 un.", tela)
        self.assertIn("Relatório exportado para mais_vendidos.txt.", tela)
        with open(os.path.join(self.pasta, "mais_vendidos.txt"), encoding="utf-8") as arq:
            self.assertIn("codigo: P001", arq.read())

    def test_04_vendas_por_cliente(self):
        print("M.5 C4 - Vendas por cliente")
        self.pagar_pedido_da_maria()
        tela = self.executar(main.fluxo_relatorios, ["4", CPF_MARIA, "n", "0"])
        self.assertIn("Pedido nº 1", tela)
        self.assertIn("R$ 109.80", tela)

    def test_05_estoque_baixo(self):
        print("M.5 C5 - Produtos com estoque baixo")
        tela = self.executar(main.fluxo_relatorios, ["5", "3", "n", "0"])
        self.assertIn("[P002] Caneca", tela)
        self.assertNotIn("[P001]", tela)

    def test_06_parametro_invalido(self):
        print("M.5 C6 - Quantidade nao numerica no ranking nao quebra o menu")
        tela = self.executar(main.fluxo_relatorios, ["3", "abc", "0"])
        self.assertIn("Nenhuma venda encontrada (ou n inválido).", tela)


if __name__ == "__main__":
    unittest.main(verbosity=2)
