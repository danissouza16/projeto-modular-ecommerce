"""
Módulo testador do ProcessadorPedidos (Módulo 3)
Responsáveis: Brenno Távora e Guilherme Meira

Implementa os casos de teste da seção 5.3 do documento do projeto (T2),
incluindo as funções internas 3.2, 3.4, 3.6 e 3.9.

Organização
- Uma classe de teste por função (3.1 a 3.9); cada método é um caso Cn.
- ANTES DE CADA TESTE o cenário inicial é recriado em uma pasta temporária,
  então os casos não dependem da ordem e nunca mexem em dados/pedidos.json.
- O CatalogoProdutos (1.7, 1.8, 1.9) e o GerenciadorClientes (2.8, 2.10)
  são simulados via unittest.mock.patch, com um estoque e carrinhos
  em memória (ver BasePedidos).

Cenário inicial
    Estoque:   P001 = 10, P002 = 3
    Carrinhos: Maria (12345678901) P001 x2 | João (98765432100) vazio |
               Ana (11122233344) P002 x3
    Pedidos (pedidos.json): 1 Maria Pago | 2 Maria Aguardando |
               3 João Cancelado | 4 e 5 João Aguardando
    Frete fixo 10.00, desconto 0.00.

Como executar (a partir da pasta raiz do projeto):
    python -m unittest testes.teste_processador_pedidos -v
  ou
    python testes/teste_processador_pedidos.py
"""

