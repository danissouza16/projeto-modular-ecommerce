"""
Módulo testador do GerenciadorClientes (Módulo 2)
Responsável: Pedro Augusto

Implementa os casos de teste da seção 5.2 do documento do projeto (T2),
além dos testes das funções internas 2.1 e 2.2 do Diagrama de Funções de Acesso.

Organização
- Uma classe de teste por função de acesso (2.1 a 2.11).
- Dentro de cada classe, os casos rodam na ordem C1, C2, ... (o unittest
  executa os métodos em ordem alfabética: test_01, test_02, ...).
- Antes de cada classe, o cenário inicial é recriado em uma pasta
  temporária, para que os testes nunca mexam no dados/clientes.json real.
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


class BaseClientes(unittest.TestCase):
    """Recria o cenário inicial em uma pasta temporária para cada classe."""

    @classmethod
    def setUpClass(cls):
        cls.caminho_original = clientes._CAMINHO_ARQUIVO
        cls.pasta = tempfile.mkdtemp()
        cls.arquivo = montar_cenario_inicial(cls.pasta)

    @classmethod
    def tearDownClass(cls):
        clientes._CAMINHO_ARQUIVO = cls.caminho_original
        shutil.rmtree(cls.pasta, ignore_errors=True)


# ==========================================================================
# 2.1 ValidarDados(c: dict) -> bool (interna)
# ==========================================================================

class Teste_2_1_ValidarDados(BaseClientes):

    def test_01_dados_validos(self):
        print("2.1 C1 - Validacao de dicionario com todos os campos validos")
        self.assertTrue(clientes.ValidarDados({
            "cpf": "12345678901",
            "nome": "Maria",
            "email": "maria@test.com",
            "senha": "123",
            "endereco": "Rua A",
        }))

    def test_02_dados_invalidos(self):
        print("2.1 C2 - Validacao falha para campo ausente, CPF invalido ou email sem @")
        self.assertFalse(clientes.ValidarDados("nao e dict"))
        self.assertFalse(clientes.ValidarDados({"cpf": "12345678901", "nome": "Maria"}))
        self.assertFalse(clientes.ValidarDados({
            "cpf": "12345",
            "nome": "Carlos",
            "email": "carlos@test.com",
            "senha": "321",
            "endereco": "Rua D",
        }))
        self.assertFalse(clientes.ValidarDados({
            "cpf": "12345678901",
            "nome": "Maria",
            "email": "mariatest.com",
            "senha": "123",
            "endereco": "Rua A",
        }))


# ==========================================================================
# 2.2 VerificarExistenciaCpf(cpf: str) -> bool (interna)
# ==========================================================================

class Teste_2_2_VerificarExistenciaCpf(BaseClientes):

    def test_01_cpf_existente(self):
        print("2.2 C1 - Verifica CPF ja cadastrado")
        self.assertTrue(clientes.VerificarExistenciaCpf("12345678901"))

    def test_02_cpf_inexistente(self):
        print("2.2 C2 - Verifica CPF nao cadastrado")
        self.assertFalse(clientes.VerificarExistenciaCpf("00000000000"))


# ==========================================================================
# 2.3 CadastrarCliente(c: dict) -> bool
# ==========================================================================

class Teste_2_3_CadastrarCliente(BaseClientes):

    @classmethod
    def setUpClass(cls):
        cls.caminho_original = clientes._CAMINHO_ARQUIVO
        cls.pasta = tempfile.mkdtemp()
        # Começa apenas com o admin para que Maria (12345678901) seja cadastrada em C1
        cls.arquivo = montar_cenario_inicial(cls.pasta, [CENARIO_INICIAL[0]])

    def test_01_cadastro_valido(self):
        print("2.3 C1 - Cadastro com dados validos e CPF/e-mail ainda nao cadastrados")
        retorno = clientes.CadastrarCliente({
            "cpf": "12345678901",
            "nome": "Maria",
            "email": "maria@test.com",
            "senha": "123",
            "endereco": "Rua A",
        })
        self.assertTrue(retorno)

    def test_02_cpf_ja_existente(self):
        print("2.3 C2 - Cadastro com CPF ja existente")
        retorno = clientes.CadastrarCliente({
            "cpf": "12345678901",
            "nome": "Mariana",
            "email": "mariana@test.com",
            "senha": "456",
            "endereco": "Rua B",
        })
        self.assertFalse(retorno)

    def test_03_email_ja_existente(self):
        print("2.3 C3 - Cadastro com e-mail ja existente")
        retorno = clientes.CadastrarCliente({
            "cpf": "98765432100",
            "nome": "João",
            "email": "maria@test.com",
            "senha": "789",
            "endereco": "Rua C",
        })
        self.assertFalse(retorno)

    def test_04_dados_invalidos(self):
        print("2.3 C4 - Cadastro com dados invalidos (CPF incompleto ou campo ausente)")
        self.assertFalse(clientes.CadastrarCliente({
            "cpf": "12345",
            "nome": "Carlos",
            "email": "carlos@test.com",
            "senha": "321",
            "endereco": "Rua D",
        }))
        self.assertFalse(clientes.CadastrarCliente({
            "cpf": "55544433322",
            "nome": "Carlos",
            "senha": "321",
            "endereco": "Rua D",
        }))


# ==========================================================================
# 2.4 AutenticarCliente(email: str, senha: str) -> dict
# ==========================================================================

class Teste_2_4_AutenticarCliente(BaseClientes):

    def test_01_credenciais_corretas(self):
        print("2.4 C1 - Autenticacao com credenciais corretas (sem senha, com perfil)")
        resultado = clientes.AutenticarCliente("maria@test.com", "123")
        self.assertEqual(resultado, {
            "cpf": "12345678901",
            "nome": "Maria",
            "email": "maria@test.com",
            "perfil": "cliente",
            "endereco": "Rua A",
            "carrinho": [{"codigo": "P001", "quantidade": 2}],
        })
        self.assertNotIn("senha", resultado)

        admin = clientes.AutenticarCliente("admin@loja.com", "admin")
        self.assertEqual(admin["perfil"], "admin")
        self.assertNotIn("senha", admin)

    def test_02_email_inexistente(self):
        print("2.4 C2 - Autenticacao com e-mail inexistente")
        self.assertEqual(clientes.AutenticarCliente("inexistente@test.com", "123"), {})

    def test_03_senha_incorreta(self):
        print("2.4 C3 - Autenticacao com senha incorreta")
        self.assertEqual(clientes.AutenticarCliente("maria@test.com", "senhaerrada"), {})


# ==========================================================================
# 2.5 AdicionarItemCarrinho(cpf: str, codigo: str, qtd: int) -> bool
# ==========================================================================

class Teste_2_5_AdicionarItemCarrinho(BaseClientes):

    @classmethod
    def setUpClass(cls):
        cls.caminho_original = clientes._CAMINHO_ARQUIVO
        cls.pasta = tempfile.mkdtemp()
        # Maria começa com carrinho vazio para testar C1 adicionando P001 (qtd 2)
        maria_vazia = dict(CENARIO_INICIAL[1], carrinho=[])
        cls.arquivo = montar_cenario_inicial(cls.pasta, [CENARIO_INICIAL[0], maria_vazia])

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_01_adicao_valida(self, _mock_bus, _mock_est):
        print("2.5 C1 - Adicao valida de produto com estoque suficiente")
        self.assertTrue(clientes.AdicionarItemCarrinho("12345678901", "P001", 2))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_02_cliente_inexistente(self, _mock_bus, _mock_est):
        print("2.5 C2 - Adicao com cliente inexistente")
        self.assertFalse(clientes.AdicionarItemCarrinho("00000000000", "P001", 1))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_03_produto_inexistente(self, _mock_bus, _mock_est):
        print("2.5 C3 - Adicao com produto inexistente no catalogo")
        self.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P999", 1))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_04_quantidade_invalida(self, _mock_bus, _mock_est):
        print("2.5 C4 - Adicao com quantidade menor ou igual a zero")
        self.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", 0))
        self.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", -1))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_05_estoque_insuficiente(self, _mock_bus, _mock_est):
        print("2.5 C5 - Adicao com estoque insuficiente para a quantidade total")
        self.assertFalse(clientes.AdicionarItemCarrinho("12345678901", "P001", 1000))


# ==========================================================================
# 2.6 AlterarQuantidadeItem(cpf: str, codigo: str, qtd: int) -> bool
# ==========================================================================

class Teste_2_6_AlterarQuantidadeItem(BaseClientes):

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    def test_01_alteracao_valida(self, _mock_est):
        print("2.6 C1 - Alteracao valida da quantidade de um item no carrinho")
        self.assertTrue(clientes.AlterarQuantidadeItem("12345678901", "P001", 4))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    def test_02_item_fora_do_carrinho(self, _mock_est):
        print("2.6 C2 - Alteracao de item que nao esta no carrinho")
        self.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P999", 2))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    def test_03_quantidade_menor_ou_igual_a_zero(self, _mock_est):
        print("2.6 C3 - Alteracao com quantidade menor ou igual a zero")
        self.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", 0))
        self.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", -2))

    @patch("modulos.catalogo_produtos.ConsultarEstoque", side_effect=_mock_consultar_estoque)
    def test_04_estoque_insuficiente(self, _mock_est):
        print("2.6 C4 - Alteracao com estoque insuficiente para a nova quantidade")
        self.assertFalse(clientes.AlterarQuantidadeItem("12345678901", "P001", 9999))


# ==========================================================================
# 2.7 RemoverItemCarrinho(cpf: str, codigo: str) -> bool
# ==========================================================================

class Teste_2_7_RemoverItemCarrinho(BaseClientes):

    def test_01_remocao_item_existente(self):
        print("2.7 C1 - Remocao de um item existente no carrinho")
        self.assertTrue(clientes.RemoverItemCarrinho("12345678901", "P001"))

    def test_02_remocao_item_inexistente(self):
        print("2.7 C2 - Remocao de um item que nao esta no carrinho")
        self.assertFalse(clientes.RemoverItemCarrinho("12345678901", "P999"))

    def test_03_remocao_cliente_inexistente(self):
        print("2.7 C3 - Remocao com cliente inexistente")
        self.assertFalse(clientes.RemoverItemCarrinho("00000000000", "P001"))


# ==========================================================================
# 2.8 ObterCarrinho(cpf: str) -> list
# ==========================================================================

class Teste_2_8_ObterCarrinho(BaseClientes):

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_01_carrinho_com_itens(self, _mock_bus):
        print("2.8 C1 - Obtencao de carrinho com itens adicionados")
        self.assertEqual(clientes.ObterCarrinho("12345678901"), [{
            "codigo": "P001",
            "nome": "Camiseta Basica",
            "preco": 49.90,
            "quantidade": 2,
        }])

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_02_carrinho_vazio(self, _mock_bus):
        print("2.8 C2 - Obtencao de carrinho vazio")
        self.assertEqual(clientes.ObterCarrinho("98765432100"), [])

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_03_cliente_inexistente(self, _mock_bus):
        print("2.8 C3 - Obtencao de carrinho para cliente inexistente")
        self.assertEqual(clientes.ObterCarrinho("00000000000"), [])


# ==========================================================================
# 2.9 CalcularSubtotal(cpf: str) -> float
# ==========================================================================

class Teste_2_9_CalcularSubtotal(BaseClientes):

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_01_subtotal_com_itens(self, _mock_bus):
        print("2.9 C1 - Calculo de subtotal com itens no carrinho")
        self.assertEqual(clientes.CalcularSubtotal("12345678901"), 99.80)

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_02_subtotal_carrinho_vazio(self, _mock_bus):
        print("2.9 C2 - Calculo de subtotal com carrinho vazio")
        self.assertEqual(clientes.CalcularSubtotal("98765432100"), 0.0)

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_03_subtotal_cliente_inexistente(self, _mock_bus):
        print("2.9 C3 - Calculo para cliente inexistente")
        self.assertEqual(clientes.CalcularSubtotal("00000000000"), 0.0)


# ==========================================================================
# 2.10 EsvaziarCarrinho(cpf: str) -> bool
# ==========================================================================

class Teste_2_10_EsvaziarCarrinho(BaseClientes):

    @patch("modulos.catalogo_produtos.BuscarProduto", side_effect=_mock_buscar_produto)
    def test_01_esvaziar_carrinho_existente(self, _mock_bus):
        print("2.10 C1 - Esvaziamento de carrinho existente (apos pagamento)")
        self.assertTrue(clientes.EsvaziarCarrinho("12345678901"))
        self.assertEqual(clientes.ObterCarrinho("12345678901"), [])

    def test_02_esvaziar_cliente_inexistente(self):
        print("2.10 C2 - Esvaziamento para cliente inexistente")
        self.assertFalse(clientes.EsvaziarCarrinho("00000000000"))


# ==========================================================================
# 2.11 SalvarClientesNoArq() -> bool (interna)
# ==========================================================================

class Teste_2_11_SalvarClientesNoArq(BaseClientes):

    def test_01_gravacao_bem_sucedida(self):
        print("2.11 C1 - Gravacao bem-sucedida no arquivo clientes.json")
        clientes.CadastrarCliente({
            "cpf": "44433322211",
            "nome": "Ana",
            "email": "ana@test.com",
            "senha": "111",
            "endereco": "Rua D",
        })
        self.assertTrue(clientes.SalvarClientesNoArq())
        self.assertEqual(len(ler_arquivo(self.arquivo)), 4)

    def test_02_falha_de_gravacao(self):
        print("2.11 C2 - Falha de gravacao caso ocorra erro no sistema de arquivos")
        os.remove(self.arquivo)
        os.mkdir(self.arquivo)
        self.assertFalse(clientes.SalvarClientesNoArq())


if __name__ == "__main__":
    unittest.main(verbosity=2)