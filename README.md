# Loja Virtual — Projeto de Programação Modular (INF1040 · 2026.2 · 3WB)

Aplicação de loja virtual em Python que cobre o ciclo completo de uma venda online:
catálogo → carrinho → pedido → pagamento simulado → relatórios.

**Grupo 2:** Pedro Augusto Beserra da Silva · Guilherme Meira Diniz · Matheus Marques ·
Brenno Távora Barbosa · Daniel Santana Souza

## Módulos e responsáveis

| Nº | Módulo | Arquivo | Arquivo de dados | Responsável | Status |
|---|---|---|---|---|---|
| — | Main | `main.py` | — | grupo | ✅ menu, catálogo, carrinho, compra e relatórios (26 testes) |
| 1 | CatalogoProdutos | `modulos/catalogo_produtos.py` | `dados/produtos.json` | Daniel | ✅ pronto (36 testes) |
| 2 | GerenciadorClientes | `modulos/gerenciador_clientes.py` | `dados/clientes.json` | Pedro | ✅ pronto (34 testes) |
| 3 | ProcessadorPedidos | `modulos/processador_pedidos.py` | `dados/pedidos.json` | Brenno e Guilherme | ✅ pronto (36 testes) |
| 4 | RelatoriosVendas | `modulos/relatorios_vendas.py` | — | Matheus | ✅ pronto (37 testes) |

Dependências (sem ciclos): Main → todos · Clientes, Pedidos e Relatórios → Catálogo ·
Pedidos → Clientes · Relatórios → Pedidos.

## Estrutura

```
projeto-modular-ecommerce/
├── main.py                           # ponto de entrada (único módulo que usa input/print)
├── modulos/                          # módulos de negócio
│   ├── __init__.py
│   ├── catalogo_produtos.py          # 1 · CatalogoProdutos
│   ├── gerenciador_clientes.py       # 2 · GerenciadorClientes
│   ├── processador_pedidos.py        # 3 · ProcessadorPedidos
│   └── relatorios_vendas.py          # 4 · RelatoriosVendas
├── testes/                           # um módulo testador por módulo
│   ├── __init__.py
│   ├── teste_catalogo_produtos.py
│   ├── teste_gerenciador_clientes.py
│   ├── teste_main.py                 # integração: menus, perfis e fluxos
│   ├── teste_processador_pedidos.py
│   └── teste_relatorios_vendas.py
└── dados/                            # arquivos JSON (cada um só é lido/gravado pelo seu módulo)
    ├── produtos.json
    ├── clientes.json                 # inclui o administrador pré-cadastrado (RNF02)
    └── pedidos.json
```

Relatórios exportados (4.6) são gravados na pasta de onde a aplicação é executada.

## Pré-requisitos

Python 3.8 ou mais recente. O projeto usa só a biblioteca padrão (`json`, `os`, `math`,
`copy`, `datetime`, `unittest`): não há nada para instalar.

## Como rodar a aplicação

```bash
python main.py
```

O administrador já vem pré-cadastrado em `dados/clientes.json` (RNF02):
e-mail `admin@loja.com`, senha `admin`. Clientes se cadastram pela opção 2 do menu inicial.

| Perfil | Opções do menu |
|---|---|
| Cliente | Consultar catálogo · Meu carrinho · Compras e pedidos (gerar, pagar, consultar, cancelar) |
| Administrador | Catálogo e estoque (consulta + cadastrar, atualizar, remover, repor) · Relatórios gerenciais |

## Estrutura dos dados

Cada módulo guarda uma lista de dicionários e grava no seu próprio JSON.

