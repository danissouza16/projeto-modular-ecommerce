"""
Testes automatizados do Módulo 4 · RelatoriosVendas (TDD / unittest).

Os módulos servidores (ProcessadorPedidos e CatalogoProdutos) são substituídos
por versões falsas que imitam 3.7, 1.2 e 1.4, com o cenário do documento do grupo.
Assim os testes não dependem dos colegas nem gravam nos arquivos .json reais.

Execução (na raiz do projeto):  python testes_relatorios_vendas.py
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from modulos import relatorios_vendas as rv

# --------------------------------------------------------------------------
# Cenário do documento (seção 5.4)
# --------------------------------------------------------------------------

def _item(codigo, nome, preco, qtd):
    return {"codigo": codigo, "nome": nome, "preco": preco, "quantidade": qtd}

PEDIDOS = [
    {"numero": 1, "cpf": "12345678901", "data": "2026-09-10", "total": 109.80,
     "status": "Pago", "itens": [_item("P001", "Camiseta Basica", 49.90, 2)]},
    {"numero": 2, "cpf": "12345678901", "data": "2026-09-20", "total": 40.10,
     "status": "Pago", "itens": [_item("P002", "P002", 30.10, 1)]},
    {"numero": 3, "cpf": "98765432100", "data": "2026-10-05", "total": 59.90,
     "status": "Pago", "itens": [_item("P001", "Camiseta Basica", 49.90, 1)]},
    {"numero": 4, "cpf": "98765432100", "data": "2026-10-08", "total": 259.50,
     "status": "Aguardando pagamento", "itens": [_item("P002", "P002", 30.10, 5)]},
    {"numero": 5, "cpf": "98765432100", "data": "2026-10-10", "total": 70.20,
     "status": "Cancelado", "itens": [_item("P001", "Camiseta Basica", 49.90, 4)]},
]

# Obs.: o nome de P002 ("P002") segue o valorado do documento; o catálogo real
# do Daniel precisa usar o mesmo nome para a integração bater.
PRODUTOS = [
    {"codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
     "categoria": "Roupas", "preco": 49.90, "estoque": 10},
    {"codigo": "P002", "nome": "P002", "descricao": "Item 2",
     "categoria": "Acessorios", "preco": 30.10, "estoque": 3},
]


class BaseRelatorios(unittest.TestCase):
    """Troca os módulos servidores por falsos que imitam 3.7, 1.2 e 1.4."""

    pedidos_cenario = PEDIDOS
    produtos_cenario = PRODUTOS

    def setUp(self):
        def listar_pedidos(status):                      # imita 3.7
            return [dict(p) for p in self.pedidos_cenario
                    if status == "" or p["status"] == status]

        def buscar_produto(codigo):                      # imita 1.2
            for p in self.produtos_cenario:
                if p["codigo"] == codigo:
                    return dict(p)
            return {}

        def listar_produtos(categoria):                  # imita 1.4
            return [dict(p) for p in self.produtos_cenario
                    if categoria == "" or p["categoria"] == categoria]

        alvos = {
            "modulos.relatorios_vendas.pedidos.ListarPedidos": listar_pedidos,
            "modulos.relatorios_vendas.catalogo.BuscarProduto": buscar_produto,
            "modulos.relatorios_vendas.catalogo.ListarProdutos": listar_produtos,
        }
        for alvo, falso in alvos.items():
            patcher = patch(alvo, side_effect=falso)
            patcher.start()
            self.addCleanup(patcher.stop)


# --------------------------------------------------------------------------
# 4.1 CalcularFaturamento
# --------------------------------------------------------------------------

class TestCalcularFaturamento(BaseRelatorios):

    def test_4_1_c1_periodo_abrange_todos_os_pagos(self):
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-10-31"), 209.80, places=2)

    def test_4_1_c2_periodo_parcial(self):
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-09-30"), 149.90, places=2)

    def test_4_1_c3_ignora_nao_pagos(self):
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-10-01", "2026-10-31"), 59.90, places=2)

    def test_4_1_c4_limites_inclusivos(self):
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-20", "2026-10-05"), 100.00, places=2)

    def test_4_1_c5_um_unico_dia(self):
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-10", "2026-09-10"), 109.80, places=2)

    def test_4_1_c6_periodo_sem_pedidos(self):
        self.assertEqual(rv.CalcularFaturamento("2026-08-01", "2026-08-31"), 0.0)

    def test_4_1_c7_data_inicial_posterior(self):
        self.assertEqual(rv.CalcularFaturamento("2026-10-31", "2026-09-01"), 0.0)

    def test_4_1_c8_formato_invalido(self):
        self.assertEqual(rv.CalcularFaturamento("10/09/2026", "2026-10-31"), 0.0)



# --------------------------------------------------------------------------
# 4.2 CalcularTicketMedio
# --------------------------------------------------------------------------

class TestCalcularTicketMedio(BaseRelatorios):

    def test_4_2_c1_media_de_parte_dos_pedidos(self):
        self.assertAlmostEqual(rv.CalcularTicketMedio("2026-09-01", "2026-09-30"), 74.95, places=2)

    def test_4_2_c2_um_pago_com_nao_pagos_misturados(self):
        self.assertAlmostEqual(rv.CalcularTicketMedio("2026-10-01", "2026-10-31"), 59.90, places=2)

    def test_4_2_c3_sem_pedidos_nao_divide_por_zero(self):
        self.assertEqual(rv.CalcularTicketMedio("2026-08-01", "2026-08-31"), 0.0)

    def test_4_2_c4_data_inicial_posterior(self):
        self.assertEqual(rv.CalcularTicketMedio("2026-10-31", "2026-09-01"), 0.0)

    def test_4_2_c5_data_invalida(self):
        self.assertEqual(rv.CalcularTicketMedio("2026-09-01", "2026-13-45"), 0.0)


# --------------------------------------------------------------------------
# 4.3 ListarMaisVendidos
# --------------------------------------------------------------------------

RANKING_COMPLETO = [
    {"codigo": "P001", "nome": "Camiseta Basica", "quantidade": 3},
    {"codigo": "P002", "nome": "P002", "quantidade": 1},
]


class TestListarMaisVendidos(BaseRelatorios):

    def test_4_3_c1_n_igual_ao_numero_de_vendidos(self):
        self.assertEqual(rv.ListarMaisVendidos(2), RANKING_COMPLETO)

    def test_4_3_c2_n_menor(self):
        self.assertEqual(rv.ListarMaisVendidos(1), RANKING_COMPLETO[:1])

    def test_4_3_c3_n_maior(self):
        self.assertEqual(rv.ListarMaisVendidos(10), RANKING_COMPLETO)

    def test_4_3_c4_n_zero(self):
        self.assertEqual(rv.ListarMaisVendidos(0), [])

    def test_4_3_c5_n_negativo(self):
        self.assertEqual(rv.ListarMaisVendidos(-1), [])

    def test_4_3_extra_n_de_tipo_errado(self):
        self.assertEqual(rv.ListarMaisVendidos("2"), [])

    def test_4_3_extra_produto_removido_do_catalogo_usa_nome_do_pedido(self):
        self.produtos_cenario = [p for p in PRODUTOS if p["codigo"] != "P001"]
        self.assertEqual(rv.ListarMaisVendidos(1)[0]["nome"], "Camiseta Basica")


class TestListarMaisVendidosSoNaoPagos(BaseRelatorios):
    pedidos_cenario = PEDIDOS[3:]      # só os pedidos 4 e 5

    def test_4_3_c6_so_existem_pedidos_nao_pagos(self):
        self.assertEqual(rv.ListarMaisVendidos(2), [])


# --------------------------------------------------------------------------
# 4.4 VendasPorCliente
# --------------------------------------------------------------------------

class TestVendasPorCliente(BaseRelatorios):

    def test_4_4_c1_cliente_com_mais_de_um_pago(self):
        esperado = [{"numero": 1, "data": "2026-09-10", "total": 109.80},
                    {"numero": 2, "data": "2026-09-20", "total": 40.10}]
        self.assertEqual(rv.VendasPorCliente("12345678901"), esperado)

    def test_4_4_c2_ignora_nao_pagos(self):
        esperado = [{"numero": 3, "data": "2026-10-05", "total": 59.90}]
        self.assertEqual(rv.VendasPorCliente("98765432100"), esperado)

    def test_4_4_c3_cliente_sem_pedidos(self):
        self.assertEqual(rv.VendasPorCliente("11122233344"), [])

    def test_4_4_c4_cpf_inexistente(self):
        self.assertEqual(rv.VendasPorCliente("00000000000"), [])

    def test_4_4_extra_cpf_de_tipo_errado(self):
        self.assertEqual(rv.VendasPorCliente(12345678901), [])


# --------------------------------------------------------------------------
# 4.5 ListarEstoqueBaixo
# --------------------------------------------------------------------------

class TestListarEstoqueBaixo(BaseRelatorios):

    def _codigos(self, lista):
        return [p["codigo"] for p in lista]

    def test_4_5_c1_limite_alcanca_um_produto(self):
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(5)), ["P002"])

    def test_4_5_c2_limite_inclusivo(self):
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(3)), ["P002"])

    def test_4_5_c3_limite_alcanca_todos(self):
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(10)), ["P001", "P002"])

    def test_4_5_c4_limite_menor_que_todos(self):
        self.assertEqual(rv.ListarEstoqueBaixo(2), [])

    def test_4_5_c5_limite_negativo(self):
        self.assertEqual(rv.ListarEstoqueBaixo(-1), [])

    def test_4_5_extra_limite_de_tipo_errado(self):
        self.assertEqual(rv.ListarEstoqueBaixo("5"), [])


# --------------------------------------------------------------------------
# 4.6 ExportarRelatorio  (usa pasta temporária: não deixa lixo no disco)
# --------------------------------------------------------------------------

class TestExportarRelatorio(unittest.TestCase):

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        original = os.getcwd()
        os.chdir(pasta.name)
        self.addCleanup(os.chdir, original)

    def test_4_6_c1_exportacao_valida(self):
        self.assertTrue(rv.ExportarRelatorio(RANKING_COMPLETO, "mais_vendidos.txt"))
        with open("mais_vendidos.txt", encoding="utf-8") as f:
            linhas = f.read().splitlines()
        self.assertEqual(len(linhas), 2)
        self.assertIn("P001", linhas[0])
        self.assertIn("P002", linhas[1])

    def test_4_6_c2_lista_vazia(self):
        self.assertFalse(rv.ExportarRelatorio([], "vazio.txt"))
        self.assertFalse(os.path.exists("vazio.txt"))

    def test_4_6_c3_nome_de_arquivo_invalido(self):
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], ""))
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "a/b.txt"))

    def test_4_6_c4_erro_de_escrita(self):
        os.mkdir("relatorio.txt")      # pasta com o mesmo nome impede a escrita
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "relatorio.txt"))

    def test_4_6_extra_dados_de_tipo_errado(self):
        self.assertFalse(rv.ExportarRelatorio("texto", "x.txt"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
