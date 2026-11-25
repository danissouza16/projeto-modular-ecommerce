"""
Módulo testador do ProcessadorPedidos (Módulo 3)
Responsáveis: Brenno Távora e Guilherme Meira

Implementa os casos de teste da seção 5.3 do documento do projeto (T2),
incluindo as funções internas 3.2, 3.4, 3.6 e 3.9.

Organização
- Sem classes: cada caso Cn é uma função; os casos de cada função
  (3.1 a 3.9) formam um grupo na lista GRUPOS, montada por
  testes/suite_funcoes.py com unittest.FunctionTestCase.
- ANTES DE CADA TESTE o cenário inicial é recriado em uma pasta temporária,
  então os casos não dependem da ordem e nunca mexem em dados/pedidos.json.
- O CatalogoProdutos (1.7, 1.8, 1.9) e o GerenciadorClientes (2.8, 2.10)
  são simulados via unittest.mock.patch, com um estoque e carrinhos
  em memória (ver preparar_cenario).

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
from testes.suite_funcoes import grupo, montar_suite, verifica   # noqa: E402

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

# --------------------------------------------------------------------------
# Preparação e limpeza do cenário (rodam antes e depois de CADA caso)
# --------------------------------------------------------------------------

_ctx = {}         # pasta, arquivo, estoque e carrinhos simulados do caso atual
_limpezas = []    # ações de limpeza, desfeitas na ordem inversa


# Versões simuladas do CatalogoProdutos (1.7, 1.8, 1.9) e do
# GerenciadorClientes (2.8, 2.10), com estoque e carrinhos em memória.

def _consultar_estoque(codigo):
    return _ctx["estoque"].get(codigo, -1)


def _baixar_estoque(codigo, qtd):
    estoque = _ctx["estoque"]
    if codigo not in estoque or qtd <= 0 or qtd > estoque[codigo]:
        return False
    estoque[codigo] -= qtd
    return True


def _repor_estoque(codigo, qtd):
    estoque = _ctx["estoque"]
    if codigo not in estoque or qtd <= 0:
        return False
    estoque[codigo] += qtd
    return True


def _obter_carrinho(cpf):
    return copy.deepcopy(_ctx["carrinhos"].get(cpf, []))


def _esvaziar_carrinho(cpf):
    if cpf not in _ctx["carrinhos"]:
        return False
    _ctx["carrinhos"][cpf] = []
    return True


def preparar_cenario():
    """Recria pedidos, estoque e carrinhos e liga as simulações."""
    caminho_original = pedidos._CAMINHO_ARQUIVO
    _ctx["pasta"] = tempfile.mkdtemp()
    _ctx["arquivo"] = montar_cenario_inicial(_ctx["pasta"])

    def restaurar():
        pedidos._CAMINHO_ARQUIVO = caminho_original
        shutil.rmtree(_ctx["pasta"], ignore_errors=True)
    _limpezas.append(restaurar)

    _ctx["estoque"] = {"P001": 10, "P002": 3}
    _ctx["carrinhos"] = {
        CPF_MARIA: [_item(ITEM_P001, 2)],
        CPF_JOAO: [],
        CPF_ANA: [_item(ITEM_P002, 3)],
    }
    for alvo, simulacao in (
        ("modulos.catalogo_produtos.ConsultarEstoque", _consultar_estoque),
        ("modulos.catalogo_produtos.BaixarEstoque", _baixar_estoque),
        ("modulos.catalogo_produtos.ReporEstoque", _repor_estoque),
        ("modulos.gerenciador_clientes.ObterCarrinho", _obter_carrinho),
        ("modulos.gerenciador_clientes.EsvaziarCarrinho", _esvaziar_carrinho),
    ):
        patcher = patch(alvo, side_effect=simulacao)
        patcher.start()
        _limpezas.append(patcher.stop)


def limpar_cenario():
    """Desliga as simulações e apaga a pasta temporária."""
    while _limpezas:
        _limpezas.pop()()


def _numeros(lista):
    return [p["numero"] for p in lista]


ITENS_3_2 = [{"codigo": "P001", "preco": 49.90, "quantidade": 2}]



# ==========================================================================
# 3.1 CriarPedido(cpf: str) -> dict
# ==========================================================================


def caso_3_1_01_carrinho_valido_e_estoque_suficiente():
    print("3.1 C1 - Criacao de pedido com carrinho valido e estoque suficiente")
    resultado = pedidos.CriarPedido(CPF_MARIA)
    verifica.assertEqual(resultado["numero"], 6)
    verifica.assertEqual(resultado["cpf"], CPF_MARIA)
    verifica.assertEqual(resultado["data"], datetime.date.today().isoformat())
    verifica.assertEqual(resultado["itens"], [_item(ITEM_P001, 2)])
    verifica.assertAlmostEqual(resultado["subtotal"], 99.80)
    verifica.assertAlmostEqual(resultado["frete"], 10.00)
    verifica.assertAlmostEqual(resultado["desconto"], 0.0)
    verifica.assertAlmostEqual(resultado["total"], 109.80)
    verifica.assertEqual(resultado["status"], "Aguardando pagamento")
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 6)


def caso_3_1_02_carrinho_vazio():
    print("3.1 C2 - Criacao com carrinho vazio")
    verifica.assertEqual(pedidos.CriarPedido(CPF_JOAO), {})
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 5)


def caso_3_1_03_estoque_insuficiente():
    print("3.1 C3 - Criacao com estoque insuficiente em algum item")
    verifica.assertTrue(_baixar_estoque("P002", 1))    # estoque 3 -> 2
    verifica.assertEqual(_ctx["estoque"]["P002"], 2)
    verifica.assertEqual(pedidos.CriarPedido(CPF_ANA), {})
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 5)


def caso_3_1_04_cliente_inexistente():
    print("3.1 C4 - Criacao para cliente inexistente")
    verifica.assertEqual(pedidos.CriarPedido("00000000000"), {})


# ==========================================================================
# 3.2 CalcularTotal(itens: list, frete: float, desconto: float) -> float (interna)
# ==========================================================================


def caso_3_2_01_itens_e_frete_sem_desconto():
    print("3.2 C1 - Calculo com itens, frete e sem desconto")
    verifica.assertAlmostEqual(pedidos.CalcularTotal(ITENS_3_2, 10.0, 0.0), 109.80)


def caso_3_2_02_itens_frete_e_desconto():
    print("3.2 C2 - Calculo com itens, frete e desconto")
    verifica.assertAlmostEqual(pedidos.CalcularTotal(ITENS_3_2, 10.0, 5.0), 104.80)


def caso_3_2_03_lista_vazia():
    print("3.2 C3 - Lista de itens vazia")
    verifica.assertEqual(pedidos.CalcularTotal([], 10.0, 0.0), 0.0)


def caso_3_2_04_frete_negativo():
    print("3.2 C4 - Frete negativo")
    verifica.assertEqual(pedidos.CalcularTotal(ITENS_3_2, -10.0, 0.0), 0.0)


def caso_3_2_05_desconto_negativo():
    print("3.2 C5 - Desconto negativo")
    verifica.assertEqual(pedidos.CalcularTotal(ITENS_3_2, 10.0, -5.0), 0.0)


# ==========================================================================
# 3.3 SimularPagamento(pedido: dict, forma: str) -> bool
# ==========================================================================


def caso_3_3_01_pix_aprovado():
    print("3.3 C1 - Pagamento aprovado via Pix")
    _ctx["carrinhos"][CPF_MARIA] = [_item(ITEM_P001, 2)]
    verifica.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(2), "pix"))
    verifica.assertEqual(pedidos.BuscarPedido(2)["status"], "Pago")
    verifica.assertEqual(_ctx["estoque"]["P002"], 2)
    verifica.assertEqual(_ctx["carrinhos"][CPF_MARIA], [])


def caso_3_3_02_cartao_aprovado():
    print("3.3 C2 - Pagamento aprovado via cartao")
    verifica.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(4), "cartao"))
    verifica.assertEqual(pedidos.BuscarPedido(4)["status"], "Pago")
    verifica.assertEqual(_ctx["estoque"]["P001"], 9)


def caso_3_3_03_boleto_aprovado():
    print("3.3 C3 - Pagamento aprovado via boleto")
    verifica.assertTrue(pedidos.SimularPagamento(pedidos.BuscarPedido(5), "boleto"))
    verifica.assertEqual(pedidos.BuscarPedido(5)["status"], "Pago")
    verifica.assertEqual(_ctx["estoque"]["P001"], 0)


def caso_3_3_04_cartao_recusado_acima_do_limite():
    print("3.3 C4 - Pagamento recusado via cartao (total acima do limite)")
    verifica.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(5), "cartao"))
    verifica.assertEqual(pedidos.BuscarPedido(5)["status"], "Cancelado")
    verifica.assertEqual(_ctx["estoque"]["P001"], 10)


def caso_3_3_05_boleto_recusado_abaixo_do_minimo():
    print("3.3 C5 - Pagamento recusado via boleto (total abaixo do minimo)")
    verifica.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(2), "boleto"))
    verifica.assertEqual(pedidos.BuscarPedido(2)["status"], "Cancelado")
    verifica.assertEqual(_ctx["estoque"]["P002"], 3)


def caso_3_3_06_forma_de_pagamento_invalida():
    print("3.3 C6 - Forma de pagamento invalida")
    verifica.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(4), "dinheiro"))
    verifica.assertEqual(pedidos.BuscarPedido(4)["status"], "Aguardando pagamento")
    verifica.assertEqual(_ctx["estoque"], {"P001": 10, "P002": 3})


def caso_3_3_07_pedido_que_nao_esta_aguardando_pagamento():
    print("3.3 C7 - Pedido que nao esta aguardando pagamento")
    verifica.assertFalse(pedidos.SimularPagamento(pedidos.BuscarPedido(1), "pix"))
    verifica.assertEqual(_ctx["estoque"]["P001"], 10)


# ==========================================================================
# 3.4 AtualizarStatus(num: int, status: str) -> bool (interna)
# ==========================================================================


def caso_3_4_01_alteracao_valida():
    print("3.4 C1 - Alteracao de status valida")
    verifica.assertTrue(pedidos.AtualizarStatus(2, "Pago"))
    verifica.assertEqual(pedidos.BuscarPedido(2)["status"], "Pago")


def caso_3_4_02_pedido_inexistente():
    print("3.4 C2 - Alteracao de pedido inexistente")
    verifica.assertFalse(pedidos.AtualizarStatus(999, "Pago"))


def caso_3_4_03_status_fora_dos_permitidos():
    print("3.4 C3 - Status fora dos tres permitidos")
    verifica.assertFalse(pedidos.AtualizarStatus(2, "Enviado"))
    verifica.assertEqual(pedidos.BuscarPedido(2)["status"], "Aguardando pagamento")


# ==========================================================================
# 3.5 CancelarPedido(num: int) -> bool
# ==========================================================================


def caso_3_5_01_pedido_aguardando_pagamento():
    print("3.5 C1 - Cancelamento de pedido aguardando pagamento")
    verifica.assertTrue(pedidos.CancelarPedido(2))
    verifica.assertEqual(pedidos.BuscarPedido(2)["status"], "Cancelado")
    verifica.assertEqual(_ctx["estoque"]["P002"], 3)


def caso_3_5_02_pedido_pago():
    print("3.5 C2 - Cancelamento de pedido pago")
    verifica.assertTrue(pedidos.CancelarPedido(1))
    verifica.assertEqual(pedidos.BuscarPedido(1)["status"], "Cancelado")
    verifica.assertEqual(_ctx["estoque"]["P001"], 12)


def caso_3_5_03_pedido_inexistente():
    print("3.5 C3 - Cancelamento de pedido inexistente")
    verifica.assertFalse(pedidos.CancelarPedido(999))


def caso_3_5_04_pedido_ja_cancelado():
    print("3.5 C4 - Cancelamento de pedido ja cancelado")
    verifica.assertFalse(pedidos.CancelarPedido(3))
    verifica.assertEqual(_ctx["estoque"]["P001"], 10)


def caso_3_5_05_pedido_pago_com_produto_removido():
    print("3.5 C5 (extra) - Cancelamento de pedido pago com produto ja removido do catalogo")
    removido = {"codigo": "P999", "nome": "Fora de linha", "preco": 5.00}
    pedidos._pedidos.append(_pedido(6, CPF_MARIA, "2026-10-20",
                                    [_item(ITEM_P001, 1), _item(removido, 1)],
                                    64.90, "Pago"))
    verifica.assertTrue(pedidos.CancelarPedido(6))
    verifica.assertEqual(pedidos.BuscarPedido(6)["status"], "Cancelado")
    verifica.assertEqual(_ctx["estoque"]["P001"], 11)
    verifica.assertNotIn("P999", _ctx["estoque"])


# ==========================================================================
# 3.6 BuscarPedido(num: int) -> dict (interna)
# ==========================================================================


def caso_3_6_01_pedido_existente():
    print("3.6 C1 - Busca de pedido existente")
    resultado = pedidos.BuscarPedido(1)
    verifica.assertEqual(resultado, CENARIO_INICIAL[0])
    verifica.assertEqual(resultado["status"], "Pago")


def caso_3_6_02_pedido_inexistente():
    print("3.6 C2 - Busca de pedido inexistente")
    verifica.assertEqual(pedidos.BuscarPedido(999), {})


# ==========================================================================
# 3.7 ListarPedidos(status: str) -> list
# ==========================================================================


def caso_3_7_01_pedidos_pagos():
    print("3.7 C1 - Listagem de pedidos pagos")
    verifica.assertEqual(_numeros(pedidos.ListarPedidos("Pago")), [1])


def caso_3_7_02_pedidos_aguardando_pagamento():
    print("3.7 C2 - Listagem de pedidos aguardando pagamento")
    verifica.assertEqual(_numeros(pedidos.ListarPedidos("Aguardando pagamento")), [2, 4, 5])


def caso_3_7_03_pedidos_cancelados():
    print("3.7 C3 - Listagem de pedidos cancelados")
    verifica.assertEqual(_numeros(pedidos.ListarPedidos("Cancelado")), [3])


def caso_3_7_04_status_vazio_lista_todos():
    print("3.7 C4 - Listagem com status vazio (todos os pedidos)")
    verifica.assertEqual(_numeros(pedidos.ListarPedidos("")), [1, 2, 3, 4, 5])


def caso_3_7_05_status_sem_pedidos():
    print("3.7 C5 - Listagem de status sem pedidos")
    verifica.assertEqual(pedidos.ListarPedidos("Enviado"), [])


# ==========================================================================
# 3.8 ListarPedidosCliente(cpf: str) -> list
# ==========================================================================


def caso_3_8_01_cliente_com_mais_de_um_pedido():
    print("3.8 C1 - Cliente com mais de um pedido (ordem)")
    verifica.assertEqual(_numeros(pedidos.ListarPedidosCliente(CPF_MARIA)), [2, 1])


def caso_3_8_02_cliente_com_status_variados():
    print("3.8 C2 - Cliente com pedidos de status variados")
    verifica.assertEqual(_numeros(pedidos.ListarPedidosCliente(CPF_JOAO)), [5, 4, 3])


def caso_3_8_03_cliente_sem_pedidos():
    print("3.8 C3 - Cliente sem pedidos")
    verifica.assertEqual(pedidos.ListarPedidosCliente(CPF_ANA), [])


# ==========================================================================
# 3.9 SalvarPedidosNoArq() -> bool (interna)
# ==========================================================================


def caso_3_9_01_gravacao_bem_sucedida():
    print("3.9 C1 - Gravacao com sucesso")
    pedidos.CriarPedido(CPF_MARIA)
    verifica.assertTrue(pedidos.SalvarPedidosNoArq())
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 6)


def caso_3_9_02_falha_de_gravacao():
    print("3.9 C2 - Gravacao quando o arquivo nao pode ser escrito")
    os.remove(_ctx["arquivo"])
    os.mkdir(_ctx["arquivo"])          # pasta com o nome do arquivo: impede a escrita
    verifica.assertFalse(pedidos.SalvarPedidosNoArq())

# ==========================================================================
# Ordem de execução: um grupo por função, casos na ordem C1, C2, ...
# ==========================================================================

GRUPOS = [
    # 3.1 CriarPedido(cpf: str) -> dict
    grupo([
        caso_3_1_01_carrinho_valido_e_estoque_suficiente,
        caso_3_1_02_carrinho_vazio,
        caso_3_1_03_estoque_insuficiente,
        caso_3_1_04_cliente_inexistente,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.2 CalcularTotal(itens: list, frete: float, desconto: float) -> float (interna)
    grupo([
        caso_3_2_01_itens_e_frete_sem_desconto,
        caso_3_2_02_itens_frete_e_desconto,
        caso_3_2_03_lista_vazia,
        caso_3_2_04_frete_negativo,
        caso_3_2_05_desconto_negativo,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.3 SimularPagamento(pedido: dict, forma: str) -> bool
    grupo([
        caso_3_3_01_pix_aprovado,
        caso_3_3_02_cartao_aprovado,
        caso_3_3_03_boleto_aprovado,
        caso_3_3_04_cartao_recusado_acima_do_limite,
        caso_3_3_05_boleto_recusado_abaixo_do_minimo,
        caso_3_3_06_forma_de_pagamento_invalida,
        caso_3_3_07_pedido_que_nao_esta_aguardando_pagamento,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.4 AtualizarStatus(num: int, status: str) -> bool (interna)
    grupo([
        caso_3_4_01_alteracao_valida,
        caso_3_4_02_pedido_inexistente,
        caso_3_4_03_status_fora_dos_permitidos,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.5 CancelarPedido(num: int) -> bool
    grupo([
        caso_3_5_01_pedido_aguardando_pagamento,
        caso_3_5_02_pedido_pago,
        caso_3_5_03_pedido_inexistente,
        caso_3_5_04_pedido_ja_cancelado,
        caso_3_5_05_pedido_pago_com_produto_removido,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.6 BuscarPedido(num: int) -> dict (interna)
    grupo([
        caso_3_6_01_pedido_existente,
        caso_3_6_02_pedido_inexistente,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.7 ListarPedidos(status: str) -> list
    grupo([
        caso_3_7_01_pedidos_pagos,
        caso_3_7_02_pedidos_aguardando_pagamento,
        caso_3_7_03_pedidos_cancelados,
        caso_3_7_04_status_vazio_lista_todos,
        caso_3_7_05_status_sem_pedidos,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.8 ListarPedidosCliente(cpf: str) -> list
    grupo([
        caso_3_8_01_cliente_com_mais_de_um_pedido,
        caso_3_8_02_cliente_com_status_variados,
        caso_3_8_03_cliente_sem_pedidos,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
    # 3.9 SalvarPedidosNoArq() -> bool (interna)
    grupo([
        caso_3_9_01_gravacao_bem_sucedida,
        caso_3_9_02_falha_de_gravacao,
    ], antes_de_cada=preparar_cenario, depois_de_cada=limpar_cenario),
]


def load_tests(loader, testes_padrao, padrao):
    """Chamada pelo unittest (discover ou execução direta) para montar a suíte."""
    return montar_suite(GRUPOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
