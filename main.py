"""
Main · Ponto de entrada da Loja Virtual
Responsável: grupo

Objetivo
    Único módulo que conversa com o usuário (input/print). Apresenta os menus,
    lê e converte as entradas e chama SOMENTE as funções de acesso dos módulos.

Controle de acesso por perfil (RNF02)
- Autenticação via 2.4 AutenticarCliente(email, senha) retorna o perfil.
- Administrador ("admin"): gerencia o catálogo e o estoque e gera os
      relatórios gerenciais (fluxo_relatorios).
- Cliente ("cliente"): consulta o catálogo, gerencia o carrinho, finaliza
      compras e consulta/cancela os próprios pedidos (fluxo_compra).

Relações (Diagrama de Arquitetura)
    Cliente de: CatalogoProdutos (1.1..1.6, 1.9, 1.10),
                GerenciadorClientes (2.3..2.9, 2.11),
                ProcessadorPedidos (3.1, 3.3, 3.5, 3.8, 3.9),
                RelatoriosVendas (4.1..4.6)

Persistência (só entre uma execução e outra)
- Ao iniciar, cada módulo lê o seu arquivo uma única vez (na importação).
- Durante a execução os dados ficam só na memória dos módulos.
- Ao encerrar, menu() grava os três arquivos de uma vez (1.10, 2.11, 3.9),
  inclusive se o programa for interrompido com Ctrl+C.
"""

from modulos import catalogo_produtos as catalogo
from modulos import gerenciador_clientes as clientes
from modulos import processador_pedidos as pedidos
from modulos import relatorios_vendas as relatorios

_FORMAS_PAGAMENTO = ("pix", "cartao", "boleto")


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


def _informar_estoque(cpf, codigo):
    """RF05: depois de uma recusa no carrinho, informa a quantidade disponível
    do produto (1.2) e quanto dele já está no carrinho (2.8)."""
    produto = catalogo.BuscarProduto(codigo)
    if not produto:
        print("  Produto não encontrado no catálogo.")
        return
    no_carrinho = 0
    for item in clientes.ObterCarrinho(cpf):
        if item["codigo"] == produto["codigo"]:
            no_carrinho = item["quantidade"]
    print(f"  Quantidade disponível de {produto['nome']}: {produto['estoque']} "
          f"(no seu carrinho: {no_carrinho}).")


def _mostrar_pedido(p):
    print(f"  Pedido nº {p['numero']} - {p['data']} - {p['status']}")
    for item in p["itens"]:
        print(f"      [{item['codigo']}] {item['nome']} - "
              f"{item['quantidade']}x R$ {item['preco']:.2f}")
    print(f"      Subtotal R$ {p['subtotal']:.2f} + frete R$ {p['frete']:.2f} "
          f"- desconto R$ {p['desconto']:.2f} = total R$ {p['total']:.2f}")


def _ler_forma_pagamento():
    """Lê a forma de pagamento; devolve None se o usuário desistir (Enter)."""
    while True:
        forma = _ler_texto("Forma de pagamento (pix, cartao, boleto; "
                           "Enter para pagar depois): ").lower()
        if forma == "":
            return None
        if forma == "cartão":
            forma = "cartao"
        if forma in _FORMAS_PAGAMENTO:
            return forma
        print("Forma de pagamento inválida.")


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
        if clientes.AdicionarItemCarrinho(cpf, codigo, qtd):
            print("Item adicionado ao carrinho.")
            return
        print("Não foi possível adicionar (produto inexistente, quantidade inválida ou estoque insuficiente).")
        _informar_estoque(cpf, codigo)

    def _alterar_qtd():
        codigo = _ler_texto("Código do produto: ")
        qtd = _ler_inteiro("Nova quantidade: ")
        if clientes.AlterarQuantidadeItem(cpf, codigo, qtd):
            print("Quantidade atualizada.")
            return
        print("Não foi possível alterar (item fora do carrinho, quantidade <= 0 ou estoque insuficiente).")
        _informar_estoque(cpf, codigo)

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