import copy
import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Permite rodar o arquivo diretamente (python testes/teste_processador_pedidos.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos import processador_pedidos as pedidos   # noqa: E402

CPF_MARIA = "12345678901"
CPF_JOAO = "98765432100"
CPF_ANA = "11122233344"

ITEM_P001 = {"codigo": "P001", "nome": "Camiseta Basica", "preco": 49.90}
ITEM_P002 = {"codigo": "P002", "nome": "Caneca", "preco": 30.10}


def _item(base, quantidade):
    item = dict(base)
    item["quantidade"] = quantidade
    return item


def _pedido(numero, cpf, data, itens, total, status):
    subtotal = round(total - 10.00, 2)
    return {"numero": numero, "cpf": cpf, "data": data, "itens": itens,
            "subtotal": subtotal, "frete": 10.00, "desconto": 0.0,
            "total": total, "status": status}


CENARIO_INICIAL = [
    _pedido(1, CPF_MARIA, "2026-09-10", [_item(ITEM_P001, 2)], 109.80, "Pago"),
    _pedido(2, CPF_MARIA, "2026-09-20", [_item(ITEM_P002, 1)], 40.10, "Aguardando pagamento"),
    _pedido(3, CPF_JOAO, "2026-10-05", [_item(ITEM_P001, 1)], 59.90, "Cancelado"),
    _pedido(4, CPF_JOAO, "2026-10-08", [_item(ITEM_P001, 1)], 59.90, "Aguardando pagamento"),
    _pedido(5, CPF_JOAO, "2026-10-10", [_item(ITEM_P001, 10)], 509.00, "Aguardando pagamento"),
]


def montar_cenario_inicial(pasta):
    """Grava o cenário em <pasta>/pedidos.json, redireciona o módulo
    e recarrega os dados."""
    caminho = os.path.join(pasta, "pedidos.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(CENARIO_INICIAL, arquivo, ensure_ascii=False, indent=2)
    pedidos._CAMINHO_ARQUIVO = caminho      # redireciona só durante os testes
    pedidos._carregar_pedidos_do_arq()
    return caminho


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


class BasePedidos(unittest.TestCase):
    """Recria o cenário (pedidos, estoque e carrinhos) antes de cada teste."""

    def setUp(self):
        caminho_original = pedidos._CAMINHO_ARQUIVO
        self.pasta = tempfile.mkdtemp()
        self.arquivo = montar_cenario_inicial(self.pasta)

        def restaurar():
            pedidos._CAMINHO_ARQUIVO = caminho_original
            shutil.rmtree(self.pasta, ignore_errors=True)
        self.addCleanup(restaurar)

        self.estoque = {"P001": 10, "P002": 3}
        self.carrinhos = {
            CPF_MARIA: [_item(ITEM_P001, 2)],
            CPF_JOAO: [],
            CPF_ANA: [_item(ITEM_P002, 3)],
        }
        for alvo, simulacao in (
            ("modulos.catalogo_produtos.ConsultarEstoque", self._consultar_estoque),
            ("modulos.catalogo_produtos.BaixarEstoque", self._baixar_estoque),
            ("modulos.catalogo_produtos.ReporEstoque", self._repor_estoque),
            ("modulos.gerenciador_clientes.ObterCarrinho", self._obter_carrinho),
            ("modulos.gerenciador_clientes.EsvaziarCarrinho", self._esvaziar_carrinho),
        ):
            patcher = patch(alvo, side_effect=simulacao)
            patcher.start()
            self.addCleanup(patcher.stop)

    # --- simulações do Módulo 1 (CatalogoProdutos) -------------------------

    def _consultar_estoque(self, codigo):
        return self.estoque.get(codigo, -1)

    def _baixar_estoque(self, codigo, qtd):
        if codigo not in self.estoque or qtd <= 0 or qtd > self.estoque[codigo]:
            return False
        self.estoque[codigo] -= qtd
        return True

    def _repor_estoque(self, codigo, qtd):
        if codigo not in self.estoque or qtd <= 0:
            return False
        self.estoque[codigo] += qtd
        return True

    # --- simulações do Módulo 2 (GerenciadorClientes) ----------------------

    def _obter_carrinho(self, cpf):
        return copy.deepcopy(self.carrinhos.get(cpf, []))

    def _esvaziar_carrinho(self, cpf):
        if cpf not in self.carrinhos:
            return False
        self.carrinhos[cpf] = []
        return True


# ==========================================================================
# 3.1 CriarPedido(cpf: str) -> dict
# ==========================================================================

class Teste_3_1_CriarPedido(BasePedidos):

    def test_01_carrinho_valido_e_estoque_suficiente(self):
        print("3.1 C1 - Criacao de pedido com carrinho valido e estoque suficiente")
        resultado = pedidos.CriarPedido(CPF_MARIA)
        self.assertEqual(resultado["numero"], 6)
        self.assertEqual(resultado["cpf"], CPF_MARIA)
        self.assertEqual(resultado["data"], datetime.date.today().isoformat())
        self.assertEqual(resultado["itens"], [_item(ITEM_P001, 2)])
        self.assertAlmostEqual(resultado["subtotal"], 99.80)
        self.assertAlmostEqual(resultado["frete"], 10.00)
        self.assertAlmostEqual(resultado["desconto"], 0.0)
        self.assertAlmostEqual(resultado["total"], 109.80)
        self.assertEqual(resultado["status"], "Aguardando pagamento")
        self.assertEqual(len(ler_arquivo(self.arquivo)), 6)

    def test_02_carrinho_vazio(self):
        print("3.1 C2 - Criacao com carrinho vazio")
        self.assertEqual(pedidos.CriarPedido(CPF_JOAO), {})
        self.assertEqual(len(ler_arquivo(self.arquivo)), 5)

    def test_03_estoque_insuficiente(self):
        print("3.1 C3 - Criacao com estoque insuficiente em algum item")
        self.assertTrue(self._baixar_estoque("P002", 1))    # estoque 3 -> 2
        self.assertEqual(self.estoque["P002"], 2)
        self.assertEqual(pedidos.CriarPedido(CPF_ANA), {})
        self.assertEqual(len(ler_arquivo(self.arquivo)), 5)

    def test_04_cliente_inexistente(self):
        print("3.1 C4 - Criacao para cliente inexistente")
        self.assertEqual(pedidos.CriarPedido("00000000000"), {})


# ==========================================================================
# 3.2 CalcularTotal(itens: list, frete: float, desconto: float) -> float (interna)
# ==========================================================================

class Teste_3_2_CalcularTotal(BasePedidos):

    ITENS = [{"codigo": "P001", "preco": 49.90, "quantidade": 2}]

    def test_01_itens_e_frete_sem_desconto(self):
        print("3.2 C1 - Calculo com itens, frete e sem desconto")
        self.assertAlmostEqual(pedidos.CalcularTotal(self.ITENS, 10.0, 0.0), 109.80)

    def test_02_itens_frete_e_desconto(self):
        print("3.2 C2 - Calculo com itens, frete e desconto")
        self.assertAlmostEqual(pedidos.CalcularTotal(self.ITENS, 10.0, 5.0), 104.80)

    def test_03_lista_vazia(self):
        print("3.2 C3 - Lista de itens vazia")
        self.assertEqual(pedidos.CalcularTotal([], 10.0, 0.0), 0.0)

    def test_04_frete_negativo(self):
        print("3.2 C4 - Frete negativo")
        self.assertEqual(pedidos.CalcularTotal(self.ITENS, -10.0, 0.0), 0.0)

    def test_05_desconto_negativo(self):
        print("3.2 C5 - Desconto negativo")
        self.assertEqual(pedidos.CalcularTotal(self.ITENS, 10.0, -5.0), 0.0)


# ==========================================================================
# 3.3 SimularPagamento(pedido: dict, forma: str) -> bool
# ==========================================================================

class Teste_3_3_SimularPagamento(BasePedidos):

    def test_01_pix_aprovado(self):
        print("3.3 C1 - Pagamento aprovado via Pix")
        self.carrinhos[CPF_MARIA] = [_item(ITEM_P001, 2)]
        self.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(2), "pix"))
        self.assertEqual(pedidos.BuscarPedido(2)["status"], "Pago")
        self.assertEqual(self.estoque["P002"], 2)
        self.assertEqual(self.carrinhos[CPF_MARIA], [])

    def test_02_cartao_aprovado(self):
        print("3.3 C2 - Pagamento aprovado via cartao")
        self.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(4), "cartao"))
        self.assertEqual(pedidos.BuscarPedido(4)["status"], "Pago")
        self.assertEqual(self.estoque["P001"], 9)

    def test_03_boleto_aprovado(self):
        print("3.3 C3 - Pagamento aprovado via boleto")
        self.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(5), "boleto"))
        self.assertEqual(pedidos.BuscarPedido(5)["status"], "Pago")
        self.assertEqual(self.estoque["P001"], 0)

    def test_04_cartao_recusado_acima_do_limite(self):
        print("3.3 C4 - Pagamento recusado via cartao (total acima do limite)")
        self.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(5), "cartao"))
        self.assertEqual(pedidos.BuscarPedido(5)["status"], "Cancelado")
        self.assertEqual(self.estoque["P001"], 10)

    def test_05_boleto_recusado_abaixo_do_minimo(self):
        print("3.3 C5 - Pagamento recusado via boleto (total abaixo do minimo)")
        self.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(2), "boleto"))
        self.assertEqual(pedidos.BuscarPedido(2)["status"], "Cancelado")
        self.assertEqual(self.estoque["P002"], 3)

    def test_06_forma_de_pagamento_invalida(self):
        print("3.3 C6 - Forma de pagamento invalida")
        self.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(4), "dinheiro"))
        self.assertEqual(pedidos.BuscarPedido(4)["status"], "Aguardando pagamento")
        self.assertEqual(self.estoque, {"P001": 10, "P002": 3})

    def test_07_pedido_que_nao_esta_aguardando_pagamento(self):
        print("3.3 C7 - Pedido que nao esta aguardando pagamento")
        self.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(1), "pix"))
        self.assertEqual(self.estoque["P001"], 10)


