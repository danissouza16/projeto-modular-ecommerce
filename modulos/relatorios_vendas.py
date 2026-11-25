"""
Módulo 4 · RelatoriosVendas
Responsável: Matheus

Objetivo
    Gerar os relatórios gerenciais do administrador (faturamento, ticket médio,
    mais vendidos, vendas por cliente, estoque baixo) e exportá-los para
    arquivo de texto. Apenas LÊ dados dos outros módulos, nunca os altera.

Relações (Diagrama de Arquitetura)
    Servidor de: Main (4.1 a 4.6)
    Cliente de:  ProcessadorPedidos (3.7), CatalogoProdutos (1.2, 1.4)

Estrutura de dados encapsulada
    Nenhuma. O módulo não possui arquivo nem estado próprio: todo dado vem
    das funções de acesso dos módulos servidores a cada chamada.

Assertivas estruturais
    - Somente pedidos com status "Pago" entram nos relatórios.
    - Datas são texto no formato AAAA-MM-DD; períodos são inclusivos nas duas pontas.
    - Entradas inválidas nunca geram exceção: retornam 0.0, [] ou False.

Encapsulamento (RNF03)
    - Não há variáveis globais de dados.
    - __all__ lista apenas as funções de acesso (4.1 a 4.6).
    - Funções auxiliares têm prefixo "_" e não são exportadas.
    - Só são chamadas as funções 3.7, 1.2 e 1.4 dos outros módulos.

Restrições
    - As auxiliares _normalizar_cpf, _texto_valido e _inteiro_valido se
      repetem em outros módulos de propósito: pelo RNF03 um módulo só pode
      chamar as funções do Diagrama de Funções de Acesso, e nenhuma delas
      está lá. Compartilhá-las exigiria um módulo utilitário novo no diagrama.
"""

from datetime import datetime

from modulos import catalogo_produtos as catalogo
from modulos import processador_pedidos as pedidos

__all__ = [
    "CalcularFaturamento",   # 4.1
    "CalcularTicketMedio",   # 4.2
    "ListarMaisVendidos",    # 4.3
    "VendasPorCliente",      # 4.4
    "ListarEstoqueBaixo",    # 4.5
    "ExportarRelatorio",     # 4.6
]

_STATUS_PAGO = "Pago"
_CARACTERES_PROIBIDOS_ARQUIVO = '\\/:*?"<>|'


# --------------------------------------------------------------------------
# Funções auxiliares internas (não fazem parte da interface)
# --------------------------------------------------------------------------

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


def _converter_data(texto):
    """Converte 'AAAA-MM-DD' em date; retorna None se inválida ou fora do formato."""
    if not isinstance(texto, str):
        return None
    texto = texto.strip()
    try:
        data = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None
    if data.isoformat() != texto:      # recusa formatos frouxos como 2026-9-1
        return None
    return data


def _pedidos_pagos():
    """Pedidos com status 'Pago' obtidos do módulo 3 (3.7)."""
    pagos = []
    for pedido in pedidos.ListarPedidos(_STATUS_PAGO):
        if pedido.get("status") == _STATUS_PAGO:
            pagos.append(pedido)
    return pagos


def _pagos_no_periodo(inicio, fim):
    """Pedidos pagos com data entre inicio e fim (inclusive); [] se datas
    inválidas ou inicio posterior a fim."""
    data_ini = _converter_data(inicio)
    data_fim = _converter_data(fim)
    if data_ini is None or data_fim is None or data_ini > data_fim:
        return []

    selecionados = []
    for pedido in _pedidos_pagos():
        data = _converter_data(pedido.get("data"))
        if data is not None and data_ini <= data <= data_fim:
            selecionados.append(pedido)
    return selecionados


# --------------------------------------------------------------------------
# 4.1 CalcularFaturamento
# --------------------------------------------------------------------------

def CalcularFaturamento(inicio, fim):
    """
    A) Descrição: soma o total dos pedidos pagos no período (inclusivo).
    B) Acoplamento:
        inicio (str), fim (str) no formato AAAA-MM-DD
        Retorno: valor faturado (float, 2 casas) |
                 0.0 se não há pedidos pagos no período, data inválida
                 ou inicio posterior a fim
    C) Condições de acoplamento:
        AE: inicio e fim são datas válidas AAAA-MM-DD com inicio <= fim.
        AS: nenhum dado é alterado; só entram pedidos "Pago" com data no
            período, inclusive nas duas pontas.
    """
    total = 0.0
    for pedido in _pagos_no_periodo(inicio, fim):
        total += pedido["total"]
    return round(total, 2)


# --------------------------------------------------------------------------
# 4.2 CalcularTicketMedio
# --------------------------------------------------------------------------

def CalcularTicketMedio(inicio, fim):
    """
    A) Descrição: faturamento do período dividido pelo número de pedidos pagos.
    B) Acoplamento:
        inicio (str), fim (str) no formato AAAA-MM-DD
        Retorno: valor médio por pedido (float, 2 casas) |
                 0.0 se não há pedidos pagos no período ou datas inválidas
    C) Condições de acoplamento:
        AE: inicio e fim são datas válidas AAAA-MM-DD com inicio <= fim.
        AS: nenhum dado é alterado; nunca há divisão por zero.
    """
    selecionados = _pagos_no_periodo(inicio, fim)
    if len(selecionados) == 0:
        return 0.0

    total = 0.0
    for pedido in selecionados:
        total += pedido["total"]
    return round(total / len(selecionados), 2)


