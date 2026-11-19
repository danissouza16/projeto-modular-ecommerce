"""
Módulo 2 · GerenciadorClientes
Responsável: Pedro Augusto

Objetivo
    Manter o cadastro e autenticação dos usuários e os carrinhos de compras
    da loja. É o ÚNICO módulo autorizado a alterar dados cadastrais e itens
    dos carrinhos, e o único que lê e grava o arquivo clientes.json (RNF01).

Relações (Diagrama de Arquitetura)
    Servidor de: Main (2.3 a 2.9), ProcessadorPedidos (2.8, 2.10)
    Cliente de:  CatalogoProdutos (1.2, 1.7)

Estrutura de dados encapsulada
    _clientes: lista de dicionários no formato
        {"cpf": str, "nome": str, "email": str, "senha": str,
         "endereco": str, "perfil": str,
         "carrinho": [{"codigo": str, "quantidade": int}, ...]}
    O CPF (somente dígitos, 11 caracteres) é o identificador único de cada cliente.
    O administrador vem pré-cadastrado em clientes.json com perfil "admin" (RNF02).

Assertivas estruturais
- Não existem dois usuários com o mesmo CPF ou o mesmo e-mail (RF01).
- Todo item no carrinho possui código existente no catálogo e quantidade int > 0.
- O módulo consulta o catálogo (1.2, 1.7) antes de aceitar itens, mas nunca altera estoque.

Encapsulamento (RNF03)
- Os dados ficam em variáveis com prefixo "_" e não são exportados.
- __all__ lista apenas as funções públicas de acesso (2.3 a 2.10).
- Funções internas do diagrama (2.1, 2.2, 2.11) e auxiliares (_) não são exportadas.
"""

import copy
import json
import os

from modulos import catalogo_produtos as catalogo

__all__ = [
    "CadastrarCliente",       # 2.3
    "AutenticarCliente",      # 2.4
    "AdicionarItemCarrinho",  # 2.5
    "AlterarQuantidadeItem",  # 2.6
    "RemoverItemCarrinho",    # 2.7
    "ObterCarrinho",          # 2.8
    "CalcularSubtotal",       # 2.9
    "EsvaziarCarrinho",       # 2.10
]

# --------------------------------------------------------------------------
# Dados encapsulados
# --------------------------------------------------------------------------

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CAMINHO_ARQUIVO = os.path.join(_RAIZ_PROJETO, "dados", "clientes.json")

_CAMPOS_OBRIGATORIOS = ("cpf", "nome", "email", "senha", "endereco")

_clientes = []


# --------------------------------------------------------------------------
# Funções auxiliares internas (não fazem parte da interface)
# --------------------------------------------------------------------------

def _texto_valido(valor):
    """True se valor é str com conteúdo além de espaços."""
    return isinstance(valor, str) and valor.strip() != ""


