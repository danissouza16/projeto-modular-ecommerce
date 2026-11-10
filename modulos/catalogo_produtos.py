"""
Módulo 1 · CatalogoProdutos
Responsável: Daniel Santana

Objetivo
    Manter o catálogo de produtos e o estoque da loja. É o ÚNICO módulo
    autorizado a alterar preços e quantidades, e o único que lê e grava
    o arquivo produtos.json (RNF01).

Relações (Diagrama de Arquitetura)
    Servidor de: Main, GerenciadorClientes, ProcessadorPedidos, RelatoriosVendas
    Cliente de:  nenhum módulo

Estrutura de dados encapsulada
    _produtos: lista de dicionários no formato
        {"codigo": str, "nome": str, "descricao": str,
         "categoria": str, "preco": float, "estoque": int}
    O código é o identificador único de cada produto.

Assertivas estruturais
    - Não existem dois produtos com o mesmo código.
    - Todo produto tem preco > 0 e estoque >= 0 (o estoque nunca fica negativo).
    - O estoque só é alterado por BaixarEstoque (1.8) e ReporEstoque (1.9).

Encapsulamento (RNF03)
    - Os dados ficam em variáveis com prefixo "_" e não são exportados.
    - __all__ lista apenas as funções de acesso (1.1 a 1.9).
    - As funções de consulta devolvem CÓPIAS dos produtos, para que nenhum
      módulo cliente consiga alterar o estoque ou o preço por referência.
"""

import json
import os

__all__ = [
    "CadastrarProduto",       # 1.1
    "BuscarProduto",          # 1.2
    "BuscarProdutoPorNome",   # 1.3
    "ListarProdutos",         # 1.4
    "AtualizarProduto",       # 1.5
    "RemoverProduto",         # 1.6
    "ConsultarEstoque",       # 1.7
    "BaixarEstoque",          # 1.8
    "ReporEstoque",           # 1.9
]

# --------------------------------------------------------------------------
# Dados encapsulados
# --------------------------------------------------------------------------

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CAMINHO_ARQUIVO = os.path.join(_RAIZ_PROJETO, "dados", "produtos.json")

_CAMPOS_OBRIGATORIOS = ("codigo", "nome", "descricao", "categoria", "preco", "estoque")
_CAMPOS_TEXTO_ALTERAVEIS = ("nome", "descricao", "categoria")

_produtos = []


# --------------------------------------------------------------------------
# Funções auxiliares internas (não fazem parte da interface)
# --------------------------------------------------------------------------

def _texto_valido(valor):
    """True se valor é str com conteúdo além de espaços."""
    return isinstance(valor, str) and valor.strip() != ""


def _numero_valido(valor):
    """True se valor é int ou float (bool não conta como número)."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro_valido(valor):
    """True se valor é int (bool não conta como inteiro)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _localizar_produto(codigo):
    """Retorna a REFERÊNCIA interna do produto com o código, ou None.
    Uso exclusivo deste módulo: nunca devolver essa referência a clientes."""
    if not isinstance(codigo, str):
        return None
    codigo = codigo.strip()
    for produto in _produtos:
        if produto["codigo"] == codigo:
            return produto
    return None


# --------------------------------------------------------------------------
# 1.1 CadastrarProduto
# --------------------------------------------------------------------------

def CadastrarProduto(p):
    """
    Descrição: inclui um novo produto no catálogo e persiste o arquivo.
    Acoplamento:
        p (dict) com codigo, nome, descricao, categoria, preco, estoque
        Retorno: True  -> produto cadastrado
                 False -> p não é dict, campo ausente/inválido ou código já existe
    AE: p contém os seis campos; textos não vazios; preco > 0; estoque int >= 0.
    AS: se True, o produto está em _produtos e em produtos.json;
        se False, o catálogo não foi alterado.
    """
    if not isinstance(p, dict):
        return False

    for campo in _CAMPOS_OBRIGATORIOS:
        if campo not in p:
            return False

    for campo in ("codigo", "nome", "descricao", "categoria"):
        if not _texto_valido(p[campo]):
            return False

    if not _numero_valido(p["preco"]) or p["preco"] <= 0:
        return False

    if not _inteiro_valido(p["estoque"]) or p["estoque"] < 0:
        return False

    if _localizar_produto(p["codigo"]) is not None:
        return False

    novo_produto = {
        "codigo": p["codigo"].strip(),
        "nome": p["nome"].strip(),
        "descricao": p["descricao"].strip(),
        "categoria": p["categoria"].strip(),
        "preco": float(p["preco"]),
        "estoque": p["estoque"],
    }
    _produtos.append(novo_produto)
    SalvarCatalogoNoArq()
    return True


# --------------------------------------------------------------------------
# 1.2 BuscarProduto
# --------------------------------------------------------------------------

