# Contexto do projeto (para o Claude Code)

Loja virtual em Python, projeto do Grupo 2 da disciplina INF1040 – Programação Modular
(PUC-Rio, 2026.2, turma 3WB, prof. Flavio Bevilacqua). A especificação oficial é o
documento do T2 ("Projeto de aplicação - T2 - GRUPO 2"); em caso de dúvida, ele manda.

## Módulos (ver README para responsáveis e status)

- Main (`main.py`): único que usa input/print; menus e controle de acesso por perfil (RNF02).
- 1 CatalogoProdutos (`modulos/catalogo_produtos.py`) – Daniel – PRONTO, 34 testes.
- 2 GerenciadorClientes (`modulos/gerenciador_clientes.py`) – Pedro.
- 3 ProcessadorPedidos (`modulos/processador_pedidos.py`) – Brenno e Guilherme.
- 4 RelatoriosVendas (`modulos/relatorios_vendas.py`) – Matheus.

Dependências permitidas (sem ciclos): Main → todos; Clientes, Pedidos, Relatórios → Catálogo;
Pedidos → Clientes; Relatórios → Pedidos. Um módulo só chama as funções do outro que
estão no Diagrama de Funções de Acesso (ex.: Clientes usa só 1.2 e 1.7 do Catálogo).

## Regras obrigatórias da disciplina

- **Proibido criar classes.** Só funções. (Herdar de `unittest.TestCase` no testador é permitido.)
- Dados do módulo em lista de dicionários com `_` no nome (ex.: `_produtos`); `__all__`
  lista apenas as funções de acesso; auxiliares internas começam com `_`.
- Nomes das funções exatamente como no T2 (`CadastrarProduto`, `ObterCarrinho`, ...),
  com os mesmos parâmetros e retornos (bool / dict vazio / lista vazia / -1 / 0.0).
- Funções de consulta devolvem cópias (`dict(p)`), nunca a referência interna.
- Persistência: cada módulo lê/grava só o próprio JSON em `dados/`, grava a cada
  alteração e carrega ao ser importado; arquivo ausente → cria com `[]`.
- Docstring de cada função no formato da matéria (§12.4): `A) Descrição`,
  `B) Acoplamento` (parâmetros e retornos), `C) Condições de acoplamento` (AE e AS).

## Testes (TDD)

- Um testador por módulo em `testes/teste_<modulo>.py`, cobrindo todos os casos da
  seção 5 do T2, com `test_NN_...` e `print("x.y Cn - descrição")`; casos a mais
  como `Cn (extra)`. O Main tem `testes/teste_main.py` (casos M.x, input simulado,
  módulos reais em pasta temporária).
- Testes usam pasta temporária e nunca alteram os arquivos reais de `dados/`
  (modelo: `testes/teste_catalogo_produtos.py`).
- Rodar da raiz: `python -m unittest discover -s testes -p "teste_*.py" -v`
- Para testar antes da integração, usar `unittest.mock.patch` nas funções do outro módulo.

## Git

- Uma branch por módulo/tarefa; Pull Request para `main`; rodar todos os testes antes.
- Commits e PRs **sem** linha de coautoria do Claude (configurado em `.claude/settings.json`).
