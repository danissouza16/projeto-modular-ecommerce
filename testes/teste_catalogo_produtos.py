"""
Módulo testador do CatalogoProdutos (Módulo 1)
Responsável: Daniel Santana

Implementa os casos de teste da seção 5.1 do documento do projeto (T2).

Organização
    - Uma classe de teste por função de acesso.
    - Dentro de cada classe, os casos rodam na ordem C1, C2, ... (o unittest
      executa os métodos em ordem alfabética: test_01, test_02, ...), porque
      alguns casos dependem do anterior (ex.: 1.1 C2 usa o P003 do C1).
    - Antes de cada classe, o cenário inicial é recriado em uma pasta
      temporária, para que os testes nunca mexam no dados/produtos.json real.

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


class BaseCatalogo(unittest.TestCase):
    """Recria o cenário inicial em uma pasta temporária para cada classe."""

    @classmethod
    def setUpClass(cls):
        cls.caminho_original = catalogo._CAMINHO_ARQUIVO
        cls.pasta = tempfile.mkdtemp()
        cls.arquivo = montar_cenario_inicial(cls.pasta)

    @classmethod
    def tearDownClass(cls):
        catalogo._CAMINHO_ARQUIVO = cls.caminho_original
        shutil.rmtree(cls.pasta, ignore_errors=True)


# ==========================================================================
# 1.1 CadastrarProduto(p: dict) -> bool
# ==========================================================================

class Teste_1_1_CadastrarProduto(BaseCatalogo):

    def test_01_cadastro_valido(self):
        print("1.1 C1 - Cadastro com dados validos e codigo novo")
        retorno = catalogo.CadastrarProduto({
            "codigo": "P003", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
        self.assertTrue(retorno)
        self.assertEqual(catalogo.BuscarProduto("P003")["nome"], "Bone")

    def test_02_codigo_ja_existente(self):
        print("1.1 C2 - Cadastro com codigo ja existente")
        retorno = catalogo.CadastrarProduto({
            "codigo": "P003", "nome": "Outro", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
        self.assertFalse(retorno)
        self.assertEqual(catalogo.BuscarProduto("P003")["nome"], "Bone")

    def test_03_campo_obrigatorio_ausente(self):
        print("1.1 C3 - Cadastro sem o campo preco")
        retorno = catalogo.CadastrarProduto({
            "codigo": "P004", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "estoque": 5})
        self.assertFalse(retorno)
        self.assertEqual(catalogo.BuscarProduto("P004"), {})

    def test_04_preco_menor_ou_igual_a_zero(self):
        print("1.1 C4 - Cadastro com preco 0")
        retorno = catalogo.CadastrarProduto({
            "codigo": "P005", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": 0, "estoque": 5})
        self.assertFalse(retorno)

    def test_05_estoque_negativo(self):
        print("1.1 C5 - Cadastro com estoque -1")
        retorno = catalogo.CadastrarProduto({
            "codigo": "P006", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": 39.90, "estoque": -1})
        self.assertFalse(retorno)

    def test_06_parametro_tipo_errado(self):
        print("1.1 C6 - Parametro do tipo errado (string)")
        retorno = catalogo.CadastrarProduto("P007, Meia, 9.90")
        self.assertFalse(retorno)


# ==========================================================================
# 1.2 BuscarProduto(codigo: str) -> dict
# ==========================================================================

class Teste_1_2_BuscarProduto(BaseCatalogo):

    def test_01_codigo_existente(self):
        print("1.2 C1 - Busca de codigo existente")
        self.assertEqual(catalogo.BuscarProduto("P001"), {
            "codigo": "P001", "nome": "Camiseta Basica", "descricao": "Algodao",
            "categoria": "Roupas", "preco": 49.90, "estoque": 10})

    def test_02_codigo_inexistente(self):
        print("1.2 C2 - Busca de codigo inexistente")
        self.assertEqual(catalogo.BuscarProduto("P999"), {})


# ==========================================================================
# 1.3 BuscarProdutoPorNome(nome: str) -> list
# ==========================================================================

class Teste_1_3_BuscarProdutoPorNome(BaseCatalogo):

    def test_01_parte_do_nome_maiusculas(self):
        print("1.3 C1 - Busca por 'CAMI' (parte do nome, maiusculas)")
        resultado = catalogo.BuscarProdutoPorNome("CAMI")
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["codigo"], "P001")
        self.assertEqual(resultado[0]["nome"], "Camiseta Basica")

    def test_02_nome_sem_correspondencia(self):
        print("1.3 C2 - Busca por 'Tenis' (inexistente)")
        self.assertEqual(catalogo.BuscarProdutoPorNome("Tenis"), [])

    def test_03_nome_vazio(self):
        print("1.3 C3 - Busca com nome vazio")
        self.assertEqual(catalogo.BuscarProdutoPorNome(""), [])


# ==========================================================================
# 1.4 ListarProdutos(categoria: str) -> list
# ==========================================================================

class Teste_1_4_ListarProdutos(BaseCatalogo):

    def test_01_categoria_existente(self):
        print("1.4 C1 - Listagem da categoria 'Roupas'")
        resultado = catalogo.ListarProdutos("Roupas")
        self.assertEqual([p["codigo"] for p in resultado], ["P001"])

    def test_02_categoria_vazia_lista_todos(self):
        print("1.4 C2 - Listagem com categoria vazia (todos)")
        resultado = catalogo.ListarProdutos("")
        self.assertEqual([p["codigo"] for p in resultado], ["P001", "P002"])

    def test_03_categoria_sem_produtos(self):
        print("1.4 C3 - Listagem da categoria 'Livros' (sem produtos)")
        self.assertEqual(catalogo.ListarProdutos("Livros"), [])


# ==========================================================================
# 1.5 AtualizarProduto(codigo: str, campo: str, valor) -> bool
# ==========================================================================

class Teste_1_5_AtualizarProduto(BaseCatalogo):

    def test_01_atualizacao_valida(self):
        print("1.5 C1 - Altera preco de P001 para 59.90")
        self.assertTrue(catalogo.AtualizarProduto("P001", "preco", 59.90))
        self.assertEqual(catalogo.BuscarProduto("P001")["preco"], 59.90)

    def test_02_codigo_inexistente(self):
        print("1.5 C2 - Altera preco de P999 (inexistente)")
        self.assertFalse(catalogo.AtualizarProduto("P999", "preco", 10.0))

    def test_03_campo_inexistente(self):
        print("1.5 C3 - Altera campo 'cor' (inexistente)")
        self.assertFalse(catalogo.AtualizarProduto("P001", "cor", "azul"))
        self.assertNotIn("cor", catalogo.BuscarProduto("P001"))

    def test_04_tentativa_de_alterar_estoque(self):
        print("1.5 C4 - Tenta alterar o estoque por esta funcao")
        self.assertFalse(catalogo.AtualizarProduto("P001", "estoque", 50))
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 10)

    def test_05_valor_incompativel(self):
        print("1.5 C5 - Altera preco para 'abc'")
        self.assertFalse(catalogo.AtualizarProduto("P001", "preco", "abc"))
        self.assertEqual(catalogo.BuscarProduto("P001")["preco"], 59.90)


# ==========================================================================
# 1.6 RemoverProduto(codigo: str) -> bool
# ==========================================================================

class Teste_1_6_RemoverProduto(BaseCatalogo):

    def test_01_codigo_existente(self):
        print("1.6 C1 - Remove P002")
        self.assertTrue(catalogo.RemoverProduto("P002"))
        self.assertEqual(catalogo.BuscarProduto("P002"), {})

    def test_02_codigo_inexistente(self):
        print("1.6 C2 - Remove P999 (inexistente)")
        self.assertFalse(catalogo.RemoverProduto("P999"))


# ==========================================================================
# 1.7 ConsultarEstoque(codigo: str) -> int
# ==========================================================================

class Teste_1_7_ConsultarEstoque(BaseCatalogo):

    def test_01_codigo_existente(self):
        print("1.7 C1 - Estoque de P001")
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 10)

    def test_02_codigo_inexistente(self):
        print("1.7 C2 - Estoque de P999 (inexistente)")
        self.assertEqual(catalogo.ConsultarEstoque("P999"), -1)


# ==========================================================================
# 1.8 BaixarEstoque(codigo: str, qtd: int) -> bool
# ==========================================================================

class Teste_1_8_BaixarEstoque(BaseCatalogo):

    def test_01_baixa_com_quantidade_disponivel(self):
        print("1.8 C1 - Baixa de 3 unidades de P001 (10 -> 7)")
        self.assertTrue(catalogo.BaixarEstoque("P001", 3))
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 7)

    def test_02_codigo_inexistente(self):
        print("1.8 C2 - Baixa em P999 (inexistente)")
        self.assertFalse(catalogo.BaixarEstoque("P999", 1))

    def test_03_quantidade_menor_ou_igual_a_zero(self):
        print("1.8 C3 - Baixa de 0 unidades")
        self.assertFalse(catalogo.BaixarEstoque("P001", 0))
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 7)

    def test_04_estoque_insuficiente(self):
        print("1.8 C4 - Baixa de 8 unidades com estoque 7")
        self.assertFalse(catalogo.BaixarEstoque("P001", 8))
        self.assertEqual(catalogo.ConsultarEstoque("P001"), 7)


# ==========================================================================
# 1.9 ReporEstoque(codigo: str, qtd: int) -> bool
# ==========================================================================

class Teste_1_9_ReporEstoque(BaseCatalogo):

    def test_01_reposicao_valida(self):
        print("1.9 C1 - Repoe 5 unidades de P002 (3 -> 8)")
        self.assertTrue(catalogo.ReporEstoque("P002", 5))
        self.assertEqual(catalogo.ConsultarEstoque("P002"), 8)

    def test_02_codigo_inexistente(self):
        print("1.9 C2 - Repoe P999 (inexistente)")
        self.assertFalse(catalogo.ReporEstoque("P999", 5))

    def test_03_quantidade_menor_ou_igual_a_zero(self):
        print("1.9 C3 - Repoe 0 unidades")
        self.assertFalse(catalogo.ReporEstoque("P002", 0))
        self.assertEqual(catalogo.ConsultarEstoque("P002"), 8)


# ==========================================================================
# 1.10 SalvarCatalogoNoArq() -> bool (interna)
# ==========================================================================

class Teste_1_10_SalvarCatalogoNoArq(BaseCatalogo):

    def test_01_gravacao_com_sucesso(self):
        print("1.10 C1 - Cadastra P003 e grava (3 produtos no arquivo)")
        catalogo.CadastrarProduto({
            "codigo": "P003", "nome": "Bone", "descricao": "Aba reta",
            "categoria": "Acessorios", "preco": 39.90, "estoque": 5})
        self.assertTrue(catalogo.SalvarCatalogoNoArq())
        self.assertEqual(len(ler_arquivo(self.arquivo)), 3)

    def test_02_arquivo_nao_pode_ser_escrito(self):
        print("1.10 C2 - Pasta com o nome produtos.json impede a escrita")
        os.remove(self.arquivo)
        os.mkdir(self.arquivo)
        self.assertFalse(catalogo.SalvarCatalogoNoArq())


# ==========================================================================
# 1.11 CarregarCatalogoDoArq() -> list (interna)
# ==========================================================================

class Teste_1_11_CarregarCatalogoDoArq(BaseCatalogo):

    def test_01_arquivo_com_produtos(self):
        print("1.11 C1 - Carrega o arquivo do cenario inicial")
        resultado = catalogo.CarregarCatalogoDoArq()
        self.assertEqual([p["codigo"] for p in resultado], ["P001", "P002"])

    def test_02_arquivo_inexistente(self):
        print("1.11 C2 - Arquivo inexistente: retorna [] e cria vazio")
        os.remove(self.arquivo)
        self.assertEqual(catalogo.CarregarCatalogoDoArq(), [])
        self.assertTrue(os.path.isfile(self.arquivo))
        self.assertEqual(ler_arquivo(self.arquivo), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
