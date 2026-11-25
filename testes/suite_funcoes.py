"""
Apoio comum aos módulos testadores: testes escritos só com funções.

As regras da disciplina não permitem que o grupo programe classes. Por isso
nenhum testador declara classe: cada caso de teste é uma função comum, e a
biblioteca unittest a executa por meio de unittest.FunctionTestCase, um
recurso pronto da própria biblioteca padrão do Python.

    verifica       objeto do unittest usado nas assertivas
                   (verifica.assertEqual, verifica.assertTrue, ...)
    grupo(...)     reúne os casos de uma função de acesso, na ordem C1, C2, ...,
                   com as funções de preparação e limpeza do cenário
    montar_suite   transforma a lista de grupos na suíte que o unittest roda

Cada testador expõe load_tests(), que o unittest chama tanto no
"python -m unittest discover" quanto ao rodar o arquivo diretamente.
"""

import unittest

__all__ = ["verifica", "grupo", "montar_suite"]

# Instância da classe pronta do unittest: dá acesso às assertivas
# (assertEqual, assertIn, ...) sem que o grupo declare nenhuma classe.
verifica = unittest.TestCase()


def grupo(casos, antes=None, depois=None, antes_de_cada=None, depois_de_cada=None):
    """
    A) Descrição: descreve os casos de teste de uma função.
    B) Acoplamento:
        casos           lista de funções de teste, na ordem em que devem rodar
        antes, depois   rodam uma vez, antes do primeiro e depois do último caso
        antes_de_cada, depois_de_cada   rodam em volta de cada caso
        Retorno: dicionário com essas informações
    """
    return {"casos": list(casos), "antes": antes, "depois": depois,
            "antes_de_cada": antes_de_cada, "depois_de_cada": depois_de_cada}


def _preparacao(g, primeiro):
    def preparar():
        if primeiro and g["antes"]:
            g["antes"]()
        if g["antes_de_cada"]:
            g["antes_de_cada"]()
    return preparar


def _limpeza(g, ultimo):
    def limpar():
        try:
            if g["depois_de_cada"]:
                g["depois_de_cada"]()
        finally:
            if ultimo and g["depois"]:
                g["depois"]()
    return limpar


def montar_suite(grupos):
    """
    A) Descrição: monta a suíte do unittest com todos os casos, na ordem
       dos grupos e, dentro de cada grupo, na ordem da lista de casos.
    B) Acoplamento:
        grupos (list) lista de dicionários criados por grupo()
        Retorno: unittest.TestSuite pronta para rodar
    """
    suite = unittest.TestSuite()
    for g in grupos:
        total = len(g["casos"])
        for i, caso in enumerate(g["casos"]):
            suite.addTest(unittest.FunctionTestCase(
                caso,
                setUp=_preparacao(g, i == 0),
                tearDown=_limpeza(g, i == total - 1)))
    return suite