# --------------------------------------------------------------------------
# 4.3 ListarMaisVendidos
# --------------------------------------------------------------------------

def ListarMaisVendidos(n):
    """
    A) Descrição: ranking dos n produtos mais vendidos em pedidos pagos.
               Empates na quantidade são desempatados pelo código (crescente).
               O nome vem do catálogo (1.2); se o produto não existir mais
               no catálogo, usa o nome registrado no item do pedido ou,
               na falta dele, o próprio código.
    B) Acoplamento:
        n (int)
        Retorno: [{"codigo": str, "nome": str, "quantidade": int}, ...]
                 em ordem decrescente de quantidade |
                 [] se n <= 0, n não é int ou não há vendas
    C) Condições de acoplamento:
        AE: n é int > 0.
        AS: nenhum dado é alterado; a lista tem no máximo n itens, só conta
            pedidos "Pago" e está em ordem decrescente de quantidade.
    """
    if not _inteiro_valido(n) or n <= 0:
        return []

    quantidades = {}
    nomes_nos_pedidos = {}
    for pedido in _pedidos_pagos():
        for item in pedido.get("itens", []):
            codigo = item["codigo"]
            quantidades[codigo] = quantidades.get(codigo, 0) + item["quantidade"]
            if "nome" in item:
                nomes_nos_pedidos[codigo] = item["nome"]

    ordenados = sorted(quantidades.items(), key=lambda par: (-par[1], par[0]))

    ranking = []
    for codigo, quantidade in ordenados[:n]:
        produto = catalogo.BuscarProduto(codigo)
        if produto:
            nome = produto["nome"]
        else:
            nome = nomes_nos_pedidos.get(codigo, codigo)
        ranking.append({"codigo": codigo, "nome": nome, "quantidade": quantidade})
    return ranking


# --------------------------------------------------------------------------
# 4.4 VendasPorCliente
# --------------------------------------------------------------------------

def VendasPorCliente(cpf):
    """
    A) Descrição: pedidos pagos de um cliente, na ordem em que a 3.7 os fornece.
    B) Acoplamento:
        cpf (str)
        Retorno: [{"numero": int, "data": str, "total": float}, ...] |
                 [] se o cliente não tem compras, não existe ou cpf inválido
    C) Condições de acoplamento:
        AE: cpf é str com 11 dígitos (pontos e traço são ignorados).
        AS: nenhum dado é alterado; só entram pedidos "Pago" do cliente.
    """
    cpf_norm = _normalizar_cpf(cpf)
    if cpf_norm is None:
        return []

    vendas = []
    for pedido in _pedidos_pagos():
        if pedido.get("cpf") == cpf_norm:
            vendas.append({
                "numero": pedido["numero"],
                "data": pedido["data"],
                "total": pedido["total"],
            })
    return vendas


# --------------------------------------------------------------------------
# 4.5 ListarEstoqueBaixo
# --------------------------------------------------------------------------

def ListarEstoqueBaixo(limite):
    """
    A) Descrição: produtos com estoque menor ou igual ao limite (inclusivo).
    B) Acoplamento:
        limite (int)
        Retorno: lista de produtos (cópias vindas de 1.4) |
                 [] se nenhum atende, limite negativo ou limite não é int
    C) Condições de acoplamento:
        AE: limite é int >= 0.
        AS: nenhum dado é alterado; todo produto devolvido tem
            estoque <= limite.
    """
    if not _inteiro_valido(limite) or limite < 0:
        return []

    baixos = []
    for produto in catalogo.ListarProdutos(""):
        if produto["estoque"] <= limite:
            baixos.append(produto)
    return baixos


# --------------------------------------------------------------------------
# 4.6 ExportarRelatorio
# --------------------------------------------------------------------------

def ExportarRelatorio(dados, arq):
    """
    A) Descrição: grava o resultado de um relatório em arquivo de texto
               (UTF-8), uma linha por item no formato "campo: valor | ...".
               O arquivo é criado no diretório de trabalho atual.
    B) Acoplamento:
        dados (list) não vazia, arq (str) nome simples de arquivo
              (sem os caracteres \\ / : * ? " < > |)
        Retorno: True  -> exportou
                 False -> lista vazia/inválida, nome inválido ou erro de escrita
    C) Condições de acoplamento:
        AE: dados é lista não vazia; arq é nome de arquivo válido.
        AS: se True, o arquivo existe com uma linha por item de dados;
            se False por validação, nenhum arquivo é criado.
    """
    if not isinstance(dados, list) or len(dados) == 0:
        return False

    if not isinstance(arq, str) or arq.strip() == "":
        return False
    arq = arq.strip()
    for caractere in arq:
        if caractere in _CARACTERES_PROIBIDOS_ARQUIVO or ord(caractere) < 32:
            return False

    linhas = []
    for item in dados:
        if isinstance(item, dict):
            partes = [f"{chave}: {valor}" for chave, valor in item.items()]
            linhas.append(" | ".join(partes))
        else:
            linhas.append(str(item))

    try:
        with open(arq, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
        return True
    except OSError:
        return False
