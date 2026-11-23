"""
Módulo 3 · ProcessadorPedidos
Responsáveis: Brenno Távora e Guilherme Meira

Objetivo
    Transformar o carrinho de um cliente em pedido, simular o pagamento,
    cancelar pedidos e consultar o histórico. É o ÚNICO módulo autorizado a
    criar ou alterar pedidos, e o único que lê e grava o arquivo pedidos.json
    (RNF01).

Relações (Diagrama de Arquitetura)
    Servidor de: Main (3.1, 3.3, 3.5, 3.8), RelatoriosVendas (3.7)
    Cliente de:  CatalogoProdutos (1.7, 1.8, 1.9),
                 GerenciadorClientes (2.8, 2.10)

Estrutura de dados encapsulada
    _pedidos: lista de dicionários no formato
        {"numero": int, "cpf": str, "data": "AAAA-MM-DD",
         "itens": [{"codigo": str, "nome": str, "preco": float,
                    "quantidade": int}, ...],
         "subtotal": float, "frete": float, "desconto": float,
         "total": float, "status": str}
    O número do pedido é sequencial (maior número existente + 1) e é o
    identificador único. Status possíveis: "Aguardando pagamento", "Pago",
    "Cancelado".

Regras de negócio (usadas nos casos de teste da seção 5.3)
    - Frete fixo de 10.00 e desconto de 0.00 em todo pedido.
    - total = subtotal - desconto + frete.
    - Pagamento simulado: Pix é sempre aprovado; cartão é aprovado se
      total <= 500.00; boleto é aprovado se total >= 50.00.
    - Pagamento aprovado: baixa o estoque (1.8), esvazia o carrinho (2.10)
      e muda o status para "Pago".
    - Pagamento recusado: o pedido passa a "Cancelado" e o estoque não muda.
    - Cancelar um pedido "Pago" devolve os itens ao estoque (1.9).

Assertivas estruturais
    - Não existem dois pedidos com o mesmo número.
    - Todo pedido tem ao menos um item, com quantidade int > 0.
    - A baixa de estoque acontece uma única vez por pedido (só na passagem
      de "Aguardando pagamento" para "Pago").

Encapsulamento (RNF03)
    - Os dados ficam em variáveis com prefixo "_" e não são exportados.
    - __all__ lista apenas as funções chamadas por outros módulos
      (3.1, 3.3, 3.5, 3.7 e 3.8).
    - Funções internas do diagrama (3.2, 3.4, 3.6, 3.9) e auxiliares (_)
      não são exportadas.
    - As funções de consulta devolvem CÓPIAS dos pedidos.
"""

import copy
import datetime
import json
import os

from modulos import catalogo_produtos as catalogo
from modulos import gerenciador_clientes as clientes

__all__ = [
    "CriarPedido",            # 3.1
    "SimularPagamento",       # 3.3
    "CancelarPedido",         # 3.5
    "ListarPedidos",          # 3.7
    "ListarPedidosCliente",   # 3.8
]

# --------------------------------------------------------------------------
# Dados encapsulados
# --------------------------------------------------------------------------

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CAMINHO_ARQUIVO = os.path.join(_RAIZ_PROJETO, "dados", "pedidos.json")

_STATUS_AGUARDANDO = "Aguardando pagamento"
_STATUS_PAGO = "Pago"
_STATUS_CANCELADO = "Cancelado"
_STATUS_VALIDOS = (_STATUS_AGUARDANDO, _STATUS_PAGO, _STATUS_CANCELADO)

_FRETE_FIXO = 10.00
_DESCONTO_PADRAO = 0.00
_LIMITE_CARTAO = 500.00
_MINIMO_BOLETO = 50.00

_pedidos = []


# --------------------------------------------------------------------------
# Funções auxiliares internas (não fazem parte da interface)
# --------------------------------------------------------------------------

def _numero_valido(valor):
    """True se valor é int ou float (bool não conta como número)."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro_valido(valor):
    """True se valor é int (bool não conta como inteiro)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _normalizar_cpf(cpf):
    """Devolve o CPF só com dígitos se tiver 11, ou None."""
    if not isinstance(cpf, str):
        return None
    digitos = "".join(ch for ch in cpf.strip() if ch.isdigit())
    if len(digitos) != 11:
        return None
    return digitos


def _status_canonico(texto):
    """Devolve o status escrito do jeito oficial (ignora maiúsculas e
    espaços nas pontas) ou None se não for um dos três status válidos."""
    if not isinstance(texto, str):
        return None
    texto = texto.strip().lower()
    for status in _STATUS_VALIDOS:
        if status.lower() == texto:
            return status
    return None


def _localizar_pedido(num):
    """Retorna a REFERÊNCIA interna do pedido com o número, ou None.
    Uso exclusivo deste módulo: nunca devolver essa referência a clientes."""
    if not _inteiro_valido(num):
        return None
    for pedido in _pedidos:
        if pedido["numero"] == num:
            return pedido
    return None


def _proximo_numero():
    """Próximo número sequencial de pedido."""
    maior = 0
    for pedido in _pedidos:
        if pedido["numero"] > maior:
            maior = pedido["numero"]
    return maior + 1


