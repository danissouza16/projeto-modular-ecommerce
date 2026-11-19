"""
Main · Ponto de entrada da Loja Virtual
Responsável: grupo

Objetivo
    Único módulo que conversa com o usuário (input/print). Apresenta os menus,
    lê e converte as entradas e chama SOMENTE as funções de acesso dos módulos.

Controle de acesso por perfil (RNF02)
- Autenticação via 2.4 AutenticarCliente(email, senha) retorna o perfil.
- Administrador ("admin"): gerencia o catálogo e o estoque (e relatórios quando
      o módulo 4 for integrado).
- Cliente ("cliente"): consulta o catálogo e gerencia seu carrinho
      (compras/pedidos entram quando o módulo 3 for integrado).

Relações (Diagrama de Arquitetura)
    Cliente de: CatalogoProdutos (1.1..1.6, 1.9),
                GerenciadorClientes (2.3..2.9)
"""

from modulos import catalogo_produtos as catalogo
from modulos import gerenciador_clientes as clientes


# --------------------------------------------------------------------------
# Auxiliares de entrada e exibição
# --------------------------------------------------------------------------

def _ler_texto(mensagem):
    """Lê um texto sem espaços nas pontas."""
    return input(mensagem).strip()


def _ler_inteiro(mensagem):
    """Lê um inteiro; devolve None se o valor digitado não for inteiro."""
    try:
        return int(input(mensagem).strip())
    except ValueError:
        return None


def _ler_preco(mensagem):
    """Lê um número real (aceita vírgula); devolve None se inválido."""
    try:
        return float(input(mensagem).strip().replace(",", "."))
    except ValueError:
        return None


def _mostrar_produto(p):
    print(f"  [{p['codigo']}] {p['nome']} - {p['categoria']} - "
          f"R$ {p['preco']:.2f} - estoque: {p['estoque']}")
    print(f"        {p['descricao']}")


def _mostrar_lista(produtos):
    if not produtos:
        print("  Nenhum produto encontrado.")
        return
    for p in produtos:
        _mostrar_produto(p)


def _mostrar_carrinho(cpf):
    itens = clientes.ObterCarrinho(cpf)
    if not itens:
        print("  Carrinho vazio.")
        return
    for item in itens:
        subtotal_item = item["preco"] * item["quantidade"]
        print(f"  [{item['codigo']}] {item['nome']} - "
              f"{item['quantidade']}x R$ {item['preco']:.2f} = R$ {subtotal_item:.2f}")
    print(f"  Subtotal do carrinho: R$ {clientes.CalcularSubtotal(cpf):.2f}")


def _resultado(ok, msg_ok, msg_erro):
    print(msg_ok if ok else msg_erro)


# --------------------------------------------------------------------------
# Ações de autenticação e cadastro (2.3, 2.4)
# --------------------------------------------------------------------------

def _cadastrar_cliente():
    cliente = {
        "cpf": _ler_texto("CPF (11 dígitos): "),
        "nome": _ler_texto("Nome completo: "),
        "email": _ler_texto("E-mail: "),
        "senha": _ler_texto("Senha: "),
        "endereco": _ler_texto("Endereço: "),
    }
    _resultado(clientes.CadastrarCliente(cliente),
               "Cadastro realizado com sucesso! Faça login para continuar.",
               "Não foi possível cadastrar (dados inválidos ou CPF/e-mail já existente).")


def _fazer_login():
    email = _ler_texto("E-mail: ")
    senha = _ler_texto("Senha: ")
    usuario = clientes.AutenticarCliente(email, senha)
    if not usuario:
        print("E-mail ou senha inválidos.")
        return None
    print(f"Bem-vindo(a), {usuario['nome']}!")
    return usuario


# --------------------------------------------------------------------------
# Ações do catálogo (1.1 a 1.6, 1.9)
# --------------------------------------------------------------------------

def _listar_produtos():
    categoria = _ler_texto("Categoria (Enter para todas): ")
    _mostrar_lista(catalogo.ListarProdutos(categoria))


def _buscar_por_codigo():
    produto = catalogo.BuscarProduto(_ler_texto("Código: "))
    if produto:
        _mostrar_produto(produto)
    else:
        print("Produto não encontrado.")


def _buscar_por_nome():
    _mostrar_lista(catalogo.BuscarProdutoPorNome(_ler_texto("Parte do nome: ")))


def _cadastrar_produto():
    produto = {
        "codigo": _ler_texto("Código: "),
        "nome": _ler_texto("Nome: "),
        "descricao": _ler_texto("Descrição: "),
        "categoria": _ler_texto("Categoria: "),
        "preco": _ler_preco("Preço: "),
        "estoque": _ler_inteiro("Estoque inicial: "),
    }
    _resultado(catalogo.CadastrarProduto(produto),
               "Produto cadastrado.",
               "Não foi possível cadastrar (código repetido ou dados inválidos).")


