"""
Módulo testador do Main (módulo principal)
Responsável: grupo

O T2 não define casos de teste para o Main na seção 5; estes casos cobrem
as funções descritas na seção 3.1 (menu, fluxo_catalogo, fluxo_carrinho,
fluxo_compra e fluxo_relatorios) e os requisitos que só o Main garante:
controle de acesso por perfil (RNF02) e aviso da quantidade disponível (RF05).

Organização
- Sem classes: cada caso Cn é uma função; os casos de cada função do Main
  (M.1 a M.5) formam um grupo na lista GRUPOS, montada por
  testes/suite_funcoes.py com unittest.FunctionTestCase.
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
from testes.suite_funcoes import grupo, montar_suite, verifica   # noqa: E402

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

# --------------------------------------------------------------------------
# Preparação e limpeza do cenário (rodam antes e depois de CADA caso)
# --------------------------------------------------------------------------

_ctx = {}         # pasta temporária do caso atual
_limpezas = []    # ações de limpeza, desfeitas na ordem inversa


def preparar_cenario():
    """Recria produtos, clientes e pedidos numa pasta temporária e recarrega
    os três módulos com arquivo; os relatórios exportados ficam nessa pasta."""
    originais = (catalogo._CAMINHO_ARQUIVO, clientes._CAMINHO_ARQUIVO,
                 pedidos._CAMINHO_ARQUIVO, os.getcwd())
    pasta = tempfile.mkdtemp()
    _ctx["pasta"] = pasta

    catalogo._CAMINHO_ARQUIVO = _gravar(pasta, "produtos.json", PRODUTOS)
    clientes._CAMINHO_ARQUIVO = _gravar(pasta, "clientes.json", CLIENTES)
    pedidos._CAMINHO_ARQUIVO = _gravar(pasta, "pedidos.json", [])
    catalogo.CarregarCatalogoDoArq()
    clientes._carregar_clientes_do_arq()
    pedidos._carregar_pedidos_do_arq()
    os.chdir(pasta)

    def restaurar():
        (catalogo._CAMINHO_ARQUIVO, clientes._CAMINHO_ARQUIVO,
         pedidos._CAMINHO_ARQUIVO, pasta_original) = originais
        os.chdir(pasta_original)
        shutil.rmtree(pasta, ignore_errors=True)
    _limpezas.append(restaurar)


def limpar_cenario():
    while _limpezas:
        _limpezas.pop()()


def executar(funcao, entradas, *args):
    """Chama a função do Main com as entradas simuladas e devolve tudo
    o que foi escrito na tela. Falha se sobrar ou faltar entrada."""
    restantes = list(entradas)

    def falso_input(_mensagem=""):
        if not restantes:
            verifica.fail("O Main pediu mais entradas do que o teste previu.")
        return restantes.pop(0)

    saida = io.StringIO()
    with patch("builtins.input", side_effect=falso_input), redirect_stdout(saida):
        funcao(*args)
    verifica.assertEqual(restantes, [], "Sobraram entradas que o Main não leu.")
    return saida.getvalue()


def pagar_pedido_da_maria():
    """Gera e paga por Pix o pedido do carrinho da Maria (P001 x2, 109.80)."""
    pedido = pedidos.CriarPedido(CPF_MARIA)
    verifica.assertTrue(pedidos.SimularPagamento(pedido, "pix"))
    return pedido



# ==========================================================================
# M.1 menu() -> void
# ==========================================================================


def caso_M_1_01_login_admin_mostra_relatorios():
    print("M.1 C1 - Login do administrador mostra o menu de relatorios")
    tela = executar(main.menu, ["1", "admin@loja.com", "admin", "0", "0"])
    verifica.assertIn("Menu Administrador", tela)
    verifica.assertIn("Relatórios Gerenciais", tela)


def caso_M_1_02_login_cliente_sem_relatorios():
    print("M.1 C2 - Login do cliente nao mostra relatorios (RNF02)")
    tela = executar(main.menu, ["1", "maria@test.com", "123", "0", "0"])
    verifica.assertIn("Menu Cliente (Maria)", tela)
    verifica.assertIn("Compras e Pedidos", tela)
    verifica.assertNotIn("Relatórios Gerenciais", tela)


def caso_M_1_03_credenciais_invalidas():
    print("M.1 C3 - Login com senha incorreta")
    tela = executar(main.menu, ["1", "maria@test.com", "errada", "0"])
    verifica.assertIn("E-mail ou senha inválidos.", tela)
    verifica.assertNotIn("Menu Cliente", tela)


def caso_M_1_04_cadastro_de_cliente():
    print("M.1 C4 - Cadastro de novo cliente pelo menu inicial")
    tela = executar(main.menu, ["2", "11122233344", "Ana", "ana@test.com",
                                     "456", "Rua E", "0"])
    verifica.assertIn("Cadastro realizado com sucesso!", tela)
    verifica.assertEqual(clientes.AutenticarCliente("ana@test.com", "456")["perfil"],
                     "cliente")


def caso_M_1_05_opcao_invalida():
    print("M.1 C5 - Opcao inexistente no menu inicial")
    tela = executar(main.menu, ["9", "0"])
    verifica.assertIn("Opção inválida.", tela)


# ==========================================================================
# M.2 fluxo_catalogo(perfil) -> void
# ==========================================================================


def caso_M_2_01_cliente_nao_ve_manutencao():
    print("M.2 C1 - Cliente nao ve nem executa a manutencao do catalogo (RNF02)")
    tela = executar(main.fluxo_catalogo, ["4", "0"], "cliente")
    verifica.assertNotIn("Cadastrar produto", tela)
    verifica.assertIn("Opção inválida.", tela)


def caso_M_2_02_admin_cadastra_produto():
    print("M.2 C2 - Administrador cadastra produto (preco com virgula)")
    tela = executar(main.fluxo_catalogo,
                         ["4", "P003", "Bone", "Aba reta", "Acessorios", "39,90", "5", "0"],
                         "admin")
    verifica.assertIn("Produto cadastrado.", tela)
    verifica.assertEqual(catalogo.BuscarProduto("P003")["preco"], 39.90)


def caso_M_2_03_admin_repoe_estoque():
    print("M.2 C3 - Administrador repoe estoque")
    tela = executar(main.fluxo_catalogo, ["7", "P002", "5", "0"], "admin")
    verifica.assertIn("Estoque reposto.", tela)
    verifica.assertEqual(catalogo.ConsultarEstoque("P002"), 8)


def caso_M_2_04_busca_por_nome():
    print("M.2 C4 - Busca por parte do nome mostra preco e estoque (RF03)")
    tela = executar(main.fluxo_catalogo, ["3", "cami", "0"], "cliente")
    verifica.assertIn("[P001] Camiseta Basica", tela)
    verifica.assertIn("estoque: 10", tela)


# ==========================================================================
# M.3 fluxo_carrinho(cpf) -> void
# ==========================================================================


def caso_M_3_01_adicionar_item():
    print("M.3 C1 - Adicao valida de item ao carrinho")
    tela = executar(main.fluxo_carrinho, ["2", "P002", "1", "0"], CPF_JOAO)
    verifica.assertIn("Item adicionado ao carrinho.", tela)
    verifica.assertEqual(clientes.ObterCarrinho(CPF_JOAO)[0]["codigo"], "P002")


def caso_M_3_02_adicionar_sem_estoque_informa_disponivel():
    print("M.3 C2 - Adicao acima do estoque informa a quantidade disponivel (RF05)")
    tela = executar(main.fluxo_carrinho, ["2", "P002", "5", "0"], CPF_JOAO)
    verifica.assertIn("Quantidade disponível de Caneca: 3 (no seu carrinho: 0).", tela)
    verifica.assertEqual(clientes.ObterCarrinho(CPF_JOAO), [])


def caso_M_3_03_alterar_sem_estoque_informa_disponivel():
    print("M.3 C3 - Alteracao acima do estoque informa a quantidade disponivel (RF05)")
    tela = executar(main.fluxo_carrinho, ["3", "P001", "50", "0"], CPF_MARIA)
    verifica.assertIn("Quantidade disponível de Camiseta Basica: 10 (no seu carrinho: 2).", tela)


def caso_M_3_04_ver_carrinho_com_subtotal():
    print("M.3 C4 - Visualizacao do carrinho com subtotal")
    tela = executar(main.fluxo_carrinho, ["1", "0"], CPF_MARIA)
    verifica.assertIn("Subtotal do carrinho: R$ 99.80", tela)


# ==========================================================================
# M.4 fluxo_compra(cpf) -> void
# ==========================================================================


def caso_M_4_01_compra_aprovada():
    print("M.4 C1 - Finaliza a compra e paga por Pix (RF06 a RF08)")
    tela = executar(main.fluxo_compra, ["1", "pix", "0"], CPF_MARIA)
    verifica.assertIn("Pagamento aprovado! Pedido nº 1 pago.", tela)
    verifica.assertEqual(pedidos.ListarPedidosCliente(CPF_MARIA)[0]["status"], "Pago")
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 8)
    verifica.assertEqual(clientes.ObterCarrinho(CPF_MARIA), [])


def caso_M_4_02_pagamento_recusado():
    print("M.4 C2 - Boleto abaixo do minimo e recusado: pedido cancelado, estoque igual")
    verifica.assertTrue(clientes.AdicionarItemCarrinho(CPF_JOAO, "P002", 1))  # total 40.10
    tela = executar(main.fluxo_compra, ["1", "boleto", "0"], CPF_JOAO)
    verifica.assertIn("Pagamento recusado (boleto).", tela)
    verifica.assertEqual(pedidos.ListarPedidosCliente(CPF_JOAO)[0]["status"], "Cancelado")
    verifica.assertEqual(catalogo.ConsultarEstoque("P002"), 3)
    verifica.assertEqual(len(clientes.ObterCarrinho(CPF_JOAO)), 1)


def caso_M_4_03_pagar_depois_bloqueia_novo_pedido():
    print("M.4 C3 - Pedido aguardando pagamento impede gerar outro igual")
    tela = executar(main.fluxo_compra, ["1", "", "1", "0"], CPF_MARIA)
    verifica.assertIn("Pedido nº 1 continua aguardando pagamento.", tela)
    verifica.assertIn("Você já tem o pedido nº 1 aguardando", tela)
    verifica.assertEqual(len(pedidos.ListarPedidosCliente(CPF_MARIA)), 1)


def caso_M_4_04_pagar_pedido_pendente():
    print("M.4 C4 - Pagamento posterior de pedido pendente")
    tela = executar(main.fluxo_compra, ["1", "", "2", "1", "cartao", "0"], CPF_MARIA)
    verifica.assertIn("Pagamento aprovado! Pedido nº 1 pago.", tela)
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 8)


def caso_M_4_05_cancelar_pedido_pago():
    print("M.4 C5 - Cancelamento de pedido pago devolve o estoque (RF09)")
    tela = executar(main.fluxo_compra, ["1", "pix", "4", "1", "0"], CPF_MARIA)
    verifica.assertIn("Pedido nº 1 cancelado.", tela)
    verifica.assertEqual(pedidos.ListarPedidosCliente(CPF_MARIA)[0]["status"], "Cancelado")
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 10)


def caso_M_4_06_nao_cancela_pedido_de_outro_cliente():
    print("M.4 C6 - Cliente nao consegue cancelar pedido de outro cliente")
    verifica.assertTrue(clientes.AdicionarItemCarrinho(CPF_JOAO, "P002", 1))
    pedido_joao = pedidos.CriarPedido(CPF_JOAO)                # pedido nº 1
    verifica.assertTrue(pedidos.SimularPagamento(pedido_joao, "pix"))
    verifica.assertTrue(pedidos.CriarPedido(CPF_MARIA))            # pedido nº 2
    tela = executar(main.fluxo_compra, ["4", "1", "0"], CPF_MARIA)
    verifica.assertIn("Pedido não encontrado entre os seus pedidos.", tela)
    verifica.assertEqual(pedidos.ListarPedidosCliente(CPF_JOAO)[0]["status"], "Pago")


def caso_M_4_07_forma_de_pagamento_invalida():
    print("M.4 C7 - Forma de pagamento invalida e pedida de novo")
    tela = executar(main.fluxo_compra, ["1", "dinheiro", "pix", "0"], CPF_MARIA)
    verifica.assertIn("Forma de pagamento inválida.", tela)
    verifica.assertIn("Pagamento aprovado!", tela)


# ==========================================================================
# M.5 fluxo_relatorios() -> void
# ==========================================================================


def caso_M_5_01_faturamento():
    print("M.5 C1 - Faturamento por periodo")
    pagar_pedido_da_maria()
    tela = executar(main.fluxo_relatorios,
                         ["1", "2000-01-01", "2100-12-31", "n", "0"])
    verifica.assertIn("Faturamento de 2000-01-01 a 2100-12-31: R$ 109.80", tela)


def caso_M_5_02_ticket_medio():
    print("M.5 C2 - Ticket medio por periodo")
    pagar_pedido_da_maria()
    tela = executar(main.fluxo_relatorios,
                         ["2", "2000-01-01", "2100-12-31", "n", "0"])
    verifica.assertIn("Ticket médio de 2000-01-01 a 2100-12-31: R$ 109.80", tela)


def caso_M_5_03_mais_vendidos_com_exportacao():
    print("M.5 C3 - Mais vendidos exportado para arquivo (RF10)")
    pagar_pedido_da_maria()
    tela = executar(main.fluxo_relatorios,
                         ["3", "5", "s", "mais_vendidos.txt", "0"])
    verifica.assertIn("1º [P001] Camiseta Basica - 2 un.", tela)
    verifica.assertIn("Relatório exportado para mais_vendidos.txt.", tela)
    with open(os.path.join(_ctx["pasta"], "mais_vendidos.txt"), encoding="utf-8") as arq:
        verifica.assertIn("codigo: P001", arq.read())


def caso_M_5_04_vendas_por_cliente():
    print("M.5 C4 - Vendas por cliente")
    pagar_pedido_da_maria()
    tela = executar(main.fluxo_relatorios, ["4", CPF_MARIA, "n", "0"])
    verifica.assertIn("Pedido nº 1", tela)
    verifica.assertIn("R$ 109.80", tela)


def caso_M_5_05_estoque_baixo():
    print("M.5 C5 - Produtos com estoque baixo")
    tela = executar(main.fluxo_relatorios, ["5", "3", "n", "0"])
    verifica.assertIn("[P002] Caneca", tela)
    verifica.assertNotIn("[P001]", tela)


def caso_M_5_06_parametro_invalido():
    print("M.5 C6 - Quantidade nao numerica no ranking nao quebra o menu")
    tela = executar(main.fluxo_relatorios, ["3", "abc", "0"])
    verifica.assertIn("Nenhuma venda encontrada (ou n inválido).", tela)

# ==========================================================================
# Ordem de execução: um grupo por função, casos na ordem C1, C2, ...
# ==========================================================================

GRUPOS = [
    # M.1 menu() -> void
    grupo([
        caso_M_1_01_login_admin_mostra_relatorios,
        caso_M_1_02_login_cliente_sem_relatorios,
        caso_M_1_03_credenciais_invalidas,
        caso_M_1_04_cadastro_de_cliente,
        caso_M_1_05_opcao_invalida,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # M.2 fluxo_catalogo(perfil) -> void
    grupo([
        caso_M_2_01_cliente_nao_ve_manutencao,
        caso_M_2_02_admin_cadastra_produto,
        caso_M_2_03_admin_repoe_estoque,
        caso_M_2_04_busca_por_nome,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # M.3 fluxo_carrinho(cpf) -> void
    grupo([
        caso_M_3_01_adicionar_item,
        caso_M_3_02_adicionar_sem_estoque_informa_disponivel,
        caso_M_3_03_alterar_sem_estoque_informa_disponivel,
        caso_M_3_04_ver_carrinho_com_subtotal,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # M.4 fluxo_compra(cpf) -> void
    grupo([
        caso_M_4_01_compra_aprovada,
        caso_M_4_02_pagamento_recusado,
        caso_M_4_03_pagar_depois_bloqueia_novo_pedido,
        caso_M_4_04_pagar_pedido_pendente,
        caso_M_4_05_cancelar_pedido_pago,
        caso_M_4_06_nao_cancela_pedido_de_outro_cliente,
        caso_M_4_07_forma_de_pagamento_invalida,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # M.5 fluxo_relatorios() -> void
    grupo([
        caso_M_5_01_faturamento,
        caso_M_5_02_ticket_medio,
        caso_M_5_03_mais_vendidos_com_exportacao,
        caso_M_5_04_vendas_por_cliente,
        caso_M_5_05_estoque_baixo,
        caso_M_5_06_parametro_invalido,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
]


def load_tests(loader, testes_padrao, padrao):
    """Chamada pelo unittest (discover ou execução direta) para montar a suíte."""
    return montar_suite(GRUPOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
