"""
Módulo testador do RelatoriosVendas (Módulo 4)
Responsável: Matheus Marques

Implementa os casos de teste da seção 5.4 do documento do projeto (T2),
mais alguns casos extras de validação de tipo.

Organização
- Sem classes: cada caso Cn é uma função; os casos de cada função
  (4.1 a 4.6) formam um grupo na lista GRUPOS, montada por
  testes/suite_funcoes.py com unittest.FunctionTestCase.
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
from testes.suite_funcoes import grupo, montar_suite, verifica   # noqa: E402

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

# --------------------------------------------------------------------------
# Preparação e limpeza (rodam antes e depois de CADA caso)
# --------------------------------------------------------------------------

_ctx = {}         # pedidos e produtos que os falsos devolvem no caso atual
_limpezas = []    # ações de limpeza, desfeitas na ordem inversa


def _ligar_falsos(pedidos_cenario, produtos_cenario):
    """Troca 3.7, 1.2 e 1.4 por versões falsas com o cenário dado. Um caso
    pode trocar _ctx["produtos_cenario"] no meio do teste (4.3 C8)."""
    _ctx["pedidos_cenario"] = pedidos_cenario
    _ctx["produtos_cenario"] = produtos_cenario

    def listar_pedidos(status):                      # imita 3.7
        return [dict(p) for p in _ctx["pedidos_cenario"]
                if status == "" or p["status"] == status]

    def buscar_produto(codigo):                      # imita 1.2
        for p in _ctx["produtos_cenario"]:
            if p["codigo"] == codigo:
                return dict(p)
        return {}

    def listar_produtos(categoria):                  # imita 1.4
        return [dict(p) for p in _ctx["produtos_cenario"]
                if categoria == "" or p["categoria"] == categoria]

    alvos = {
        "modulos.relatorios_vendas.pedidos.ListarPedidos": listar_pedidos,
        "modulos.relatorios_vendas.catalogo.BuscarProduto": buscar_produto,
        "modulos.relatorios_vendas.catalogo.ListarProdutos": listar_produtos,
    }
    for alvo, falso in alvos.items():
        patcher = patch(alvo, side_effect=falso)
        patcher.start()
        _limpezas.append(patcher.stop)


def preparar_cenario():
    """Cenário completo do documento (5 pedidos, 2 produtos)."""
    _ligar_falsos(PEDIDOS, PRODUTOS)


def preparar_cenario_so_nao_pagos():
    """Só os pedidos 4 e 5, nenhum pago (4.3 C6)."""
    _ligar_falsos(PEDIDOS[3:], PRODUTOS)


def preparar_pasta_exportacao():
    """4.6: grava numa pasta temporária, sem deixar arquivos no projeto."""
    pasta = tempfile.TemporaryDirectory()
    _limpezas.append(pasta.cleanup)
    original = os.getcwd()
    os.chdir(pasta.name)
    _limpezas.append(lambda: os.chdir(original))


def limpar():
    """Desfaz as trocas e volta à pasta original."""
    while _limpezas:
        _limpezas.pop()()


def _codigos(lista):
    return [p["codigo"] for p in lista]



# --------------------------------------------------------------------------
# 4.1 CalcularFaturamento
# --------------------------------------------------------------------------


def caso_4_1_01_periodo_abrange_todos_os_pagos():
    print("4.1 C1 - Periodo que abrange todos os pedidos pagos")
    verifica.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-10-31"), 209.80, places=2)


def caso_4_1_02_periodo_parcial():
    print("4.1 C2 - Periodo que abrange so parte dos pedidos pagos")
    verifica.assertAlmostEqual(rv.CalcularFaturamento("2026-09-01", "2026-09-30"), 149.90, places=2)


def caso_4_1_03_ignora_nao_pagos():
    print("4.1 C3 - Periodo com pedidos nao pagos (ignorados)")
    verifica.assertAlmostEqual(rv.CalcularFaturamento("2026-10-01", "2026-10-31"), 59.90, places=2)


def caso_4_1_04_limites_inclusivos():
    print("4.1 C4 - Limites do periodo inclusivos")
    verifica.assertAlmostEqual(rv.CalcularFaturamento("2026-09-20", "2026-10-05"), 100.00, places=2)


def caso_4_1_05_um_unico_dia():
    print("4.1 C5 - Periodo de um unico dia")
    verifica.assertAlmostEqual(rv.CalcularFaturamento("2026-09-10", "2026-09-10"), 109.80, places=2)


def caso_4_1_06_periodo_sem_pedidos():
    print("4.1 C6 - Periodo sem pedidos pagos")
    verifica.assertEqual(rv.CalcularFaturamento("2026-08-01", "2026-08-31"), 0.0)


def caso_4_1_07_data_inicial_posterior():
    print("4.1 C7 - Data inicial posterior a final")
    verifica.assertEqual(rv.CalcularFaturamento("2026-10-31", "2026-09-01"), 0.0)


def caso_4_1_08_formato_invalido():
    print("4.1 C8 - Data em formato invalido")
    verifica.assertEqual(rv.CalcularFaturamento("10/09/2026", "2026-10-31"), 0.0)


# --------------------------------------------------------------------------
# 4.2 CalcularTicketMedio
# --------------------------------------------------------------------------


def caso_4_2_01_media_de_parte_dos_pedidos():
    print("4.2 C1 - Media de periodo com parte dos pedidos pagos")
    verifica.assertAlmostEqual(rv.CalcularTicketMedio("2026-09-01", "2026-09-30"), 74.95, places=2)


def caso_4_2_02_um_pago_com_nao_pagos_misturados():
    print("4.2 C2 - Um pedido pago com nao pagos misturados")
    verifica.assertAlmostEqual(rv.CalcularTicketMedio("2026-10-01", "2026-10-31"), 59.90, places=2)


def caso_4_2_03_sem_pedidos_nao_divide_por_zero():
    print("4.2 C3 - Periodo sem pedidos pagos (sem divisao por zero)")
    verifica.assertEqual(rv.CalcularTicketMedio("2026-08-01", "2026-08-31"), 0.0)


def caso_4_2_04_data_inicial_posterior():
    print("4.2 C4 - Data inicial posterior a final")
    verifica.assertEqual(rv.CalcularTicketMedio("2026-10-31", "2026-09-01"), 0.0)


def caso_4_2_05_data_invalida():
    print("4.2 C5 - Data invalida")
    verifica.assertEqual(rv.CalcularTicketMedio("2026-09-01", "2026-13-45"), 0.0)

# --------------------------------------------------------------------------
# 4.3 ListarMaisVendidos
# --------------------------------------------------------------------------

RANKING_COMPLETO = [
    {"codigo": "P001", "nome": "Camiseta Basica", "quantidade": 3},
    {"codigo": "P002", "nome": "P002", "quantidade": 1},
]


def caso_4_3_01_n_igual_ao_numero_de_vendidos():
    print("4.3 C1 - n igual ao numero de produtos vendidos")
    verifica.assertEqual(rv.ListarMaisVendidos(2), RANKING_COMPLETO)


def caso_4_3_02_n_menor():
    print("4.3 C2 - n menor que o numero de produtos vendidos")
    verifica.assertEqual(rv.ListarMaisVendidos(1), RANKING_COMPLETO[:1])


def caso_4_3_03_n_maior():
    print("4.3 C3 - n maior que o numero de produtos vendidos")
    verifica.assertEqual(rv.ListarMaisVendidos(10), RANKING_COMPLETO)


def caso_4_3_04_n_zero():
    print("4.3 C4 - n igual a zero")
    verifica.assertEqual(rv.ListarMaisVendidos(0), [])


def caso_4_3_05_n_negativo():
    print("4.3 C5 - n negativo")
    verifica.assertEqual(rv.ListarMaisVendidos(-1), [])


def caso_4_3_06_n_de_tipo_errado():
    print("4.3 C7 (extra) - n de tipo errado")
    verifica.assertEqual(rv.ListarMaisVendidos("2"), [])


def caso_4_3_07_produto_removido_do_catalogo_usa_nome_do_pedido():
    print("4.3 C8 (extra) - Produto removido do catalogo usa o nome do pedido")
    _ctx["produtos_cenario"] = [p for p in PRODUTOS if p["codigo"] != "P001"]
    verifica.assertEqual(rv.ListarMaisVendidos(1)[0]["nome"], "Camiseta Basica")


def caso_4_3_01_so_existem_pedidos_nao_pagos():
    print("4.3 C6 - So existem pedidos nao pagos")
    verifica.assertEqual(rv.ListarMaisVendidos(2), [])


# --------------------------------------------------------------------------
# 4.4 VendasPorCliente
# --------------------------------------------------------------------------


def caso_4_4_01_cliente_com_mais_de_um_pago():
    print("4.4 C1 - Cliente com mais de um pedido pago")
    esperado = [{"numero": 1, "data": "2026-09-10", "total": 109.80},
                {"numero": 2, "data": "2026-09-20", "total": 40.10}]
    verifica.assertEqual(rv.VendasPorCliente("12345678901"), esperado)


def caso_4_4_02_ignora_nao_pagos():
    print("4.4 C2 - Cliente com pedidos pagos e nao pagos")
    esperado = [{"numero": 3, "data": "2026-10-05", "total": 59.90}]
    verifica.assertEqual(rv.VendasPorCliente("98765432100"), esperado)


def caso_4_4_03_cliente_sem_pedidos():
    print("4.4 C3 - Cliente sem pedidos")
    verifica.assertEqual(rv.VendasPorCliente("11122233344"), [])


def caso_4_4_04_cpf_inexistente():
    print("4.4 C4 - CPF inexistente")
    verifica.assertEqual(rv.VendasPorCliente("00000000000"), [])


def caso_4_4_05_cpf_de_tipo_errado():
    print("4.4 C5 (extra) - CPF de tipo errado")
    verifica.assertEqual(rv.VendasPorCliente(12345678901), [])


# --------------------------------------------------------------------------
# 4.5 ListarEstoqueBaixo
# --------------------------------------------------------------------------


def caso_4_5_01_limite_alcanca_um_produto():
    print("4.5 C1 - Limite que alcanca apenas um produto")
    verifica.assertEqual(_codigos(rv.ListarEstoqueBaixo(5)), ["P002"])


def caso_4_5_02_limite_inclusivo():
    print("4.5 C2 - Limite igual ao estoque (inclusivo)")
    verifica.assertEqual(_codigos(rv.ListarEstoqueBaixo(3)), ["P002"])


def caso_4_5_03_limite_alcanca_todos():
    print("4.5 C3 - Limite que alcanca todos os produtos")
    verifica.assertEqual(_codigos(rv.ListarEstoqueBaixo(10)), ["P001", "P002"])


def caso_4_5_04_limite_menor_que_todos():
    print("4.5 C4 - Limite menor que o estoque de todos")
    verifica.assertEqual(rv.ListarEstoqueBaixo(2), [])


def caso_4_5_05_limite_negativo():
    print("4.5 C5 - Limite negativo")
    verifica.assertEqual(rv.ListarEstoqueBaixo(-1), [])


def caso_4_5_06_limite_de_tipo_errado():
    print("4.5 C6 (extra) - Limite de tipo errado")
    verifica.assertEqual(rv.ListarEstoqueBaixo("5"), [])


# --------------------------------------------------------------------------
# 4.6 ExportarRelatorio  (usa pasta temporária: não deixa lixo no disco)
# --------------------------------------------------------------------------


def caso_4_6_01_exportacao_valida():
    print("4.6 C1 - Exportacao com dados e nome validos")
    verifica.assertTrue(rv.ExportarRelatorio(RANKING_COMPLETO, "mais_vendidos.txt"))
    with open("mais_vendidos.txt", encoding="utf-8") as f:
        linhas = f.read().splitlines()
    verifica.assertEqual(len(linhas), 2)
    verifica.assertIn("P001", linhas[0])
    verifica.assertIn("P002", linhas[1])


def caso_4_6_02_lista_vazia():
    print("4.6 C2 - Exportacao com lista vazia")
    verifica.assertFalse(rv.ExportarRelatorio([], "vazio.txt"))
    verifica.assertFalse(os.path.exists("vazio.txt"))


def caso_4_6_03_nome_de_arquivo_invalido():
    print("4.6 C3 - Nome de arquivo invalido")
    verifica.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], ""))
    verifica.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "a/b.txt"))


def caso_4_6_04_erro_de_escrita():
    print("4.6 C4 - Erro de escrita no arquivo")
    os.mkdir("relatorio.txt")      # pasta com o mesmo nome impede a escrita
    verifica.assertFalse(rv.ExportarRelatorio(RANKING_COMPLETO[:1], "relatorio.txt"))


def caso_4_6_05_dados_de_tipo_errado():
    print("4.6 C5 (extra) - Dados de tipo errado")
    verifica.assertFalse(rv.ExportarRelatorio("texto", "x.txt"))

# ==========================================================================
# Ordem de execução: um grupo por função, casos na ordem C1, C2, ...
# ==========================================================================

GRUPOS = [
    # 4.1 CalcularFaturamento
    grupo([
        caso_4_1_01_periodo_abrange_todos_os_pagos,
        caso_4_1_02_periodo_parcial,
        caso_4_1_03_ignora_nao_pagos,
        caso_4_1_04_limites_inclusivos,
        caso_4_1_05_um_unico_dia,
        caso_4_1_06_periodo_sem_pedidos,
        caso_4_1_07_data_inicial_posterior,
        caso_4_1_08_formato_invalido,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar),
    # 4.2 CalcularTicketMedio
    grupo([
        caso_4_2_01_media_de_parte_dos_pedidos,
        caso_4_2_02_um_pago_com_nao_pagos_misturados,
        caso_4_2_03_sem_pedidos_nao_divide_por_zero,
        caso_4_2_04_data_inicial_posterior,
        caso_4_2_05_data_invalida,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar),
    # Teste_4_3_ListarMaisVendidos
    grupo([
        caso_4_3_01_n_igual_ao_numero_de_vendidos,
        caso_4_3_02_n_menor,
        caso_4_3_03_n_maior,
        caso_4_3_04_n_zero,
        caso_4_3_05_n_negativo,
        caso_4_3_06_n_de_tipo_errado,
        caso_4_3_07_produto_removido_do_catalogo_usa_nome_do_pedido,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar),
    # Teste_4_3_ListarMaisVendidosSoNaoPagos
    grupo([
        caso_4_3_01_so_existem_pedidos_nao_pagos,
    ], antes_de_cada=preparar_cenario_so_nao_pagos, depois_de_cada=limpar),
    # 4.4 VendasPorCliente
    grupo([
        caso_4_4_01_cliente_com_mais_de_um_pago,
        caso_4_4_02_ignora_nao_pagos,
        caso_4_4_03_cliente_sem_pedidos,
        caso_4_4_04_cpf_inexistente,
        caso_4_4_05_cpf_de_tipo_errado,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar),
    # 4.5 ListarEstoqueBaixo
    grupo([
        caso_4_5_01_limite_alcanca_um_produto,
        caso_4_5_02_limite_inclusivo,
        caso_4_5_03_limite_alcanca_todos,
        caso_4_5_04_limite_menor_que_todos,
        caso_4_5_05_limite_negativo,
        caso_4_5_06_limite_de_tipo_errado,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar),
    # 4.6 ExportarRelatorio  (usa pasta temporária: não deixa lixo no disco)
    grupo([
        caso_4_6_01_exportacao_valida,
        caso_4_6_02_lista_vazia,
        caso_4_6_03_nome_de_arquivo_invalido,
        caso_4_6_04_erro_de_escrita,
        caso_4_6_05_dados_de_tipo_errado,
    ], antes_de_cada=preparar_pasta_exportacao, depois_de_cada=limpar),
]


def load_tests(loader, testes_padrao, padrao):
    """Chamada pelo unittest (discover ou execução direta) para montar a suíte."""
    return montar_suite(GRUPOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