def BuscarProduto(codigo):
    """
    Descrição: busca um produto pelo código.
    Acoplamento:
        codigo (str)
        Retorno: dict com uma cópia do produto | {} se o código não existe
    AS: o catálogo não é alterado.
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return {}
    return dict(produto)


# --------------------------------------------------------------------------
# 1.3 BuscarProdutoPorNome
# --------------------------------------------------------------------------

def BuscarProdutoPorNome(nome):
    """
    Descrição: busca produtos cujo nome contém o texto informado,
               sem diferenciar maiúsculas e minúsculas.
    Acoplamento:
        nome (str)
        Retorno: lista de cópias dos produtos encontrados |
                 [] se nenhum corresponde ou o texto é vazio
    """
    if not _texto_valido(nome):
        return []

    texto = nome.strip().lower()
    encontrados = []
    for produto in _produtos:
        if texto in produto["nome"].lower():
            encontrados.append(dict(produto))
    return encontrados


# --------------------------------------------------------------------------
# 1.4 ListarProdutos
# --------------------------------------------------------------------------

def ListarProdutos(categoria):
    """
    Descrição: lista os produtos de uma categoria; categoria "" lista todos.
               A comparação de categoria não diferencia maiúsculas e minúsculas.
    Acoplamento:
        categoria (str)
        Retorno: lista de cópias dos produtos | [] se não houver produtos
    """
    if not isinstance(categoria, str):
        return []

    categoria = categoria.strip().lower()
    lista = []
    for produto in _produtos:
        if categoria == "" or produto["categoria"].lower() == categoria:
            lista.append(dict(produto))
    return lista


# --------------------------------------------------------------------------
# 1.5 AtualizarProduto
# --------------------------------------------------------------------------

def AtualizarProduto(codigo, campo, valor):
    """
    Descrição: altera UM campo do produto (nome, descricao, categoria ou preco).
               Código e estoque não podem ser alterados por esta função.
    Acoplamento:
        codigo (str), campo (str), valor (str para textos; número > 0 para preco)
        Retorno: True  -> campo atualizado
                 False -> código inexistente, campo inválido ou valor incompatível
    AS: se False, o produto não foi alterado.
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return False

    if campo in _CAMPOS_TEXTO_ALTERAVEIS:
        if not _texto_valido(valor):
            return False
        produto[campo] = valor.strip()
    elif campo == "preco":
        if not _numero_valido(valor) or valor <= 0:
            return False
        produto["preco"] = float(valor)
    else:
        return False

    SalvarCatalogoNoArq()
    return True


# --------------------------------------------------------------------------
# 1.6 RemoverProduto
# --------------------------------------------------------------------------

def RemoverProduto(codigo):
    """
    Descrição: remove o produto do catálogo.
    Acoplamento:
        codigo (str)
        Retorno: True -> removido | False -> código inexistente
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return False

    _produtos.remove(produto)
    SalvarCatalogoNoArq()
    return True


# --------------------------------------------------------------------------
# 1.7 ConsultarEstoque
# --------------------------------------------------------------------------

def ConsultarEstoque(codigo):
    """
    Descrição: informa a quantidade disponível de um produto.
    Acoplamento:
        codigo (str)
        Retorno: quantidade em estoque (int >= 0) | -1 se o código não existe
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return -1
    return produto["estoque"]


# --------------------------------------------------------------------------
# 1.8 BaixarEstoque
# --------------------------------------------------------------------------

def BaixarEstoque(codigo, qtd):
    """
    Descrição: subtrai qtd do estoque após um pagamento aprovado.
    Acoplamento:
        codigo (str), qtd (int)
        Retorno: True  -> baixa realizada
                 False -> código inexistente, qtd <= 0 ou estoque insuficiente
    AE: qtd é int > 0 e qtd <= estoque atual.
    AS: se True, estoque_novo = estoque_antigo - qtd (nunca negativo);
        se False, o estoque não muda.
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return False

    if not _inteiro_valido(qtd) or qtd <= 0:
        return False

    if qtd > produto["estoque"]:
        return False

    produto["estoque"] -= qtd
    SalvarCatalogoNoArq()
    return True


# --------------------------------------------------------------------------
# 1.9 ReporEstoque
# --------------------------------------------------------------------------

def ReporEstoque(codigo, qtd):
    """
    Descrição: soma qtd ao estoque (reposição pelo administrador ou
               devolução no cancelamento de um pedido pago).
    Acoplamento:
        codigo (str), qtd (int)
        Retorno: True  -> reposição realizada
                 False -> código inexistente ou qtd <= 0
    AS: se True, estoque_novo = estoque_antigo + qtd; se False, não muda.
    """
    produto = _localizar_produto(codigo)
    if produto is None:
        return False

    if not _inteiro_valido(qtd) or qtd <= 0:
        return False

    produto["estoque"] += qtd
    SalvarCatalogoNoArq()
    return True


# --------------------------------------------------------------------------
# 1.10 SalvarCatalogoNoArq (interna)
# --------------------------------------------------------------------------

def SalvarCatalogoNoArq():
    """
    Descrição: grava todos os produtos em produtos.json.
    Acoplamento:
        Retorno: True -> gravou | False -> erro de escrita
    """
    try:
        os.makedirs(os.path.dirname(_CAMINHO_ARQUIVO), exist_ok=True)
        with open(_CAMINHO_ARQUIVO, "w", encoding="utf-8") as arquivo:
            json.dump(_produtos, arquivo, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# 1.11 CarregarCatalogoDoArq (interna)
# --------------------------------------------------------------------------

def CarregarCatalogoDoArq():
    """
    Descrição: lê produtos.json para a estrutura interna. Se o arquivo não
               existe, cria-o vazio ("[]") e o catálogo começa vazio.
    Acoplamento:
        Retorno: lista (cópia) dos produtos carregados | [] se vazio,
                 inexistente ou ilegível
    AS: _produtos reflete o conteúdo do arquivo.
    """
    global _produtos

    if not os.path.exists(_CAMINHO_ARQUIVO):
        _produtos = []
        SalvarCatalogoNoArq()
        return []

    try:
        with open(_CAMINHO_ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        _produtos = []
        return []

    if not isinstance(dados, list):
        _produtos = []
        return []

    _produtos = dados
    return [dict(produto) for produto in _produtos]


# --------------------------------------------------------------------------
# Inicialização: carrega o catálogo quando o módulo é importado (RF11)
# --------------------------------------------------------------------------

CarregarCatalogoDoArq()