# ==========================================================================
# 3.4 AtualizarStatus(num: int, status: str) -> bool (interna)
# ==========================================================================

class Teste_3_4_AtualizarStatus(BasePedidos):

    def test_01_alteracao_valida(self):
        print("3.4 C1 - Alteracao de status valida")
        self.assertTrue(pedidos.AtualizarStatus(2, "Pago"))
        self.assertEqual(pedidos.BuscarPedido(2)["status"], "Pago")

    def test_02_pedido_inexistente(self):
        print("3.4 C2 - Alteracao de pedido inexistente")
        self.assertFalse(pedidos.AtualizarStatus(999, "Pago"))

    def test_03_status_fora_dos_permitidos(self):
        print("3.4 C3 - Status fora dos tres permitidos")
        self.assertFalse(pedidos.AtualizarStatus(2, "Enviado"))
        self.assertEqual(pedidos.BuscarPedido(2)["status"], "Aguardando pagamento")


# ==========================================================================
# 3.5 CancelarPedido(num: int) -> bool
# ==========================================================================

class Teste_3_5_CancelarPedido(BasePedidos):

    def test_01_pedido_aguardando_pagamento(self):
        print("3.5 C1 - Cancelamento de pedido aguardando pagamento")
        self.assertTrue(pedidos.CancelarPedido(2))
        self.assertEqual(pedidos.BuscarPedido(2)["status"], "Cancelado")
        self.assertEqual(self.estoque["P002"], 3)

    def test_02_pedido_pago(self):
        print("3.5 C2 - Cancelamento de pedido pago")
        self.assertTrue(pedidos.CancelarPedido(1))
        self.assertEqual(pedidos.BuscarPedido(1)["status"], "Cancelado")
        self.assertEqual(self.estoque["P001"], 12)

    def test_03_pedido_inexistente(self):
        print("3.5 C3 - Cancelamento de pedido inexistente")
        self.assertFalse(pedidos.CancelarPedido(999))

    def test_04_pedido_ja_cancelado(self):
        print("3.5 C4 - Cancelamento de pedido ja cancelado")
        self.assertFalse(pedidos.CancelarPedido(3))
        self.assertEqual(self.estoque["P001"], 10)

    def test_05_pedido_pago_com_produto_removido(self):
        print("3.5 C5 (extra) - Cancelamento de pedido pago com produto ja removido do catalogo")
        removido = {"codigo": "P999", "nome": "Fora de linha", "preco": 5.00}
        pedidos._pedidos.append(_pedido(6, CPF_MARIA, "2026-10-20",
                                        [_item(ITEM_P001, 1), _item(removido, 1)],
                                        64.90, "Pago"))
        self.assertTrue(pedidos.CancelarPedido(6))
        self.assertEqual(pedidos.BuscarPedido(6)["status"], "Cancelado")
        self.assertEqual(self.estoque["P001"], 11)
        self.assertNotIn("P999", self.estoque)