```python
# Produto (produtos.json) — identificado pelo código
{"codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
 "categoria": "Roupas", "preco": 49.90, "estoque": 10}

# Cliente (clientes.json) — identificado pelo CPF, com o carrinho embutido
{"cpf": "12345678901", "nome": "Maria", "email": "maria@test.com", "senha": "123",
 "endereco": "Rua A", "perfil": "cliente",
 "carrinho": [{"codigo": "P001", "quantidade": 2}]}

# Pedido (pedidos.json) — identificado pelo número sequencial
{"numero": 1, "cpf": "12345678901", "data": "2026-09-10",
 "itens": [{"codigo": "P001", "nome": "Camiseta Basica", "preco": 49.90, "quantidade": 2}],
 "subtotal": 99.80, "frete": 10.00, "desconto": 0.00, "total": 109.80,
 "status": "Pago"}          # "Aguardando pagamento" | "Pago" | "Cancelado"
```

## Regras de negócio

- **Total do pedido:** subtotal + frete (fixo, 10.00) − desconto (0.00).
- **Pagamento simulado (RF07):** Pix é sempre aprovado; cartão é aprovado se o total for
  até 500.00; boleto é aprovado se o total for a partir de 50.00.
- **Aprovado (RF08):** baixa o estoque, esvazia o carrinho e o pedido vira "Pago".
  **Recusado:** o pedido vira "Cancelado", o estoque não muda e o carrinho é mantido.
- **Sem venda parcial (RI02):** se algum item não tiver estoque, o pedido inteiro é recusado.
- **Cancelamento (RF09):** vale para pedidos "Aguardando pagamento" ou "Pago"; se já estava
  pago, os itens voltam ao estoque. O cliente só cancela os próprios pedidos.
- **Relatórios (RF10):** consideram só pedidos "Pago"; datas no formato AAAA-MM-DD,
  período inclusivo nas duas pontas.

## Exemplo de uso das funções de acesso

Os módulos podem ser usados sem o menu, por exemplo num terminal Python aberto na raiz
(lembrando que eles gravam nos arquivos reais de `dados/`):

```python
from modulos import catalogo_produtos as catalogo
from modulos import gerenciador_clientes as clientes
from modulos import processador_pedidos as pedidos
from modulos import relatorios_vendas as relatorios

catalogo.CadastrarProduto({"codigo": "P001", "nome": "Camiseta Basica",
                           "descricao": "Algodao", "categoria": "Roupas",
                           "preco": 49.90, "estoque": 10})           # True
clientes.CadastrarCliente({"cpf": "12345678901", "nome": "Maria",
                           "email": "maria@test.com", "senha": "123",
                           "endereco": "Rua A"})                     # True
clientes.AdicionarItemCarrinho("12345678901", "P001", 2)            # True
pedido = pedidos.CriarPedido("12345678901")    # {"numero": 1, ..., "total": 109.8}
pedidos.SimularPagamento(pedido, "pix")        # True: estoque 10 -> 8, carrinho vazio
relatorios.ListarMaisVendidos(1)   # [{"codigo": "P001", "nome": "Camiseta Basica", "quantidade": 2}]
```

Toda função de acesso devolve um código de retorno em vez de lançar exceção:
`True`/`False`, dicionário ou lista vazios, `-1` (estoque de produto inexistente) ou `0.0`.

## Como rodar os testes

Sempre a partir da pasta raiz do repositório:

```bash
python -m unittest discover -s testes -p "teste_*.py" -v      # todos os módulos (169 testes)
python -m unittest testes.teste_catalogo_produtos -v           # só catálogo (36 testes)
python -m unittest testes.teste_gerenciador_clientes -v        # só clientes (34 testes)
python -m unittest testes.teste_processador_pedidos -v         # só pedidos (36 testes)
python -m unittest testes.teste_relatorios_vendas -v           # só relatórios (37 testes)
python -m unittest testes.teste_main -v                        # só Main (26 testes)
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
- **Docstrings** no formato da matéria (§12.4): `A) Descrição`, `B) Acoplamento`
  (parâmetros e retornos) e `C) Condições de acoplamento` (AE e AS).
- **Testes:** cada caso da seção 5 do T2 vira um `test_NN_...` com
  `print("x.y Cn - descrição")`; casos a mais aparecem como `Cn (extra)`. Testes nunca alteram os arquivos reais de `dados/`
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
