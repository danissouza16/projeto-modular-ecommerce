"""
Módulo testador do RelatoriosVendas (Módulo 4)
Responsável: Matheus Marques

Implementa os casos de teste da seção 5.4 do documento do projeto (T2),
mais alguns casos extras de validação de tipo.

Organização
- Uma classe de teste por função de acesso (4.1 a 4.6); cada método é um caso Cn.
- Os módulos servidores (ProcessadorPedidos e CatalogoProdutos) são
  substituídos via unittest.mock.patch por versões falsas que imitam
  3.7, 1.2 e 1.4, com o cenário do documento. Assim os testes não dependem
  dos colegas nem gravam nos arquivos .json reais.
- A 4.6 grava numa pasta temporária, sem deixar arquivos no projeto.

Como executar (a partir da pasta raiz do projeto):
    python -m unittest testes.teste_relatorios_vendas -v
  ou
    python testes/teste_relatorios_vendas.py
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Permite rodar o arquivo diretamente (python testes/teste_relatorios_vendas.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos import relatorios_vendas as rv   # noqa: E402

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

class Teste_4_1_CalcularFaturamento(BaseRelatorios):

    def test_01_periodo_abrange_todos_os_pagos(self):
        print("4.1 C1 - Periodo que abrange todos os pedidos pagos")
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-10-31"), 209.80, places=2)

    def test_02_periodo_parcial(self):
        print("4.1 C2 - Periodo que abrange so parte dos pedidos pagos")
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-09-30"), 149.90, places=2)

    def test_03_ignora_nao_pagos(self):
        print("4.1 C3 - Periodo com pedidos nao pagos (ignorados)")
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-10-01", "2026-10-31"), 59.90, places=2)

    def test_04_limites_inclusivos(self):
        print("4.1 C4 - Limites do periodo inclusivos")
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-20", "2026-10-05"), 100.00, places=2)

    def test_05_um_unico_dia(self):
        print("4.1 C5 - Periodo de um unico dia")
        self.assertAlmostEqual(rv.CalcularFaturamento("2026-09-10", "2026-09-10"), 109.80, places=2)

    def test_06_periodo_sem_pedidos(self):
        print("4.1 C6 - Periodo sem pedidos pagos")
        self.assertEqual(rv.CalcularFaturamento("2026-08-01", "2026-08-31"), 0.0)

    def test_07_data_inicial_posterior(self):
        print("4.1 C7 - Data inicial posterior a final")
        self.assertEqual(rv.CalcularFaturamento("2026-10-31", "2026-09-01"), 0.0)

    def test_08_formato_invalido(self):
        print("4.1 C8 - Data em formato invalido")
        self.assertEqual(rv.CalcularFaturamento("10/09/2026", "2026-10-31"), 0.0)


# --------------------------------------------------------------------------
# 4.2 CalcularTicketMedio
# --------------------------------------------------------------------------

class Teste_4_2_CalcularTicketMedio(BaseRelatorios):

    def test_01_media_de_parte_dos_pedidos(self):
        print("4.2 C1 - Media de periodo com parte dos pedidos pagos")
        self.assertAlmostEqual(rv.CalcularTicketMedio("2026-09-01", "2026-09-30"), 74.95, places=2)

    def test_02_um_pago_com_nao_pagos_misturados(self):
        print("4.2 C2 - Um pedido pago com nao pagos misturados")
        self.assertAlmostEqual(rv.CalcularTicketMedio("2026-10-01", "2026-10-31"), 59.90, places=2)

    def test_03_sem_pedidos_nao_divide_por_zero(self):
        print("4.2 C3 - Periodo sem pedidos pagos (sem divisao por zero)")
        self.assertEqual(rv.CalcularTicketMedio("2026-08-01", "2026-08-31"), 0.0)

    def test_04_data_inicial_posterior(self):
        print("4.2 C4 - Data inicial posterior a final")
        self.assertEqual(rv.CalcularTicketMedio("2026-10-31", "2026-09-01"), 0.0)

    def test_05_data_invalida(self):
        print("4.2 C5 - Data invalida")
        self.assertEqual(rv.CalcularTicketMedio("2026-09-01", "2026-13-45"), 0.0)


# --------------------------------------------------------------------------
# 4.3 ListarMaisVendidos
# --------------------------------------------------------------------------

RANKING_COMPLETO = [
    {"codigo": "P001", "nome": "Camiseta Basica", "quantidade": 3},
    {"codigo": "P002", "nome": "P002", "quantidade": 1},
]


class Teste_4_3_ListarMaisVendidos(BaseRelatorios):

    def test_01_n_igual_ao_numero_de_vendidos(self):
        print("4.3 C1 - n igual ao numero de produtos vendidos")
        self.assertEqual(rv.ListarMaisVendidos(2), RANKING_COMPLETO)

    def test_02_n_menor(self):
        print("4.3 C2 - n menor que o numero de produtos vendidos")
        self.assertEqual(rv.ListarMaisVendidos(1), RANKING_COMPLETO[:1])

    def test_03_n_maior(self):
        print("4.3 C3 - n maior que o numero de produtos vendidos")
        self.assertEqual(rv.ListarMaisVendidos(10), RANKING_COMPLETO)

    def test_04_n_zero(self):
        print("4.3 C4 - n igual a zero")
        self.assertEqual(rv.ListarMaisVendidos(0), [])

    def test_05_n_negativo(self):
        print("4.3 C5 - n negativo")
        self.assertEqual(rv.ListarMaisVendidos(-1), [])

    def test_06_n_de_tipo_errado(self):
        print("4.3 C7 (extra) - n de tipo errado")
        self.assertEqual(rv.ListarMaisVendidos("2"), [])

    def test_07_produto_removido_do_catalogo_usa_nome_do_pedido(self):
        print("4.3 C8 (extra) - Produto removido do catalogo usa o nome do pedido")
        self.produtos_cenario = [p for p in PRODUTOS if p["codigo"] != "P001"]
        self.assertEqual(rv.ListarMaisVendidos(1)[0]["nome"], "Camiseta Basica")


class Teste_4_3_ListarMaisVendidosSoNaoPagos(BaseRelatorios):
    pedidos_cenario = PEDIDOS[3:]      # só os pedidos 4 e 5

    def test_01_so_existem_pedidos_nao_pagos(self):
        print("4.3 C6 - So existem pedidos nao pagos")
        self.assertEqual(rv.ListarMaisVendidos(2), [])


# --------------------------------------------------------------------------
# 4.4 VendasPorCliente
# --------------------------------------------------------------------------

class Teste_4_4_VendasPorCliente(BaseRelatorios):

    def test_01_cliente_com_mais_de_um_pago(self):
        print("4.4 C1 - Cliente com mais de um pedido pago")
        esperado = [{"numero": 1, "data": "2026-09-10", "total": 109.80},
                    {"numero": 2, "data": "2026-09-20", "total": 40.10}]
        self.assertEqual(rv.VendasPorCliente("12345678901"), esperado)

    def test_02_ignora_nao_pagos(self):
        print("4.4 C2 - Cliente com pedidos pagos e nao pagos")
        esperado = [{"numero": 3, "data": "2026-10-05", "total": 59.90}]
        self.assertEqual(rv.VendasPorCliente("98765432100"), esperado)

    def test_03_cliente_sem_pedidos(self):
        print("4.4 C3 - Cliente sem pedidos")
        self.assertEqual(rv.VendasPorCliente("11122233344"), [])

    def test_04_cpf_inexistente(self):
        print("4.4 C4 - CPF inexistente")
        self.assertEqual(rv.VendasPorCliente("00000000000"), [])

    def test_05_cpf_de_tipo_errado(self):
        print("4.4 C5 (extra) - CPF de tipo errado")
        self.assertEqual(rv.VendasPorCliente(12345678901), [])


# --------------------------------------------------------------------------
# 4.5 ListarEstoqueBaixo
# --------------------------------------------------------------------------

class Teste_4_5_ListarEstoqueBaixo(BaseRelatorios):

    def _codigos(self, lista):
        return [p["codigo"] for p in lista]

    def test_01_limite_alcanca_um_produto(self):
        print("4.5 C1 - Limite que alcanca apenas um produto")
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(5)), ["P002"])

    def test_02_limite_inclusivo(self):
        print("4.5 C2 - Limite igual ao estoque (inclusivo)")
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(3)), ["P002"])

    def test_03_limite_alcanca_todos(self):
        print("4.5 C3 - Limite que alcanca todos os produtos")
        self.assertEqual(self._codigos(rv.ListarEstoqueBaixo(10)), ["P001", "P002"])

    def test_04_limite_menor_que_todos(self):
        print("4.5 C4 - Limite menor que o estoque de todos")
        self.assertEqual(rv.ListarEstoqueBaixo(2), [])

    def test_05_limite_negativo(self):
        print("4.5 C5 - Limite negativo")
        self.assertEqual(rv.ListarEstoqueBaixo(-1), [])

    def test_06_limite_de_tipo_errado(self):
        print("4.5 C6 (extra) - Limite de tipo errado")
        self.assertEqual(rv.ListarEstoqueBaixo("5"), [])


# --------------------------------------------------------------------------
# 4.6 ExportarRelatorio  (usa pasta temporária: não deixa lixo no disco)
# --------------------------------------------------------------------------

class Teste_4_6_ExportarRelatorio(unittest.TestCase):

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        original = os.getcwd()
        os.chdir(pasta.name)
        self.addCleanup(os.chdir, original)

    def test_01_exportacao_valida(self):
        print("4.6 C1 - Exportacao com dados e nome validos")
        self.assertTrue(rv.ExportarRelatorio(RANKING_COMPLETO, "mais_vendidos.txt"))
        with open("mais_vendidos.txt", encoding="utf-8") as f:
            linhas = f.read().splitlines()
        self.assertEqual(len(linhas), 2)
        self.assertIn("P001", linhas[0])
        self.assertIn("P002", linhas[1])

    def test_02_lista_vazia(self):
        print("4.6 C2 - Exportacao com lista vazia")
        self.assertFalse(rv.ExportarRelatorio([], "vazio.txt"))
        self.assertFalse(os.path.exists("vazio.txt"))

    def test_03_nome_de_arquivo_invalido(self):
        print("4.6 C3 - Nome de arquivo invalido")
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], ""))
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "a/b.txt"))

    def test_04_erro_de_escrita(self):
        print("4.6 C4 - Erro de escrita no arquivo")
        os.mkdir("relatorio.txt")      # pasta com o mesmo nome impede a escrita
        self.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "relatorio.txt"))

    def test_05_dados_de_tipo_errado(self):
        print("4.6 C5 (extra) - Dados de tipo errado")
        self.assertFalse(rv.ExportarRelatorio("texto", "x.txt"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