def _inteiro_valido(valor):
    """True se valor é int (bool não conta como inteiro)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _normalizar_cpf(cpf):
    """Remove pontos/traços e retorna string com 11 dígitos se válido, ou None."""
    if not isinstance(cpf, str):
        return None
    digitos = "".join(ch for ch in cpf.strip() if ch.isdigit())
    if len(digitos) != 11:
        return None
    return digitos


def _localizar_cliente_por_cpf(cpf):
    """Retorna a REFERÊNCIA interna do cliente com o CPF, ou None.
    Uso exclusivo deste módulo: nunca devolver essa referência a clientes."""
    cpf_norm = _normalizar_cpf(cpf)
    if cpf_norm is None:
        return None
    for cliente in _clientes:
        if cliente["cpf"] == cpf_norm:
            return cliente
    return None


def _email_ja_cadastrado(email):
    """True se já existe algum usuário com o mesmo e-mail (case-insensitive)."""
    email_norm = email.strip().lower()
    for cliente in _clientes:
        if cliente["email"].strip().lower() == email_norm:
            return True
    return False


def _carregar_clientes_do_arq():
    """Lê clientes.json na inicialização; se não existir, cria vazio ("[]")."""
    global _clientes

    if not os.path.exists(_CAMINHO_ARQUIVO):
        _clientes = []
        SalvarClientesNoArq()
        return []

    try:
        with open(_CAMINHO_ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        _clientes = []
        return []

    if not isinstance(dados, list):
        _clientes = []
        return []

    _clientes = dados
    return copy.deepcopy(_clientes)


# --------------------------------------------------------------------------
# 2.1 ValidarDados (interna)
# --------------------------------------------------------------------------

def ValidarDados(c):
    """
    Descrição: verifica se o dicionário gerado com os dados do cliente possui
               todos os campos obrigatórios e com valores válidos (nome não vazio,
               CPF com 11 dígitos, e-mail contendo "@", senha e endereço preenchidos).
    Acoplamento:
        c (dict)
        Retorno: True -> válido | False -> caso contrário
    """
    if not isinstance(c, dict):
        return False

    for campo in _CAMPOS_OBRIGATORIOS:
        if campo not in c:
            return False

    if _normalizar_cpf(c["cpf"]) is None:
        return False

    for campo in ("nome", "email", "senha", "endereco"):
        if not _texto_valido(c[campo]):
            return False

    email = c["email"].strip()
    if "@" not in email or " " in email:
        return False

    return True


# --------------------------------------------------------------------------
# 2.2 VerificarExistenciaCpf (interna)
# --------------------------------------------------------------------------

def VerificarExistenciaCpf(cpf):
    """
    Descrição: verifica se o CPF já está cadastrado.
    Acoplamento:
        cpf (str)
        Retorno: True -> encontrado | False -> caso contrário
    """
    return _localizar_cliente_por_cpf(cpf) is not None


# --------------------------------------------------------------------------
# 2.3 CadastrarCliente
# --------------------------------------------------------------------------

def CadastrarCliente(c):
    """
    Descrição: valida os dados (2.1), verifica duplicidade de CPF (2.2) e de
               e-mail e inclui o cliente com perfil "cliente" e carrinho vazio.
    Acoplamento:
        c (dict) com cpf, nome, email, senha, endereco
        Retorno: True  -> cliente cadastrado
                 False -> dados inválidos ou CPF/e-mail já existente
    """
    if not ValidarDados(c):
        return False

    cpf_norm = _normalizar_cpf(c["cpf"])
    if VerificarExistenciaCpf(cpf_norm):
        return False

    if _email_ja_cadastrado(c["email"]):
        return False

    novo_cliente = {
        "cpf": cpf_norm,
        "nome": c["nome"].strip(),
        "email": c["email"].strip().lower(),
        "senha": c["senha"].strip(),
        "endereco": c["endereco"].strip(),
        "perfil": "cliente",
        "carrinho": [],
    }
    _clientes.append(novo_cliente)
    SalvarClientesNoArq()
    return True


# --------------------------------------------------------------------------
# 2.4 AutenticarCliente
# --------------------------------------------------------------------------

def AutenticarCliente(email, senha):
    """
    Descrição: verifica o e-mail e a senha e retorna o dicionário do usuário
               (sem a senha, incluindo o perfil "cliente" ou "admin"), ou um
               dicionário vazio se as credenciais forem inválidas.
    Acoplamento:
        email (str), senha (str)
        Retorno: dict do usuário (sem "senha") | {} se credenciais inválidas
    """
    if not _texto_valido(email) or not _texto_valido(senha):
        return {}

    email_norm = email.strip().lower()
    senha_limpa = senha.strip()

    for cliente in _clientes:
        if (cliente["email"].strip().lower() == email_norm
                and cliente["senha"] == senha_limpa):
            usuario = copy.deepcopy(cliente)
            usuario.pop("senha", None)
            return usuario

    return {}


# --------------------------------------------------------------------------
# 2.5 AdicionarItemCarrinho
# --------------------------------------------------------------------------

def AdicionarItemCarrinho(cpf, codigo, qtd):
    """
    Descrição: consulta o produto (1.2) e o estoque (1.7) e adiciona o item
               ao carrinho; se o item já estiver no carrinho, soma as quantidades.
    Acoplamento:
        cpf (str), codigo (str), qtd (int)
        Retorno: True  -> item adicionado/atualizado
                 False -> cliente ou produto inexistente, qtd <= 0 ou
                          estoque insuficiente para a quantidade total
    """
    cliente = _localizar_cliente_por_cpf(cpf)
    if cliente is None:
        return False

    if not _texto_valido(codigo) or not _inteiro_valido(qtd) or qtd <= 0:
        return False

    codigo_limpo = codigo.strip()
    produto = catalogo.BuscarProduto(codigo_limpo)
    if not produto:
        return False

    estoque_disp = catalogo.ConsultarEstoque(codigo_limpo)
    if estoque_disp < 0:
        return False

    item_existente = None
    for item in cliente["carrinho"]:
        if item["codigo"] == codigo_limpo:
            item_existente = item
            break

    qtd_total = qtd + (item_existente["quantidade"] if item_existente else 0)
    if qtd_total > estoque_disp:
        return False

    if item_existente is not None:
        item_existente["quantidade"] = qtd_total
    else:
        cliente["carrinho"].append({"codigo": codigo_limpo, "quantidade": qtd})

    SalvarClientesNoArq()
    return True


# --------------------------------------------------------------------------
# 2.6 AlterarQuantidadeItem
# --------------------------------------------------------------------------

def AlterarQuantidadeItem(cpf, codigo, qtd):
    """
    Descrição: define a nova quantidade de um item já presente no carrinho
               após consultar o estoque (1.7).
    Acoplamento:
        cpf (str), codigo (str), qtd (int)
        Retorno: True  -> quantidade alterada
                 False -> cliente inexistente, item não está no carrinho,
                          qtd <= 0 ou estoque insuficiente
    """
    cliente = _localizar_cliente_por_cpf(cpf)
    if cliente is None or not _texto_valido(codigo):
        return False

    if not _inteiro_valido(qtd) or qtd <= 0:
        return False

    codigo_limpo = codigo.strip()
    item_alvo = None
    for item in cliente["carrinho"]:
        if item["codigo"] == codigo_limpo:
            item_alvo = item
            break

    if item_alvo is None:
        return False

    estoque_disp = catalogo.ConsultarEstoque(codigo_limpo)
    if estoque_disp < 0 or qtd > estoque_disp:
        return False

    item_alvo["quantidade"] = qtd
    SalvarClientesNoArq()
    return True


# --------------------------------------------------------------------------
# 2.7 RemoverItemCarrinho
# --------------------------------------------------------------------------

def RemoverItemCarrinho(cpf, codigo):
    """
    Descrição: remove o item do carrinho.
    Acoplamento:
        cpf (str), codigo (str)
        Retorno: True  -> item removido
                 False -> cliente inexistente ou item não está no carrinho
    """
    cliente = _localizar_cliente_por_cpf(cpf)
    if cliente is None or not _texto_valido(codigo):
        return False

    codigo_limpo = codigo.strip()
    for item in cliente["carrinho"]:
        if item["codigo"] == codigo_limpo:
            cliente["carrinho"].remove(item)
            SalvarClientesNoArq()
            return True

    return False


# --------------------------------------------------------------------------
# 2.8 ObterCarrinho
# --------------------------------------------------------------------------

def ObterCarrinho(cpf):
    """
    Descrição: retorna a lista de itens do carrinho, cada um com código,
               nome, preço unitário e quantidade, ou lista vazia se o carrinho
               estiver vazio ou o cliente não existir.
    Acoplamento:
        cpf (str)
        Retorno: [{"codigo": str, "nome": str, "preco": float, "quantidade": int}, ...]
                 | [] se carrinho vazio ou cliente inexistente
    """
    cliente = _localizar_cliente_por_cpf(cpf)
    if cliente is None:
        return []

    itens = []
    for item in cliente["carrinho"]:
        produto = catalogo.BuscarProduto(item["codigo"])
        if produto:
            itens.append({
                "codigo": item["codigo"],
                "nome": produto["nome"],
                "preco": float(produto["preco"]),
                "quantidade": item["quantidade"],
            })
    return itens


# --------------------------------------------------------------------------
# 2.9 CalcularSubtotal
# --------------------------------------------------------------------------

def CalcularSubtotal(cpf):
    """
    Descrição: retorna a soma de preço * quantidade de todos os itens do
               carrinho ou 0.0 se o carrinho estiver vazio ou cliente inexistente.
    Acoplamento:
        cpf (str)
        Retorno: float (subtotal) | 0.0
    """
    itens = ObterCarrinho(cpf)
    if not itens:
        return 0.0

    total = sum(item["preco"] * item["quantidade"] for item in itens)
    return round(float(total), 2)


# --------------------------------------------------------------------------
# 2.10 EsvaziarCarrinho
# --------------------------------------------------------------------------

def EsvaziarCarrinho(cpf):
    """
    Descrição: remove todos os itens do carrinho após um pagamento aprovado.
    Acoplamento:
        cpf (str)
        Retorno: True -> esvaziou | False -> cliente não existe
    """
    cliente = _localizar_cliente_por_cpf(cpf)
    if cliente is None:
        return False

    cliente["carrinho"] = []
    SalvarClientesNoArq()
    return True


# --------------------------------------------------------------------------
# 2.11 SalvarClientesNoArq (interna)
# --------------------------------------------------------------------------

def SalvarClientesNoArq():
    """
    Descrição: grava os clientes e seus carrinhos no arquivo clientes.json
               após cada alteração.
    Acoplamento:
        Retorno: True -> salvou | False -> erro de escrita
    """
    try:
        os.makedirs(os.path.dirname(_CAMINHO_ARQUIVO), exist_ok=True)
        with open(_CAMINHO_ARQUIVO, "w", encoding="utf-8") as arquivo:
            json.dump(_clientes, arquivo, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# Inicialização: carrega os clientes quando o módulo é importado (RF11)
# --------------------------------------------------------------------------

_carregar_clientes_do_arq()