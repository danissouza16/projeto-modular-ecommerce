"""
Main · Ponto de entrada da Loja Virtual
Responsável: grupo

Objetivo
    Único módulo que conversa com o usuário (input/print). Apresenta os menus,
    lê e converte as entradas e chama SOMENTE as funções de acesso dos módulos.

Controle de acesso por perfil (RNF02)
    - Administrador: gerencia o catálogo e o estoque.
    - Cliente: apenas consulta o catálogo (carrinho e pedidos entram quando
      os módulos 2 e 3 forem integrados).

Relações (Diagrama de Arquitetura)
    Cliente de: CatalogoProdutos (demais módulos serão adicionados na integração)
"""

from modulos import catalogo_produtos as catalogo


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


def _resultado(ok, msg_ok, msg_erro):
    print(msg_ok if ok else msg_erro)


# --------------------------------------------------------------------------
# Ações do catálogo
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


def _consultar_estoque():
    qtd = catalogo.ConsultarEstoque(_ler_texto("Código: "))
    print("Produto não encontrado." if qtd == -1 else f"Estoque: {qtd}")


def _repor_estoque():
    codigo = _ler_texto("Código: ")
    qtd = _ler_inteiro("Quantidade a repor: ")
    _resultado(catalogo.ReporEstoque(codigo, qtd),
               "Estoque reposto.",
               "Não foi possível repor (código inexistente ou quantidade inválida).")


# --------------------------------------------------------------------------
# Menus
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


def _menu_administrador():
    _executar_menu("Administrador - Catálogo", [
        ("Listar produtos", _listar_produtos),
        ("Buscar produto por código", _buscar_por_codigo),
        ("Buscar produto por nome", _buscar_por_nome),
        ("Cadastrar produto", _cadastrar_produto),
        ("Atualizar produto", _atualizar_produto),
        ("Remover produto", _remover_produto),
        ("Consultar estoque", _consultar_estoque),
        ("Repor estoque", _repor_estoque),
    ])


def _menu_cliente():
    _executar_menu("Cliente - Catálogo", [
        ("Listar produtos", _listar_produtos),
        ("Buscar produto por código", _buscar_por_codigo),
        ("Buscar produto por nome", _buscar_por_nome),
    ])


def main():
    while True:
        print("\n=== Loja Virtual ===")
        print("1 - Entrar como administrador")
        print("2 - Entrar como cliente")
        print("0 - Sair")

        escolha = _ler_inteiro("Opção: ")
        if escolha == 1:
            _menu_administrador()
        elif escolha == 2:
            _menu_cliente()
        elif escolha == 0:
            print("Até logo!")
            return
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
