# Loja Virtual — Projeto de Programação Modular (INF1040 · 2026.2 · 3WB)

Aplicação de loja virtual em Python que cobre o ciclo completo de uma venda online:
catálogo → carrinho → pedido → pagamento simulado → relatórios.

**Grupo 2:** Pedro Augusto Beserra da Silva · Guilherme Meira Diniz · Matheus Marques ·
Brenno Távora Barbosa · Daniel Santana Souza

## Módulos e responsáveis

| Nº | Módulo | Arquivo | Arquivo de dados | Responsável | Status |
|---|---|---|---|---|---|
| — | Main | `main.py` | — | grupo | 🟡 menu do catálogo (perfis admin/cliente) |
| 1 | CatalogoProdutos | `modulos/catalogo_produtos.py` | `dados/produtos.json` | Daniel | ✅ pronto (34 testes) |
| 2 | GerenciadorClientes | `modulos/gerenciador_clientes.py` | `dados/clientes.json` | Pedro | a fazer |
| 3 | ProcessadorPedidos | `modulos/processador_pedidos.py` | `dados/pedidos.json` | Brenno e Guilherme | a fazer |
| 4 | RelatoriosVendas | `modulos/relatorios_vendas.py` | — | Matheus | a fazer |

Dependências (sem ciclos): Main → todos · Clientes, Pedidos e Relatórios → Catálogo ·
Pedidos → Clientes · Relatórios → Pedidos.

## Estrutura

```
loja/
├── main.py                       # ponto de entrada (único módulo que usa input/print)
├── modulos/                      # módulos de negócio
│   ├── __init__.py
│   └── catalogo_produtos.py
├── testes/                       # um módulo testador por módulo
│   ├── __init__.py
│   └── teste_catalogo_produtos.py
└── dados/                        # arquivos JSON (cada um só é lido/gravado pelo seu módulo)
    └── produtos.json
```

## Como rodar a aplicação

```bash
python main.py
```

## Como rodar os testes

Sempre a partir da pasta raiz do repositório:

```bash
python -m unittest discover -s testes -p "teste_*.py" -v   # todos os módulos
python -m unittest testes.teste_catalogo_produtos -v        # só um módulo
```

## Regras do projeto (resumo do T2 e das orientações da disciplina)

- **Sem classes próprias** — só funções. (A `unittest.TestCase` dos testadores é permitida.)
- **Encapsulamento (RNF03):** dados do módulo em variáveis com `_` (ex.: `_produtos`);
  `__all__` lista só as funções de acesso; funções internas começam com `_` ou estão
  marcadas como internas no diagrama.
- **Comunicação só pelas funções de acesso** do Diagrama de Funções de Acesso.
  Nunca acessar `_variaveis` de outro módulo.
- **Persistência (RNF01/RF11):** cada módulo grava o seu JSON a cada alteração e o
  carrega ao ser importado; se o arquivo não existir, cria vazio (`[]`).
- **Nomes das funções** iguais aos do documento (`CadastrarProduto`, `ObterCarrinho`, ...).
- **Testes:** cada caso da seção 5 do T2 vira um `test_NN_...` com
  `print("x.y Cn - descrição")`. Testes nunca alteram os arquivos reais de `dados/`
  (usar pasta temporária, como em `teste_catalogo_produtos.py`).
- **Importação entre módulos:** `from modulos import catalogo_produtos as catalogo`.
- **Mock para desenvolver antes da integração:** use `unittest.mock.patch`, ex.:
  `patch("modulos.catalogo_produtos.ConsultarEstoque", return_value=10)`.

## Fluxo de trabalho no Git

1. Atualize sua cópia: `git checkout main && git pull`
2. Crie uma branch para o seu módulo: `git checkout -b modulo-clientes`
3. Faça commits pequenos (ciclo TDD: teste falha → implementa → passa → refatora).
4. Antes de enviar, rode **todos** os testes (comando acima) e confira que passam.
5. `git push -u origin modulo-clientes` e abra um Pull Request para `main`.
6. Outro integrante revisa e faz o merge.

Não commitar `__pycache__/`, `.venv/` nem arquivos de relatório exportados (já no `.gitignore`).