def _atualizar_produto():
    codigo = _ler_texto("Código: ")
    campo = _ler_texto("Campo (nome, descricao, categoria, preco): ").lower()
    if campo == "preco":
        valor = _ler_preco("Novo preço: ")
    else:
        valor = _ler_texto("Novo valor: ")
    _resultado(catalogo.AtualizarProduto(codigo, campo, valor),
               "Produto atualizado.",
               "Não foi possível atualizar (código, campo ou valor inválido).")


def _remover_produto():
    _resultado(catalogo.RemoverProduto(_ler_texto("Código: ")),
               "Produto removido.",
               "Produto não encontrado.")


def _repor_estoque():
    codigo = _ler_texto("Código: ")
    qtd = _ler_inteiro("Quantidade a repor: ")
    _resultado(catalogo.ReporEstoque(codigo, qtd),
               "Estoque reposto.",
               "Não foi possível repor (código inexistente ou quantidade inválida).")


# --------------------------------------------------------------------------
# Fluxos do sistema (Seção 3.1)
# --------------------------------------------------------------------------

def _executar_menu(titulo, opcoes):
    """Mostra o menu até o usuário escolher 0. opcoes: lista de (texto, função)."""
    while True:
        print(f"\n=== {titulo} ===")
        for i, (texto, _) in enumerate(opcoes, start=1):
            print(f"{i} - {texto}")
        print("0 - Voltar")

        escolha = _ler_inteiro("Opção: ")
        if escolha == 0:
            return
        if escolha is None or not 1 <= escolha <= len(opcoes):
            print("Opção inválida.")
            continue
        opcoes[escolha - 1][1]()


def fluxo_catalogo(perfil):
    """Conduz consulta de produtos (todos) e manutenção (apenas admin)."""
    opcoes = [
        ("Listar produtos", _listar_produtos),
        ("Buscar produto por código", _buscar_por_codigo),
        ("Buscar produto por nome", _buscar_por_nome),
    ]
    if perfil == "admin":
        opcoes.extend([
            ("Cadastrar produto", _cadastrar_produto),
            ("Atualizar produto", _atualizar_produto),
            ("Remover produto", _remover_produto),
            ("Repor estoque", _repor_estoque),
        ])
    _executar_menu("Catálogo de Produtos", opcoes)


def fluxo_carrinho(cpf):
    """Conduz inclusão, alteração, remoção e visualização do carrinho (2.5 a 2.9)."""
    def _adicionar():
        codigo = _ler_texto("Código do produto: ")
        qtd = _ler_inteiro("Quantidade: ")
        _resultado(clientes.AdicionarItemCarrinho(cpf, codigo, qtd),
                   "Item adicionado ao carrinho.",
                   "Não foi possível adicionar (produto inexistente, quantidade inválida ou estoque insuficiente).")

    def _alterar_qtd():
        codigo = _ler_texto("Código do produto: ")
        qtd = _ler_inteiro("Nova quantidade: ")
        _resultado(clientes.AlterarQuantidadeItem(cpf, codigo, qtd),
                   "Quantidade atualizada.",
                   "Não foi possível alterar (item fora do carrinho, quantidade <= 0 ou estoque insuficiente).")

    def _remover():
        codigo = _ler_texto("Código do produto: ")
        _resultado(clientes.RemoverItemCarrinho(cpf, codigo),
                   "Item removido do carrinho.",
                   "Item não encontrado no carrinho.")

    def _ver():
        _mostrar_carrinho(cpf)

    _executar_menu("Meu Carrinho", [
        ("Ver carrinho e subtotal", _ver),
        ("Adicionar item ao carrinho", _adicionar),
        ("Alterar quantidade de item", _alterar_qtd),
        ("Remover item do carrinho", _remover),
    ])


def _sessao_administrador():
    _executar_menu("Menu Administrador", [
        ("Catálogo e Estoque", lambda: fluxo_catalogo("admin")),
    ])


def _sessao_cliente(usuario):
    cpf = usuario["cpf"]
    _executar_menu(f"Menu Cliente ({usuario['nome']})", [
        ("Consultar Catálogo", lambda: fluxo_catalogo("cliente")),
        ("Meu Carrinho", lambda: fluxo_carrinho(cpf)),
    ])


def menu():
    while True:
        print("\n=== Loja Virtual ===")
        print("1 - Entrar (Login)")
        print("2 - Cadastrar-se como cliente")
        print("0 - Sair")

        escolha = _ler_inteiro("Opção: ")
        if escolha == 1:
            usuario = _fazer_login()
            if usuario:
                if usuario.get("perfil") == "admin":
                    _sessao_administrador()
                else:
                    _sessao_cliente(usuario)
        elif escolha == 2:
            _cadastrar_cliente()
        elif escolha == 0:
            print("Até logo!")
            return
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()