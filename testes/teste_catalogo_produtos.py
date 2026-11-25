"""
Módulo testador do CatalogoProdutos (Módulo 1)
Responsável: Daniel Santana

Implementa os casos de teste da seção 5.1 do documento do projeto (T2).

Organização (sem classes: cada caso de teste é uma função)
    - Os casos de cada função de acesso formam um grupo e rodam na ordem
      C1, C2, ... da lista GRUPOS, porque alguns dependem do anterior
      (ex.: 1.1 C2 usa o P003 do C1).
    - Antes de cada grupo, o cenário inicial é recriado em uma pasta
      temporária, para que os testes nunca mexam no dados/produtos.json real.
    - A suíte é montada por testes/suite_funcoes.py com unittest.FunctionTestCase.

Cenário inicial (produtos.json)
    P001 - Camiseta Basica - Roupas     - 49.90 - estoque 10
    P002 - Caneca          - Utilidades - 30.10 - estoque 3

Como executar (a partir da pasta raiz do projeto):
    python -m unittest testes.teste_catalogo_produtos -v
  ou
    python testes/teste_catalogo_produtos.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

# Permite rodar o arquivo diretamente (python testes/teste_catalogo_produtos.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos import catalogo_produtos as catalogo   # noqa: E402
from testes.suite_funcoes import grupo, montar_suite, verifica   # noqa: E402

CENARIO_INICIAL = [
    {"codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
     "categoria": "Roupas", "preco": 49.90, "estoque": 10},
    {"codigo": "P002", "nome": "Caneca", "descricao": "Ceramica 300ml",
     "categoria": "Utilidades", "preco": 30.10, "estoque": 3},
]


def montar_cenario_inicial(pasta):
    """Grava o cenário inicial em <pasta>/produtos.json, aponta o módulo
    para esse arquivo e recarrega o catálogo."""
    caminho = os.path.join(pasta, "produtos.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(CENARIO_INICIAL, arquivo, ensure_ascii=False, indent=2)
    catalogo._CAMINHO_ARQUIVO = caminho      # redireciona só durante os testes
    catalogo.CarregarCatalogoDoArq()
    return caminho


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

# --------------------------------------------------------------------------
# Preparação e limpeza do cenário (rodam antes e depois de cada grupo)
# --------------------------------------------------------------------------

_ctx = {}   # caminho original, pasta temporária e arquivo do grupo atual


def preparar_cenario():
    """Recria o cenário inicial numa pasta temporária e aponta o módulo para ela."""
    _ctx["caminho_original"] = catalogo._CAMINHO_ARQUIVO
    _ctx["pasta"] = tempfile.mkdtemp()
    _ctx["arquivo"] = montar_cenario_inicial(_ctx["pasta"])


def limpar_cenario():
    """Devolve o caminho original ao módulo e apaga a pasta temporária."""
    catalogo._CAMINHO_ARQUIVO = _ctx["caminho_original"]
    shutil.rmtree(_ctx["pasta"], ignore_errors=True)



# ==========================================================================
# 1.1 CadastrarProduto(p: dict) -> bool
# ==========================================================================


def caso_1_1_01_cadastro_valido():
    print("1.1 C1 - Cadastro com dados validos e codigo novo")
    retorno = catalogo.CadastrarProduto({
        "codigo": "P003", "nome": "Bone", "descricao": "Aba reta",
        "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
    verifica.assertTrue(retorno)
    verifica.assertEqual(catalogo.BuscarProduto("P003")["nome"], "Bone")


def caso_1_1_02_codigo_ja_existente():
    print("1.1 C2 - Cadastro com codigo ja existente")
    retorno = catalogo.CadastrarProduto({
        "codigo": "P003", "nome": "Outro", "descricao": "Aba reta",
        "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
    verifica.assertFalse(retorno)
    verifica.assertEqual(catalogo.BuscarProduto("P003")["nome"], "Bone")


def caso_1_1_03_campo_obrigatorio_ausente():
    print("1.1 C3 - Cadastro sem o campo preco")
    retorno = catalogo.CadastrarProduto({
        "codigo": "P004", "nome": "Bone", "descricao": "Aba reta",
        "categoria": "Acessorios", "estoque": 5})
    verifica.assertFalse(retorno)
    verifica.assertEqual(catalogo.BuscarProduto("P004"), {})


def caso_1_1_04_preco_menor_ou_igual_a_zero():
    print("1.1 C4 - Cadastro com preco 0")
    retorno = catalogo.CadastrarProduto({
        "codigo": "P005", "nome": "Bone", "descricao": "Aba reta",
        "categoria": "Acessorios", "preco": 0, "estoque": 5})
    verifica.assertFalse(retorno)


def caso_1_1_05_estoque_negativo():
    print("1.1 C5 - Cadastro com estoque -1")
    retorno = catalogo.CadastrarProduto({
        "codigo": "P006", "nome": "Bone", "descricao": "Aba reta",
        "categoria": "Acessorios", "preco": 39.90, "estoque": -1})
    verifica.assertFalse(retorno)


def caso_1_1_06_parametro_tipo_errado():
    print("1.1 C6 - Parametro do tipo errado (string)")
    retorno = catalogo.CadastrarProduto("P007, Meia, 9.90")
    verifica.assertFalse(retorno)


def caso_1_1_08_cadastro_nao_grava_durante_a_execucao():
    print("1.1 C8 (extra) - Cadastro fica so na memoria: o arquivo continua com 2 produtos")
    verifica.assertEqual(catalogo.BuscarProduto("P003")["nome"], "Bone")
    verifica.assertEqual([p["codigo"] for p in ler_arquivo(_ctx["arquivo"])],
                         ["P001", "P002"])


def caso_1_1_07_preco_nao_finito():
    print("1.1 C7 (extra) - Cadastro com preco NaN ou infinito")
    for preco in (float("nan"), float("inf")):
        retorno = catalogo.CadastrarProduto({
            "codigo": "P008", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": preco, "estoque": 5})
        verifica.assertFalse(retorno)
    verifica.assertEqual(catalogo.BuscarProduto("P008"), {})


# ==========================================================================
# 1.2 BuscarProduto(codigo: str) -> dict
# ==========================================================================


def caso_1_2_01_codigo_existente():
    print("1.2 C1 - Busca de codigo existente")
    verifica.assertEqual(catalogo.BuscarProduto("P001"), {
        "codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
        "categoria": "Roupas", "preco": 49.90, "estoque": 10})


def caso_1_2_02_codigo_inexistente():
    print("1.2 C2 - Busca de codigo inexistente")
    verifica.assertEqual(catalogo.BuscarProduto("P999"), {})


# ==========================================================================
# 1.3 BuscarProdutoPorNome(nome: str) -> list
# ==========================================================================


def caso_1_3_01_parte_do_nome_maiusculas():
    print("1.3 C1 - Busca por 'CAMI' (parte do nome, maiusculas)")
    resultado = catalogo.BuscarProdutoPorNome("CAMI")
    verifica.assertEqual(len(resultado), 1)
    verifica.assertEqual(resultado[0]["codigo"], "P001")
    verifica.assertEqual(resultado[0]["nome"], "Camiseta Basica")


def caso_1_3_02_nome_sem_correspondencia():
    print("1.3 C2 - Busca por 'Tenis' (inexistente)")
    verifica.assertEqual(catalogo.BuscarProdutoPorNome("Tenis"), [])


def caso_1_3_03_nome_vazio():
    print("1.3 C3 - Busca com nome vazio")
    verifica.assertEqual(catalogo.BuscarProdutoPorNome(""), [])


# ==========================================================================
# 1.4 ListarProdutos(categoria: str) -> list
# ==========================================================================


def caso_1_4_01_categoria_existente():
    print("1.4 C1 - Listagem da categoria 'Roupas'")
    resultado = catalogo.ListarProdutos("Roupas")
    verifica.assertEqual([p["codigo"] for p in resultado], ["P001"])


def caso_1_4_02_categoria_vazia_lista_todos():
    print("1.4 C2 - Listagem com categoria vazia (todos)")
    resultado = catalogo.ListarProdutos("")
    verifica.assertEqual([p["codigo"] for p in resultado], ["P001", "P002"])


def caso_1_4_03_categoria_sem_produtos():
    print("1.4 C3 - Listagem da categoria 'Livros' (sem produtos)")
    verifica.assertEqual(catalogo.ListarProdutos("Livros"), [])


# ==========================================================================
# 1.5 AtualizarProduto(codigo: str, campo: str, valor) -> bool
# ==========================================================================


def caso_1_5_01_atualizacao_valida():
    print("1.5 C1 - Altera preco de P001 para 59.90")
    verifica.assertTrue(catalogo.AtualizarProduto("P001", "preco", 59.90))
    verifica.assertEqual(catalogo.BuscarProduto("P001")["preco"], 59.90)


def caso_1_5_02_codigo_inexistente():
    print("1.5 C2 - Altera preco de P999 (inexistente)")
    verifica.assertFalse(catalogo.AtualizarProduto("P999", "preco", 10.0))


def caso_1_5_03_campo_inexistente():
    print("1.5 C3 - Altera campo 'cor' (inexistente)")
    verifica.assertFalse(catalogo.AtualizarProduto("P001", "cor", "azul"))
    verifica.assertNotIn("cor", catalogo.BuscarProduto("P001"))


def caso_1_5_04_tentativa_de_alterar_estoque():
    print("1.5 C4 - Tenta alterar o estoque por esta funcao")
    verifica.assertFalse(catalogo.AtualizarProduto("P001", "estoque", 50))
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 10)


def caso_1_5_05_valor_incompativel():
    print("1.5 C5 - Altera preco para 'abc'")
    verifica.assertFalse(catalogo.AtualizarProduto("P001", "preco", "abc"))
    verifica.assertEqual(catalogo.BuscarProduto("P001")["preco"], 59.90)


def caso_1_5_06_preco_nao_finito():
    print("1.5 C6 (extra) - Altera preco para NaN ou infinito")
    verifica.assertFalse(catalogo.AtualizarProduto("P001", "preco", float("nan")))
    verifica.assertFalse(catalogo.AtualizarProduto("P001", "preco", float("inf")))
    verifica.assertEqual(catalogo.BuscarProduto("P001")["preco"], 59.90)


# ==========================================================================
# 1.6 RemoverProduto(codigo: str) -> bool
# ==========================================================================


def caso_1_6_01_codigo_existente():
    print("1.6 C1 - Remove P002")
    verifica.assertTrue(catalogo.RemoverProduto("P002"))
    verifica.assertEqual(catalogo.BuscarProduto("P002"), {})


def caso_1_6_02_codigo_inexistente():
    print("1.6 C2 - Remove P999 (inexistente)")
    verifica.assertFalse(catalogo.RemoverProduto("P999"))


# ==========================================================================
# 1.7 ConsultarEstoque(codigo: str) -> int
# ==========================================================================


def caso_1_7_01_codigo_existente():
    print("1.7 C1 - Estoque de P001")
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 10)


def caso_1_7_02_codigo_inexistente():
    print("1.7 C2 - Estoque de P999 (inexistente)")
    verifica.assertEqual(catalogo.ConsultarEstoque("P999"), -1)


# ==========================================================================
# 1.8 BaixarEstoque(codigo: str, qtd: int) -> bool
# ==========================================================================


def caso_1_8_01_baixa_com_quantidade_disponivel():
    print("1.8 C1 - Baixa de 3 unidades de P001 (10 -> 7)")
    verifica.assertTrue(catalogo.BaixarEstoque("P001", 3))
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 7)


def caso_1_8_02_codigo_inexistente():
    print("1.8 C2 - Baixa em P999 (inexistente)")
    verifica.assertFalse(catalogo.BaixarEstoque("P999", 1))


def caso_1_8_03_quantidade_menor_ou_igual_a_zero():
    print("1.8 C3 - Baixa de 0 unidades")
    verifica.assertFalse(catalogo.BaixarEstoque("P001", 0))
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 7)


def caso_1_8_04_estoque_insuficiente():
    print("1.8 C4 - Baixa de 8 unidades com estoque 7")
    verifica.assertFalse(catalogo.BaixarEstoque("P001", 8))
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 7)


def caso_1_8_05_baixa_nao_grava_durante_a_execucao():
    print("1.8 C5 (extra) - Baixa muda so a memoria: o arquivo continua com estoque 10")
    verifica.assertEqual(catalogo.ConsultarEstoque("P001"), 7)
    estoque_no_arquivo = [p["estoque"] for p in ler_arquivo(_ctx["arquivo"])
                          if p["codigo"] == "P001"]
    verifica.assertEqual(estoque_no_arquivo, [10])


# ==========================================================================
# 1.9 ReporEstoque(codigo: str, qtd: int) -> bool
# ==========================================================================


def caso_1_9_01_reposicao_valida():
    print("1.9 C1 - Repoe 5 unidades de P002 (3 -> 8)")
    verifica.assertTrue(catalogo.ReporEstoque("P002", 5))
    verifica.assertEqual(catalogo.ConsultarEstoque("P002"), 8)


def caso_1_9_02_codigo_inexistente():
    print("1.9 C2 - Repoe P999 (inexistente)")
    verifica.assertFalse(catalogo.ReporEstoque("P999", 5))


def caso_1_9_03_quantidade_menor_ou_igual_a_zero():
    print("1.9 C3 - Repoe 0 unidades")
    verifica.assertFalse(catalogo.ReporEstoque("P002", 0))
    verifica.assertEqual(catalogo.ConsultarEstoque("P002"), 8)


# ==========================================================================
# 1.10 SalvarCatalogoNoArq() -> bool (interna)
# ==========================================================================


def caso_1_10_01_gravacao_com_sucesso():
    print("1.10 C1 - Cadastra P003 e grava (3 produtos no arquivo)")
    catalogo.CadastrarProduto({
        "codigo": "P003", "nome": "Bone", "descricao": "Aba reta",
        "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
    verifica.assertTrue(catalogo.SalvarCatalogoNoArq())
    verifica.assertEqual(len(ler_arquivo(_ctx["arquivo"])), 3)


def caso_1_10_02_arquivo_nao_pode_ser_escrito():
    print("1.10 C2 - Pasta com o nome produtos.json impede a escrita")
    os.remove(_ctx["arquivo"])
    os.mkdir(_ctx["arquivo"])
    verifica.assertFalse(catalogo.SalvarCatalogoNoArq())


# ==========================================================================
# 1.11 CarregarCatalogoDoArq() -> list (interna)
# ==========================================================================


def caso_1_11_01_arquivo_com_produtos():
    print("1.11 C1 - Carrega o arquivo do cenario inicial")
    resultado = catalogo.CarregarCatalogoDoArq()
    verifica.assertEqual([p["codigo"] for p in resultado], ["P001", "P002"])


def caso_1_11_02_arquivo_inexistente():
    print("1.11 C2 - Arquivo inexistente: retorna [] e cria vazio")
    os.remove(_ctx["arquivo"])
    verifica.assertEqual(catalogo.CarregarCatalogoDoArq(), [])
    verifica.assertTrue(os.path.isfile(_ctx["arquivo"]))
    verifica.assertEqual(ler_arquivo(_ctx["arquivo"]), [])

# ==========================================================================
# Ordem de execução: um grupo por função, casos na ordem C1, C2, ...
# ==========================================================================

GRUPOS = [
    # 1.1 CadastrarProduto(p: dict) -> bool
    grupo([
        caso_1_1_01_cadastro_valido,
        caso_1_1_02_codigo_ja_existente,
        caso_1_1_03_campo_obrigatorio_ausente,
        caso_1_1_04_preco_menor_ou_igual_a_zero,
        caso_1_1_05_estoque_negativo,
        caso_1_1_06_parametro_tipo_errado,
        caso_1_1_07_preco_nao_finito,
        caso_1_1_08_cadastro_nao_grava_durante_a_execucao,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.2 BuscarProduto(codigo: str) -> dict
    grupo([
        caso_1_2_01_codigo_existente,
        caso_1_2_02_codigo_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.3 BuscarProdutoPorNome(nome: str) -> list
    grupo([
        caso_1_3_01_parte_do_nome_maiusculas,
        caso_1_3_02_nome_sem_correspondencia,
        caso_1_3_03_nome_vazio,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.4 ListarProdutos(categoria: str) -> list
    grupo([
        caso_1_4_01_categoria_existente,
        caso_1_4_02_categoria_vazia_lista_todos,
        caso_1_4_03_categoria_sem_produtos,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.5 AtualizarProduto(codigo: str, campo: str, valor) -> bool
    grupo([
        caso_1_5_01_atualizacao_valida,
        caso_1_5_02_codigo_inexistente,
        caso_1_5_03_campo_inexistente,
        caso_1_5_04_tentativa_de_alterar_estoque,
        caso_1_5_05_valor_incompativel,
        caso_1_5_06_preco_nao_finito,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.6 RemoverProduto(codigo: str) -> bool
    grupo([
        caso_1_6_01_codigo_existente,
        caso_1_6_02_codigo_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.7 ConsultarEstoque(codigo: str) -> int
    grupo([
        caso_1_7_01_codigo_existente,
        caso_1_7_02_codigo_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.8 BaixarEstoque(codigo: str, qtd: int) -> bool
    grupo([
        caso_1_8_01_baixa_com_quantidade_disponivel,
        caso_1_8_02_codigo_inexistente,
        caso_1_8_03_quantidade_menor_ou_igual_a_zero,
        caso_1_8_04_estoque_insuficiente,
        caso_1_8_05_baixa_nao_grava_durante_a_execucao,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.9 ReporEstoque(codigo: str, qtd: int) -> bool
    grupo([
        caso_1_9_01_reposicao_valida,
        caso_1_9_02_codigo_inexistente,
        caso_1_9_03_quantidade_menor_ou_igual_a_zero,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.10 SalvarCatalogoNoArq() -> bool (interna)
    grupo([
        caso_1_10_01_gravacao_com_sucesso,
        caso_1_10_02_arquivo_nao_pode_ser_escrito,
    ], antes=preparar_cenario, depois=limpar_cenario),
    # 1.11 CarregarCatalogoDoArq() -> list (interna)
    grupo([
        caso_1_11_01_arquivo_com_produtos,
        caso_1_11_02_arquivo_inexistente,
    ], antes=preparar_cenario, depois=limpar_cenario),
]


def load_tests(loader, testes_padrao, padrao):
    """Chamada pelo unittest (discover ou execução direta) para montar a suíte."""
    return montar_suite(GRUPOS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