# ==========================================================================
# 3.6 BuscarPedido(num: int) -> dict (interna)
# ==========================================================================

class Teste_3_6_BuscarPedido(BasePedidos):

    def test_01_pedido_existente(self):
        print("3.6 C1 - Busca de pedido existente")
        resultado = pedidos.BuscarPedido(1)
        self.assertEqual(resultado, CENARIO_INICIAL[0])
        self.assertEqual(resultado["status"], "Pago")

    def test_02_pedido_inexistente(self):
        print("3.6 C2 - Busca de pedido inexistente")
        self.assertEqual(pedidos.BuscarPedido(999), {})


# ==========================================================================
# 3.7 ListarPedidos(status: str) -> list
# ==========================================================================

class Teste_3_7_ListarPedidos(BasePedidos):

    @staticmethod
    def _numeros(lista):
        return [p["numero"] for p in lista]

    def test_01_pedidos_pagos(self):
        print("3.7 C1 - Listagem de pedidos pagos")
        self.assertEqual(self._numeros(pedidos.ListarPedidos("Pago")), [1])

    def test_02_pedidos_aguardando_pagamento(self):
        print("3.7 C2 - Listagem de pedidos aguardando pagamento")
        self.assertEqual(self._numeros(pedidos.ListarPedidos("Aguardando pagamento")), [2, 4, 5])

    def test_03_pedidos_cancelados(self):
        print("3.7 C3 - Listagem de pedidos cancelados")
        self.assertEqual(self._numeros(pedidos.ListarPedidos("Cancelado")), [3])

    def test_04_status_vazio_lista_todos(self):
        print("3.7 C4 - Listagem com status vazio (todos os pedidos)")
        self.assertEqual(self._numeros(pedidos.ListarPedidos("")), [1, 2, 3, 4, 5])

    def test_05_status_sem_pedidos(self):
        print("3.7 C5 - Listagem de status sem pedidos")
        self.assertEqual(pedidos.ListarPedidos("Enviado"), [])


# ==========================================================================
# 3.8 ListarPedidosCliente(cpf: str) -> list
# ==========================================================================

class Teste_3_8_ListarPedidosCliente(BasePedidos):

    @staticmethod
    def _numeros(lista):
        return [p["numero"] for p in lista]

    def test_01_cliente_com_mais_de_um_pedido(self):
        print("3.8 C1 - Cliente com mais de um pedido (ordem)")
        self.assertEqual(self._numeros(pedidos.ListarPedidosCliente(CPF_MARIA)), [2, 1])

    def test_02_cliente_com_status_variados(self):
        print("3.8 C2 - Cliente com pedidos de status variados")
        self.assertEqual(self._numeros(pedidos.ListarPedidosCliente(CPF_JOAO)), [5, 4, 3])

    def test_03_cliente_sem_pedidos(self):
        print("3.8 C3 - Cliente sem pedidos")
        self.assertEqual(pedidos.ListarPedidosCliente(CPF_ANA), [])


# ==========================================================================
# 3.9 SalvarPedidosNoArq() -> bool (interna)
# ==========================================================================

class Teste_3_9_SalvarPedidosNoArq(BasePedidos):

    def test_01_gravacao_bem_sucedida(self):
        print("3.9 C1 - Gravacao com sucesso")
        pedidos.CriarPedido(CPF_MARIA)
        self.assertTrue(pedidos.SalvarPedidosNoArq())
        self.assertEqual(len(ler_arquivo(self.arquivo)), 6)

    def test_02_falha_de_gravacao(self):
        print("3.9 C2 - Gravacao quando o arquivo nao pode ser escrito")
        os.remove(self.arquivo)
        os.mkdir(self.arquivo)          # pasta com o nome do arquivo: impede a escrita
        self.assertFalse(pedidos.SalvarPedidosNoArq())


if __name__ == "__main__":
    unittest.main(verbosity=2)
