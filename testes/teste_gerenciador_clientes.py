"""
Módulo testador do GerenciadorClientes (Módulo 2)
Responsável: Pedro Augusto

Implementa os casos de teste da seção 5.2 do documento do projeto (T2),
além dos testes das funções internas 2.1 e 2.2 do Diagrama de Funções de Acesso.

Organização (sem classes: cada caso de teste é uma função)
- Os casos de cada função (2.1 a 2.11) formam um grupo e rodam na ordem
  C1, C2, ... da lista GRUPOS.
- Antes de cada grupo, o cenário inicial é recriado em uma pasta
  temporária, para que os testes nunca mexam no dados/clientes.json real.
- A suíte é montada por testes/suite_funcoes.py com unittest.FunctionTestCase.
- As chamadas ao CatalogoProdutos (1.2 e 1.7) são simuladas via
  unittest.mock.patch.

Como executar (a partir da pasta raiz do projeto):
    python -m unittest testes.teste_gerenciador_clientes -v
  ou
    python testes/teste_gerenciador_clientes.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Permite rodar o arquivo diretamente (python testes/teste_gerenciador_clientes.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos import gerenciador_clientes as clientes   # noqa: E402
from testes.suite_funcoes import grupo, montar_suite, verifica   # noqa: E402

CENARIO_INICIAL = [
    {
        "cpf": "00000000001",
        "nome": "Administrador",
        "email": "admin@loja.com",
        "senha": "admin",
        "endereco": "Sede",
        "perfil": "admin",
        "carrinho": [],
    },
    {
        "cpf": "12345678901",
        "nome": "Maria",
        "email": "maria@test.com",
        "senha": "123",
        "endereco": "Rua A",
        "perfil": "cliente",
        "carrinho": [{"codigo": "P001", "quantidade": 2}],
    },
    {
        "cpf": "98765432100",
        "nome": "João",
        "email": "joao@test.com",
        "senha": "789",
        "endereco": "Rua C",
        "perfil": "cliente",
        "carrinho": [],
    },
]

PRODUTOS_MOCK = {
    "P001": {
        "codigo": "P001",
        "nome": "Camiseta Basica",
        "descricao": "Algodao",
        "categoria": "Roupas",
        "preco": 49.90,
        "estoque": 10,
    },
    "P002": {
        "codigo": "P002",
        "nome": "Caneca",
        "descricao": "Ceramica 300ml",
        "categoria": "Utilidades",
        "preco": 30.10,
        "estoque": 3,
    },
}


def _mock_buscar_produto(codigo):
    prod = PRODUTOS_MOCK.get(codigo)
    return dict(prod) if prod else {}


def _mock_consultar_estoque(codigo):
    prod = PRODUTOS_MOCK.get(codigo)
    return prod["estoque"] if prod else -1


def montar_cenario_inicial(pasta, lista_clientes=None):
    """Grava o cenário em <pasta>/clientes.json, redireciona o módulo
    e recarrega os dados."""
    caminho = os.path.join(pasta, "clientes.json")
    dados = CENARIO_INICIAL if lista_clientes is None else lista_clientes
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    clientes._CAMINHO_ARQUIVO = caminho
    clientes._carregar_clientes_do_arq()
    return caminho


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

# --------------------------------------------------------------------------
# Preparação e limpeza do cenário (rodam antes e depois de cada grupo)
# --------------------------------------------------------------------------

_ctx = {}   # caminho original, pasta temporária e arquivo do grupo atual


def _preparar(lista_clientes=None):
    _ctx["caminho_original"] = clientes._CAMINHO_ARQUIVO
    _ctx["pasta"] = tempfile.mkdtemp()
    _ctx["arquivo"] = montar_cenario_inicial(_ctx["pasta"], lista_clientes)


def preparar_cenario():
    """Recria o cenário inicial completo numa pasta temporária."""
    _preparar()


def preparar_cenario_so_admin():
    """2.3: começa apenas com o admin, para que Maria seja cadastrada em C1."""
    _preparar([CENARIO_INICIAL[0]])


def preparar_cenario_maria_sem_carrinho():
    """2.5: Maria começa com carrinho vazio, para C1 adicionar P001 (qtd 2)."""
    maria_vazia = dict(CENARIO_INICIAL[1], carrinho=[])
    _preparar([CENARIO_INICIAL[0], maria_vazia])


def limpar_cenario():
    """Devolve o caminho original ao módulo e apaga a pasta temporária."""
    clientes._CAMINHO_ARQUIVO = _ctx["caminho_original"]
    shutil.rmtree(_ctx["pasta"], ignore_errors=True)



# ==========================================================================
# 2.1 ValidarDados(c: dict) -> bool (interna)
# ==========================================================================


def caso_2_1_01_dados_validos():
    print("2.1 C1 - Validacao de dicionario com todos os campos validos")
    verifica.assertTrue(clientes.ValidarDados({
        "cpf": "12345678901",
        "nome": "Maria",
        "email": "maria@test.com",
        "senha": "123",
        "endereco": "Rua A",
    }))


def caso_2_1_02_dados_invalidos():
    print("2.1 C2 - Validacao falha para campo ausente, CPF invalido ou email sem @")
    verifica.assertFalse(clientes.ValidarDados("nao e dict"))
    verifica.assertFalse(clientes.ValidarDados({"cpf": "12345678901", "nome": "Maria"}))
    verifica.assertFalse(clientes.ValidarDados({
        "cpf": "12345",
        "nome": "Carlos",
        "email": "carlos@test.com",
        "senha": "321",
        "endereco": "Rua D",
    }))
    verifica.assertFalse(clientes.ValidarDados({
        "cpf": "12345678901",
        "nome": "Maria",
        "email": "mariatest.com",
        "senha": "123",
        "endereco": "Rua A",
    }))


# ==========================================================================
# 2.2 VerificarExistenciaCpf(cpf: str) -> bool (interna)
# ==========================================================================


def caso_2_2_01_cpf_existente():
    print("2.2 C1 - Verifica CPF ja cadastrado")
    verifica.assertTrue(clientes.VerificarExistenciaCpf("12345678901"))


def caso_2_2_02_cpf_inexistente():
    print("2.2 C2 - Verifica CPF nao cadastrado")
    verifica.assertFalse(clientes.VerificarExistenciaCpf("00000000000"))


# ==========================================================================
# 2.3 CadastrarCliente(c: dict) -> bool
# ==========================================================================


def caso_2_3_01_cadastro_valido():
    print("2.3 C1 - Cadastro com dados validos e CPF/e-mail ainda nao cadastrados")
    retorno = clientes.CadastrarCliente({
        "cpf": "12345678901",
        "nome": "Maria",
        "email": "maria@test.com",
        "senha": "123",
        "endereco": "Rua A",
    })
    verifica.assertTrue(retorno)


def caso_2_3_02_cpf_ja_existente():
    print("2.3 C2 - Cadastro com CPF ja existente")
    retorno = clientes.CadastrarCliente({
        "cpf": "12345678901",
        "nome": "Mariana",
        "email": "mariana@test.com",
        "senha": "456",
        "endereco": "Rua B",
    })
    verifica.assertFalse(retorno)


def caso_2_3_03_email_ja_existente():
    print("2.3 C3 - Cadastro com e-mail ja existente")
    retorno = clientes.CadastrarCliente({
        "cpf": "98765432100",
        "nome": "João",
        "email": "maria@test.com",
        "senha": "789",
        "endereco": "Rua C",
    })
    verifica.assertFalse(retorno)


def caso_2_3_04_dados_invalidos():
    print("2.3 C4 - Cadastro com dados invalidos (CPF incompleto ou campo ausente)")
    verifica.assertFalse(clientes.CadastrarCliente({
        "cpf": "12345",
        "nome": "Carlos",
        "email": "carlos@test.com",
        "senha": "321",
        "endereco": "Rua D",
    }))
    verifica.assertFalse(clientes.CadastrarCliente({
        "cpf": "55544433322",
        "nome": "Carlos",
        "senha": "321",
        "endereco": "Rua D",
    }))


# ==========================================================================
# 2.4 AutenticarCliente(email: str, senha: str) -> dict
# ==========================================================================


def caso_2_4_01_credenciais_corretas():
    print("2.4 C1 - Autenticacao com credenciais corretas (sem senha, com perfil)")
    resultado = clientes.AutenticarCliente("maria@test.com", "123")
    verifica.assertEqual(resultado, {
        "cpf": "12345678901",
        "nome": "Maria",
        "email": "maria@test.com",
        "perfil": "cliente",
        "endereco": "Rua A",
        "carrinho": [{"codigo": "P001", "quantidade": 2}],
    })
    verifica.assertNotIn("senha", resultado)

    admin = clientes.AutenticarCliente("admin@loja.com", "admin")
    verifica.assertEqual(admin["perfil"], "admin")
    verifica.assertNotIn("senha", admin)


def caso_2_4_02_email_inexistente():
    print("2.4 C2 - Autenticacao com e-mail inexistente")
    verifica.assertEqual(clientes.AutenticarCliente("inexistente@test.com", "123"), {})


def caso_2_4_03_senha_incorreta():
    print("2.4 C3 - Autenticacao com senha incorreta")
    verifica.assertEqual(clientes.AutenticarCliente("maria@test.com", "senhaerrada"), {})


# ==========================================================================
# 2.5 AdicionarItemCarrinho(cpf: str, codigo: str, qtd: int) -> bool
# ==========================================================================


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_5_01_adicao_valida(_mock_bus, _mock_est):
    print("2.5 C1 - Adicao valida de produto com estoque suficiente")
    verifica.assertTrue(clientes.AdicionarItemCarrinho("12345678901", "P001", 2))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_5_02_cliente_inexistente(_mock_bus, _mock_est):
    print("2.5 C2 - Adicao com cliente inexistente")
    verifica.assertFalse(clientes.AdicionarItemCarrinho("00000000000", "P001", 1))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_5_03_produto_inexistente(_mock_bus, _mock_est):
    print("2.5 C3 - Adicao com produto inexistente no catalogo")
    verifica.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P999", 1))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_5_04_quantidade_invalida(_mock_bus, _mock_est):
    print("2.5 C4 - Adicao com quantidade menor ou igual a zero")
    verifica.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", 0))
    verifica.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", -1))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_5_05_estoque_insuficiente(_mock_bus, _mock_est):
    print("2.5 C5 - Adicao com estoque insuficiente para a quantidade total")
    verifica.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", 1000))


# ==========================================================================
# 2.6 AlterarQuantidadeItem(cpf: str, codigo: str, qtd: int) -> bool
# ==========================================================================


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
def caso_2_6_01_alteracao_valida(_mock_est):
    print("2.6 C1 - Alteracao valida da quantidade de um item no carrinho")
    verifica.assertTrue(clientes.AlterarQuantidadeItem("12345678901", "P001", 4))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
def caso_2_6_02_item_fora_do_carrinho(_mock_est):
    print("2.6 C2 - Alteracao de item que nao esta no carrinho")
    verifica.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P999", 2))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
def caso_2_6_03_quantidade_menor_ou_igual_a_zero(_mock_est):
    print("2.6 C3 - Alteracao com quantidade menor ou igual a zero")
    verifica.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", 0))
    verifica.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", -2))


@patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
def caso_2_6_04_estoque_insuficiente(_mock_est):
    print("2.6 C4 - Alteracao com estoque insuficiente para a nova quantidade")
    verifica.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", 9999))


# ==========================================================================
# 2.7 RemoverItemCarrinho(cpf: str, codigo: str) -> bool
# ==========================================================================


def caso_2_7_01_remocao_item_existente():
    print("2.7 C1 - Remocao de um item existente no carrinho")
    verifica.assertTrue(clientes.RemoverItemCarrinho("12345678901", "P001"))


def caso_2_7_02_remocao_item_inexistente():
    print("2.7 C2 - Remocao de um item que nao esta no carrinho")
    verifica.assertFalse(clientes.RemoverItemCarrinho("12345678901", "P999"))


def caso_2_7_03_remocao_cliente_inexistente():
    print("2.7 C3 - Remocao com cliente inexistente")
    verifica.assertFalse(clientes.RemoverItemCarrinho("00000000000", "P001"))


# ==========================================================================
# 2.8 ObterCarrinho(cpf: str) -> list
# ==========================================================================


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_8_01_carrinho_com_itens(_mock_bus):
    print("2.8 C1 - Obtencao de carrinho com itens adicionados")
    verifica.assertEqual(clientes.ObterCarrinho("12345678901"), [{
        "codigo": "P001",
        "nome": "Camiseta Basica",
        "preco": 49.90,
        "quantidade": 2,
    }])


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_8_02_carrinho_vazio(_mock_bus):
    print("2.8 C2 - Obtencao de carrinho vazio")
    verifica.assertEqual(clientes.ObterCarrinho("98765432100"), [])


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_8_03_cliente_inexistente(_mock_bus):
    print("2.8 C3 - Obtencao de carrinho para cliente inexistente")
    verifica.assertEqual(clientes.ObterCarrinho("00000000000"), [])


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_8_04_produto_removido_do_catalogo(_mock_bus):
    print("2.8 C4 (extra) - Item de produto removido do catalogo sai do carrinho")
    montar_cenario_inicial(_ctx["pasta"], [{
        "cpf": "11122233344", "nome": "Ana", "email": "ana@test.com",
        "senha": "1", "endereco": "Rua E", "perfil": "cliente",
        "carrinho": [{"codigo": "P001", "quantidade": 1},
                     {"codigo": "P999", "quantidade": 2}],
    }])
    verifica.assertEqual([i["codigo"] for i in clientes.ObterCarrinho("11122233344")],
                     ["P001"])
    # A limpeza vale na memoria; o arquivo so e gravado ao encerrar (pelo Main).
    verifica.assertEqual(ler_arquivo(_ctx["arquivo"])[0]["carrinho"],
                     [{"codigo": "P001", "quantidade": 1},
                      {"codigo": "P999", "quantidade": 2}])


# ==========================================================================
# 2.9 CalcularSubtotal(cpf: str) -> float
# ==========================================================================


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_9_01_subtotal_com_itens(_mock_bus):
    print("2.9 C1 - Calculo de subtotal com itens no carrinho")
    verifica.assertEqual(clientes.CalcularSubtotal("12345678901"), 99.80)


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_9_02_subtotal_carrinho_vazio(_mock_bus):
    print("2.9 C2 - Calculo de subtotal com carrinho vazio")
    verifica.assertEqual(clientes.CalcularSubtotal("98765432100"), 0.0)


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_9_03_subtotal_cliente_inexistente(_mock_bus):
    print("2.9 C3 - Calculo para cliente inexistente")
    verifica.assertEqual(clientes.CalcularSubtotal("00000000000"), 0.0)


# ==========================================================================
# 2.10 EsvaziarCarrinho(cpf: str) -> bool
# ==========================================================================


@patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
def caso_2_10_01_esvaziar_carrinho_existente(_mock_bus):
    print("2.10 C1 - Esvaziamento de carrinho existente (apos pagamento)")
    verifica.assertTrue(clientes.EsvaziarCarrinho("12345678901"))
    verifica.assertEqual(clientes.ObterCarrinho("12345678901"), [])


def caso_2_10_02_esvaziar_cliente_inexistente():
    print("2.10 C2 - Esvaziamento para cliente inexistente")
    verifica.assertFalse(clientes.EsvaziarCarrinho("00000000000"))


# ==========================================================================
# 2.11 SalvarClientesNoArq() -> bool (interna)
# ==========================================================================


def caso_2_11_01_gravacao_bem_sucedida():
    print("2.11 C1 - Gravacao bem-sucedida no arquivo clientes.json")
    clientes.CadastrarCliente({
        "cpf": "44433322211",
        "nome": "Ana",
        "email": "ana@test.com",
        "senha": "111",
        "endereco": "Rua D",
    })
    verifica.assertTrue(clientes.SalvarClientesNoArq())
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 4)


def caso_2_11_02_falha_de_gravacao():
    print("2.11 C2 - Falha de gravacao caso ocorra erro no sistema de arquivos")
    os.remove(_ctx["arquivo"])
    os.mkdir(_ctx["arquivo"])
    verifica.assertFalse(clientes.SalvarClientesNoArq())

# ==========================================================================
# Ordem de execução: um grupo por função, casos na ordem C1, C2, ...
# ==========================================================================

GRUPOS = [
    # 2.1 ValidarDados(c: dict) -> bool (interna)
    grupo([
        caso_2_1_01_dados_validos,
        caso_2_1_02_dados_invalidos,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.2 VerificarExistenciaCpf(cpf: str) -> bool (interna)
    grupo([
        caso_2_2_01_cpf_existente,
        caso_2_2_02_cpf_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.3 CadastrarCliente(c: dict) -> bool
    grupo([
        caso_2_3_01_cadastro_valido,
        caso_2_3_02_cpf_ja_existente,
        caso_2_3_03_email_ja_existente,
        caso_2_3_04_dados_invalidos,
    ], antes=preparar_cenario_so_admin, depois=limpar_cenario),
    # 2.4 AutenticarCliente(email: str, senha: str) -> dict
    grupo([
        caso_2_4_01_credenciais_corretas,
        caso_2_4_02_email_inexistente,
        caso_2_4_03_senha_incorreta,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.5 AdicionarItemCarrinho(cpf: str, codigo: str, qtd: int) -> bool
    grupo([
        caso_2_5_01_adicao_valida,
        caso_2_5_02_cliente_inexistente,
        caso_2_5_03_produto_inexistente,
        caso_2_5_04_quantidade_invalida,
        caso_2_5_05_estoque_insuficiente,
    ], antes=preparar_cenario_maria_sem_carrinho, depois=limpar_cenario),
    # 2.6 AlterarQuantidadeItem(cpf: str, codigo: str, qtd: int) -> bool
    grupo([
        caso_2_6_01_alteracao_valida,
        caso_2_6_02_item_fora_do_carrinho,
        caso_2_6_03_quantidade_menor_ou_igual_a_zero,
        caso_2_6_04_estoque_insuficiente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.7 RemoverItemCarrinho(cpf: str, codigo: str) -> bool
    grupo([
        caso_2_7_01_remocao_item_existente,
        caso_2_7_02_remocao_item_inexistente,
        caso_2_7_03_remocao_cliente_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.8 ObterCarrinho(cpf: str) -> list
    grupo([
        caso_2_8_01_carrinho_com_itens,
        caso_2_8_02_carrinho_vazio,
        caso_2_8_03_cliente_inexistente,
        caso_2_8_04_produto_removido_do_catalogo,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.9 CalcularSubtotal(cpf: str) -> float
    grupo([
        caso_2_9_01_subtotal_com_itens,
        caso_2_9_02_subtotal_carrinho_vazio,
        caso_2_9_03_subtotal_cliente_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.10 EsvaziarCarrinho(cpf: str) -> bool
    grupo([
        caso_2_10_01_esvaziar_carrinho_existente,
        caso_2_10_02_esvaziar_cliente_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 2.11 SalvarClientesNoArq() -> bool (interna)
    grupo([
        caso_2_11_01_gravacao_bem_sucedida,
        caso_2_11_02_falha_de_gravacao,
    ], antes=preparar_cenario, depois=limpar_cenario),
]


def load_tests(loader, testes_padrao, padrao):
    """Chamada pelo unittest (discover ou execução direta) para montar a suíte."""
    return montar_suite(GRUPOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