def _pagamento_aprovado(forma, total):
    """True/False conforme a regra da forma de pagamento; None se a forma
    de pagamento é inválida."""
    if not isinstance(forma, str):
        return None
    forma = forma.strip().lower()
    if forma == "pix":
        return True
    if forma in ("cartao", "cartão"):
        return total <= _LIMITE_CARTAO
    if forma == "boleto":
        return total >= _MINIMO_BOLETO
    return None


def _carregar_pedidos_do_arq():
    """Lê pedidos.json na inicialização; se não existir, cria vazio ("[]")."""
    global _pedidos

    if not os.path.exists(_CAMINHO_ARQUIVO):
        _pedidos = []
        SalvarPedidosNoArq()
        return []

    try:
        with open(_CAMINHO_ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        _pedidos = []
        return []

    if not isinstance(dados, list):
        _pedidos = []
        return []

    _pedidos = dados
    return copy.deepcopy(_pedidos)


# --------------------------------------------------------------------------
# 3.1 CriarPedido
# --------------------------------------------------------------------------

def CriarPedido(cpf):
    """
    Descrição: lê o carrinho do cliente (2.8), confere o estoque de cada
               item (1.7), calcula o total (3.2) e registra o pedido com
               status "Aguardando pagamento". O carrinho só é esvaziado
               quando o pagamento é aprovado (3.3).
    Acoplamento:
        cpf (str)
        Retorno: dict com o pedido criado
                 | {} se o cliente não existe, o carrinho está vazio ou
                   algum item tem estoque insuficiente
    AS: se retornou pedido, ele está em _pedidos e em pedidos.json;
        se {}, nada foi criado.
    """
    cpf_norm = _normalizar_cpf(cpf)
    if cpf_norm is None:
        return {}

    itens = clientes.ObterCarrinho(cpf_norm)
    if not itens:
        return {}

    for item in itens:
        if catalogo.ConsultarEstoque(item["codigo"]) < item["quantidade"]:
            return {}

    subtotal = round(sum(i["preco"] * i["quantidade"] for i in itens), 2)
    total = CalcularTotal(itens, _FRETE_FIXO, _DESCONTO_PADRAO)

    pedido = {
        "numero": _proximo_numero(),
        "cpf": cpf_norm,
        "data": datetime.date.today().isoformat(),
        "itens": [dict(i) for i in itens],
        "subtotal": subtotal,
        "frete": _FRETE_FIXO,
        "desconto": _DESCONTO_PADRAO,
        "total": total,
        "status": _STATUS_AGUARDANDO,
    }
    _pedidos.append(pedido)
    SalvarPedidosNoArq()
    return copy.deepcopy(pedido)


# --------------------------------------------------------------------------
# 3.2 CalcularTotal (interna)
# --------------------------------------------------------------------------

def CalcularTotal(itens, frete, desconto):
    """
    Descrição: soma preço * quantidade dos itens, subtrai o desconto e soma
               o frete.
    Acoplamento:
        itens (list de dict com preco e quantidade), frete (float >= 0),
        desconto (float >= 0)
        Retorno: total calculado, arredondado em 2 casas
                 | 0.0 se a lista é vazia/inválida, ou frete ou desconto negativos
    """
    if not isinstance(itens, list) or not itens:
        return 0.0
    if not _numero_valido(frete) or frete < 0:
        return 0.0
    if not _numero_valido(desconto) or desconto < 0:
        return 0.0

    subtotal = 0.0
    for item in itens:
        if not isinstance(item, dict):
            return 0.0
        preco = item.get("preco")
        qtd = item.get("quantidade")
        if not _numero_valido(preco) or preco < 0:
            return 0.0
        if not _inteiro_valido(qtd) or qtd <= 0:
            return 0.0
        subtotal += preco * qtd

    total = max(subtotal - desconto, 0.0) + frete
    return round(total, 2)


# --------------------------------------------------------------------------
# 3.3 SimularPagamento
# --------------------------------------------------------------------------

def SimularPagamento(pedido, forma):
    """
    Descrição: simula o pagamento de um pedido "Aguardando pagamento".
               Aprovado: baixa o estoque (1.8), esvazia o carrinho (2.10) e
               muda o status para "Pago". Recusado: muda o status para
               "Cancelado" sem mexer no estoque.
    Acoplamento:
        pedido (dict com ao menos "numero"), forma (str: "pix", "cartao" ou "boleto")
        Retorno: True  -> pagamento aprovado
                 False -> pedido inexistente ou que não está aguardando
                          pagamento, forma inválida (o pedido continua
                          aguardando), pagamento recusado ou estoque
                          insuficiente (o pedido é cancelado)
    AS: a baixa de estoque ocorre uma única vez por pedido.
    """
    if not isinstance(pedido, dict):
        return False

    registro = _localizar_pedido(pedido.get("numero"))
    if registro is None or registro["status"] != _STATUS_AGUARDANDO:
        return False

    aprovado = _pagamento_aprovado(forma, registro["total"])
    if aprovado is None:
        return False

    if not aprovado:
        registro["status"] = _STATUS_CANCELADO
        SalvarPedidosNoArq()
        return False

    # Confere o estoque de todos os itens antes de baixar qualquer um
    for item in registro["itens"]:
        if catalogo.ConsultarEstoque(item["codigo"]) < item["quantidade"]:
            registro["status"] = _STATUS_CANCELADO
            SalvarPedidosNoArq()
            return False

    baixados = []
    for item in registro["itens"]:
        if catalogo.BaixarEstoque(item["codigo"], item["quantidade"]):
            baixados.append(item)
        else:
            for feito in baixados:                      # desfaz o que já baixou
                catalogo.ReporEstoque(feito["codigo"], feito["quantidade"])
            registro["status"] = _STATUS_CANCELADO
            SalvarPedidosNoArq()
            return False

    clientes.EsvaziarCarrinho(registro["cpf"])
    registro["status"] = _STATUS_PAGO
    SalvarPedidosNoArq()
    return True


# --------------------------------------------------------------------------
# 3.4 AtualizarStatus (interna)
# --------------------------------------------------------------------------

def AtualizarStatus(num, status):
    """
    Descrição: altera o status de um pedido para "Aguardando pagamento",
               "Pago" ou "Cancelado". Não mexe no estoque.
    Acoplamento:
        num (int), status (str)
        Retorno: True -> status alterado
                 False -> pedido inexistente ou status fora dos três permitidos
    """
    novo_status = _status_canonico(status)
    if novo_status is None:
        return False

    registro = _localizar_pedido(num)
    if registro is None:
        return False

    registro["status"] = novo_status
    SalvarPedidosNoArq()
    return True


# --------------------------------------------------------------------------
# 3.5 CancelarPedido
# --------------------------------------------------------------------------

def CancelarPedido(num):
    """
    Descrição: cancela um pedido. Se o pedido estava "Pago", devolve os
               itens ao estoque (1.9).
    Acoplamento:
        num (int)
        Retorno: True  -> pedido cancelado
                 False -> pedido inexistente ou já cancelado
    """
    registro = _localizar_pedido(num)
    if registro is None or registro["status"] == _STATUS_CANCELADO:
        return False

    if registro["status"] == _STATUS_PAGO:
        for item in registro["itens"]:
            catalogo.ReporEstoque(item["codigo"], item["quantidade"])

    registro["status"] = _STATUS_CANCELADO
    SalvarPedidosNoArq()
    return True


# --------------------------------------------------------------------------
# 3.6 BuscarPedido (interna)
# --------------------------------------------------------------------------

def BuscarPedido(num):
    """
    Descrição: busca um pedido pelo número.
    Acoplamento:
        num (int)
        Retorno: dict com uma cópia do pedido | {} se não existe
    """
    registro = _localizar_pedido(num)
    if registro is None:
        return {}
    return copy.deepcopy(registro)


# --------------------------------------------------------------------------
# 3.7 ListarPedidos
# --------------------------------------------------------------------------

def ListarPedidos(status):
    """
    Descrição: lista os pedidos com o status informado; status "" lista todos.
               A comparação ignora maiúsculas e minúsculas.
    Acoplamento:
        status (str)
        Retorno: lista de cópias dos pedidos | [] se nenhum corresponde
                 ou o status é inválido
    """
    if not isinstance(status, str):
        return []

    if status.strip() == "":
        return [copy.deepcopy(p) for p in _pedidos]

    alvo = _status_canonico(status)
    if alvo is None:
        return []
    return [copy.deepcopy(p) for p in _pedidos if p["status"] == alvo]


# --------------------------------------------------------------------------
# 3.8 ListarPedidosCliente
# --------------------------------------------------------------------------

def ListarPedidosCliente(cpf):
    """
    Descrição: lista todos os pedidos de um cliente, do mais recente ao
               mais antigo (data e, em empate, número decrescentes).
    Acoplamento:
        cpf (str)
        Retorno: lista de cópias dos pedidos | [] se o cliente não tem
                 pedidos ou o CPF é inválido
    """
    cpf_norm = _normalizar_cpf(cpf)
    if cpf_norm is None:
        return []

    do_cliente = [p for p in _pedidos if p["cpf"] == cpf_norm]
    do_cliente.sort(key=lambda p: (p["data"], p["numero"]), reverse=True)
    return [copy.deepcopy(p) for p in do_cliente]


# --------------------------------------------------------------------------
# 3.9 SalvarPedidosNoArq (interna)
# --------------------------------------------------------------------------

def SalvarPedidosNoArq():
    """
    Descrição: grava todos os pedidos no arquivo pedidos.json após cada
               alteração.
    Acoplamento:
        Retorno: True -> salvou | False -> erro de escrita
    """
    try:
        os.makedirs(os.path.dirname(_CAMINHO_ARQUIVO), exist_ok=True)
        with open(_CAMINHO_ARQUIVO, "w", encoding="utf-8") as arquivo:
            json.dump(_pedidos, arquivo, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# Inicialização: carrega os pedidos quando o módulo é importado (RF11)
# --------------------------------------------------------------------------

_carregar_pedidos_do_arq()
