import unittest
import logging
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from models import Operador,Transacao, Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if TEST_DATABASE_URL is None:
    raise ValueError("Variável de ambiente TEST_DATABASE_URL ausente")
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

"""
debug do sqlalchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
"""
class TestOperador(unittest.TestCase):
    """Testa as funcionalidades de gravação e consulta de operadores no banco de dados
    """
    @classmethod
    def setUpClass(cls):
        """Prepara a conexão ao banco de testes e cria as tabelas
        """
        logger.info("Preparando conexão ao banco")
        cls.url_banco_testes = TEST_DATABASE_URL
        cls.engine = create_engine(cls.url_banco_testes)
        logger.info("Criando tabelas de teste")
        Base.metadata.create_all(bind=cls.engine)
        Session = sessionmaker(cls.engine, autoflush=False)
        cls.session = Session()
        logger.info("Gerando dataframe operadores")
        cls.gerar_dataframe_operadores(cls)
        cls.gerar_dataframe_transacoes(cls)

    def gerar_dataframe_operadores(self):
        """Gera o dataframe com nomes e códigos de exemplo para gravar no banco
        """
        lista_operadores = []
        # nomes aleatórios, não tem intenção de representar pessoas reais
        nomes = ["Maria", "Jose", "Raimunda", "Kellen", "Francisca", 
                "Estevan", "Adriana", "Eliane", "Edilma", "Andrei"]
        logger.info("Tamanho da lista de nomes: %s", len(nomes))
        for i, nome in enumerate(nomes):
            d = {
                "Código": i+1,
                "Nome": f"{nome}",
                "Logname": f"{nome.lower()}{i+1}"
            }
            logger.info("Operador gerado: %s",d)
            lista_operadores.append(d)
        self.df_operadores = pd.DataFrame(lista_operadores)

    def gerar_dataframe_transacoes(self):
        """Com valores gerados dinâmicamente cria um dataframe 
        para inserir no banco de dados
        """
        lista_transacoes = []
        data_transacao_base = datetime.strptime(
            "01/01/2023 00:00:00", "%d/%m/%Y %H:%M:%S"
            )
        lista_possiveis_nsu = list(range(1, 1000))
        random.shuffle(lista_possiveis_nsu)

        while len(lista_transacoes) < 20:
            # Gera valores semi-aleatórios para preencher o dataframe
            
            d = {
                "Nsu": lista_possiveis_nsu.pop(),
                "Operador": random.randint(1, 10),
                "Pdv": f"P00{random.randint(1, 30)}",
                "Transacao": "Compra Pix", # if random.choice([True, False]) else "Dinheiro",
                "Estado Transacao": "Efetuada PDV", # if random.choice([True, False]) else "Negada",
                "Datetime": data_transacao_base + timedelta(minutes=len(lista_transacoes)) # soma minutos equivalente ao tamanho da lista total
            }
            lista_transacoes.append(d)
        self.df_transacoes = pd.DataFrame(lista_transacoes)

    def test_a_gravar_no_banco(self):
        """Grava os operadores gerados no banco de dados
        nomeado com "a" para execução na ordem correta
        """
        logger.info("Iniciando gravação no banco")
        Operador.gravar_banco(self.df_operadores, self.session)
        todos = Operador.todos(self.session)
        logger.info("Tamanho da lista de todos os operadores: %s", len(todos))
        self.assertEqual(len(todos),10)

    def test_b_consulta_operador(self):
        """Verifica se os operadores gerados estão presentes no banco
        """
        op_maria = Operador.operador_por_codigo(self.session, 1)
        op_andrei = Operador.operador_por_codigo(self.session, 10)
        logger.info("Consultando no banco pelas informações de operadores esperadas")
        self.assertIsNotNone(op_maria)
        self.assertIsNotNone(op_andrei)
        self.assertEqual(op_maria.nome, "Maria")
        self.assertEqual(op_andrei.nome, "Andrei")

    def test_c_gravar_transacoes_banco(self):
        """Grava as transações geradas no banco
        """
        logger.info("Grava as transacoes no banco")
        Transacao.gravar_banco(self.df_transacoes, self.session)

    def test_d_ranking(self):
        """Consulta as transações gravadas no banco com consulta válida e uma inválida
        """
        logger.info("Gerando consulta no banco com data válida")
        ranking_range_data_correto = Transacao.ranking_range_data(
            self.session, 
            datetime.strptime("01/01/2023 00:00:00", "%d/%m/%Y %H:%M:%S"),
            datetime.strptime("31/12/2023 00:00:00", "%d/%m/%Y %H:%M:%S")
            )
        self.assertIsNotNone(ranking_range_data_correto)

        logger.info("Gerando consulta no banco com data inválida")
        try:
            _ = Transacao.ranking_range_data(
                self.session, 
                datetime.strptime("01/01/1990 00:00:00", "%d/%m/%Y %H:%M:%S"),
                datetime.strptime("31/12/1990 00:00:00", "%d/%m/%Y %H:%M:%S")
                )
        except Transacao.exc.ConsultaInvalida:
            self.assertTrue(True)

    @classmethod
    def tearDownClass(cls):
        """Limpa o banco de dados para evitar resíduos de interferência no teste
        """
        cls.session.commit()
        logger.info("Teste concluído, eliminando tabelas do banco")
        Base.metadata.drop_all(bind=cls.engine)
        cls.session.close()


if __name__ == '__main__':
    unittest.main()