def fluxo_compra(cpf):
    """Finaliza a compra (3.1 e 3.3) e permite consultar e cancelar os pedidos
    do cliente (3.8 e 3.5). Só pedidos do próprio cliente podem ser pagos
    ou cancelados."""

    def _pedidos_do_cliente(status=None):
        lista = pedidos.ListarPedidosCliente(cpf)
        if status is None:
            return lista
        return [p for p in lista if p["status"] == status]

    def _pagar(pedido):
        forma = _ler_forma_pagamento()
        if forma is None:
            print(f"Pedido nº {pedido['numero']} continua aguardando pagamento.")
            return
        if pedidos.SimularPagamento(pedido, forma):
            print(f"Pagamento aprovado! Pedido nº {pedido['numero']} pago.")
            return
        atual = [p for p in _pedidos_do_cliente() if p["numero"] == pedido["numero"]]
        if atual and atual[0]["status"] == "Cancelado":
            print(f"Pagamento recusado ({forma}). Pedido nº {pedido['numero']} "
                  "cancelado; o carrinho foi mantido para uma nova tentativa.")
        else:
            print("Não foi possível processar o pagamento.")

    def _escolher_pedido(candidatos, acao):
        if not candidatos:
            print(f"  Nenhum pedido disponível para {acao}.")
            return None
        for p in candidatos:
            _mostrar_pedido(p)
        num = _ler_inteiro(f"Número do pedido para {acao}: ")
        for p in candidatos:
            if p["numero"] == num:
                return p
        print("Pedido não encontrado entre os seus pedidos.")
        return None

    def _finalizar():
        pendentes = _pedidos_do_cliente("Aguardando pagamento")
        if pendentes:
            print(f"Você já tem o pedido nº {pendentes[0]['numero']} aguardando "
                  "pagamento. Pague ou cancele esse pedido antes de gerar outro.")
            return
        _mostrar_carrinho(cpf)
        pedido = pedidos.CriarPedido(cpf)
        if not pedido:
            print("Não foi possível gerar o pedido (carrinho vazio ou estoque insuficiente).")
            for item in clientes.ObterCarrinho(cpf):
                _informar_estoque(cpf, item["codigo"])
            return
        print("Pedido gerado:")
        _mostrar_pedido(pedido)
        _pagar(pedido)

    def _pagar_pendente():
        pedido = _escolher_pedido(_pedidos_do_cliente("Aguardando pagamento"), "pagar")
        if pedido:
            _pagar(pedido)

    def _meus_pedidos():
        lista = _pedidos_do_cliente()
        if not lista:
            print("  Você ainda não tem pedidos.")
        for p in lista:
            _mostrar_pedido(p)

    def _cancelar():
        cancelaveis = [p for p in _pedidos_do_cliente() if p["status"] != "Cancelado"]
        pedido = _escolher_pedido(cancelaveis, "cancelar")
        if pedido:
            _resultado(pedidos.CancelarPedido(pedido["numero"]),
                       f"Pedido nº {pedido['numero']} cancelado.",
                       "Não foi possível cancelar o pedido.")

    _executar_menu("Compras e Pedidos", [
        ("Finalizar compra (gerar pedido e pagar)", _finalizar),
        ("Pagar pedido pendente", _pagar_pendente),
        ("Meus pedidos", _meus_pedidos),
        ("Cancelar pedido", _cancelar),
    ])


def fluxo_relatorios():
    """Disponível só para o administrador: gera os relatórios (4.1 a 4.5)
    e oferece a exportação para arquivo (4.6)."""

    def _oferecer_exportacao(dados):
        if not dados:
            return
        if _ler_texto("Exportar para arquivo? (s/n): ").lower() != "s":
            return
        arq = _ler_texto("Nome do arquivo (ex.: relatorio.txt): ")
        _resultado(relatorios.ExportarRelatorio(dados, arq),
                   f"Relatório exportado para {arq}.",
                   "Não foi possível exportar (nome inválido ou erro de escrita).")

    def _por_periodo(titulo, funcao):
        inicio = _ler_texto("Data inicial (AAAA-MM-DD): ")
        fim = _ler_texto("Data final (AAAA-MM-DD): ")
        valor = funcao(inicio, fim)
        print(f"  {titulo} de {inicio} a {fim}: R$ {valor:.2f}")
        if valor == 0.0:
            print("  (sem pedidos pagos no período, ou datas inválidas)")
        _oferecer_exportacao([{"relatorio": titulo, "inicio": inicio,
                               "fim": fim, "valor": valor}])

    def _mais_vendidos():
        ranking = relatorios.ListarMaisVendidos(_ler_inteiro("Quantos produtos (n)? "))
        if not ranking:
            print("  Nenhuma venda encontrada (ou n inválido).")
        for pos, item in enumerate(ranking, start=1):
            print(f"  {pos}º [{item['codigo']}] {item['nome']} - {item['quantidade']} un.")
        _oferecer_exportacao(ranking)

    def _vendas_por_cliente():
        vendas = relatorios.VendasPorCliente(_ler_texto("CPF do cliente: "))
        if not vendas:
            print("  Nenhuma compra paga para esse CPF.")
        for v in vendas:
            print(f"  Pedido nº {v['numero']} - {v['data']} - R$ {v['total']:.2f}")
        _oferecer_exportacao(vendas)

    def _estoque_baixo():
        produtos = relatorios.ListarEstoqueBaixo(_ler_inteiro("Limite de estoque: "))
        _mostrar_lista(produtos)
        _oferecer_exportacao(produtos)

    _executar_menu("Relatórios Gerenciais", [
        ("Faturamento por período",
         lambda: _por_periodo("Faturamento", relatorios.CalcularFaturamento)),
        ("Ticket médio por período",
         lambda: _por_periodo("Ticket médio", relatorios.CalcularTicketMedio)),
        ("Produtos mais vendidos", _mais_vendidos),
        ("Vendas por cliente", _vendas_por_cliente),
        ("Produtos com estoque baixo", _estoque_baixo),
    ])


def _sessao_administrador():
    _executar_menu("Menu Administrador", [
        ("Catálogo e Estoque", lambda: fluxo_catalogo("admin")),
        ("Relatórios Gerenciais", fluxo_relatorios),
    ])


def _sessao_cliente(usuario):
    cpf = usuario["cpf"]
    _executar_menu(f"Menu Cliente ({usuario['nome']})", [
        ("Consultar Catálogo", lambda: fluxo_catalogo("cliente")),
        ("Meu Carrinho", lambda: fluxo_carrinho(cpf)),
        ("Compras e Pedidos", lambda: fluxo_compra(cpf)),
    ])


def _gravar_dados():
    """
    A) Descrição: grava produtos, clientes (com carrinhos) e pedidos nos
       arquivos, uma única vez, ao encerrar o programa.
    B) Acoplamento:
        Retorno: True -> os três arquivos gravados | False -> algum falhou
    C) Condições de acoplamento:
        AE: o programa está sendo encerrado.
        AS: se True, os arquivos refletem tudo o que foi feito na execução.
    """
    resultados = [
        ("produtos.json", catalogo.SalvarCatalogoNoArq()),
        ("clientes.json", clientes.SalvarClientesNoArq()),
        ("pedidos.json", pedidos.SalvarPedidosNoArq()),
    ]
    falhas = [nome for nome, gravou in resultados if not gravou]
    if falhas:
        print("Atenção: não foi possível gravar " + ", ".join(falhas) + ".")
        return False
    print("Dados gravados.")
    return True


def menu():
    """
    A) Descrição: exibe o menu inicial, conduz login ou cadastro e, após a
       autenticação, as opções do perfil. Ao sair (opção 0 ou Ctrl+C), grava
       todos os dados nos arquivos.
    B) Acoplamento: sem parâmetros; sem retorno.
    C) Condições de acoplamento:
        AE: os módulos já carregaram seus arquivos na importação.
        AS: os arquivos foram gravados uma vez, no encerramento.
    """
    try:
        _menu_inicial()
    finally:
        _gravar_dados()


def _menu_inicial():
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
    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma encerrado.")