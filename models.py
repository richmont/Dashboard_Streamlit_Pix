from typing import List
from datetime import datetime
import logging
import sqlalchemy
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy import select, between
from sqlalchemy.sql.expression import func
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Operador(Base):
    """Classe compatível com SQLAlchemy que representa um operador
    """
    __tablename__ = 'operador'
    id: Mapped[int] = mapped_column(primary_key = True)
    codigo_operador:Mapped[int] = mapped_column(Integer, unique=True)
    nome:Mapped[str] = mapped_column(String(100))
    login:Mapped[str] = mapped_column(String(30))
    transacao:Mapped[List["Transacao"]] = relationship(back_populates="operador")

    def __repr__(self) -> str:
        return f"Código operador: {self.codigo_operador}, Nome: {self.nome}, Login: {self.login}"

    def to_dict(self) -> dict:
        """Gera um dicionário com os atributos da classe
        """
        return {
            "id": self.id,
            "codigo_operador": self.codigo_operador,
            "nome": self.nome,
            "login": self.login
        }

    @staticmethod
    def todos(session:sqlalchemy.orm.session.Session) -> list:
        """Retorna todos os operadores cadastrados

        Args:
            session (sqlalchemy.orm.session.Session): Sessão do SQLALchemy

        Returns:
            list: Lista com objetos Operador
        """
        r = session.execute(select(Operador)).scalars().all()
        return r
    
    @staticmethod
    def todos_para_df(session:sqlalchemy.orm.session.Session) -> list:
        """Retorna todos os operadores cadastrados na forma de um dataframe
        Usa o método to_dict() e a lista de colunas para gerar o dataframe

        Args:
            session (sqlalchemy.orm.session.Session): Sessão do SQLALchemy

        Returns:
            pd.DataFrame: DF com todos os operadores 
        """
        lista_dicts = []
        r = session.execute(select(Operador)).scalars().all()
        for x in r:
            operador_dict = x.to_dict()
            lista_dicts.append(operador_dict)
        return pd.DataFrame(lista_dicts, columns=Operador.__table__.columns.keys())
        
    @staticmethod
    def operador_por_codigo(session:sqlalchemy.orm.session.Session, cod_operador:int):
        """Consulta no banco um operador a partir do código de operador

        Args:
            session (sqlalchemy.orm.session.Session): Sessão com conexão ao banco
            cod_operador (int): Código numérico que identifica operador
        """
        result = session.execute(select(Operador).where(Operador.codigo_operador == cod_operador)).first()
        if result:
            return result[0]

    @staticmethod
    def existe(session:sqlalchemy.orm.session.Session, cod_operador:int) -> bool:
        """Verifica se operador existe no banco baseado no código identificador

        Args:
            session (sqlalchemy.orm.session.Session): Session do SQLAlchemy
            nsu (int): Identificador de operador

        Returns:
            bool: True se operador existe, False se não
        """
        result = session.execute(select(Operador).where(Operador.codigo_operador == cod_operador)).first()
        if result:
            return True
        else:
            return False

    @staticmethod
    def gravar_banco(df:pd.DataFrame, session:sqlalchemy.orm.session.Session):
        """Grava os dados de transações do dataframe no banco identificado pelo Session

        Args:
            df (pandas.DataFrame): DataFrame com dados de transações
            session (sqlalchemy.orm.session.Session): Session do SQLAlchemy
        """
        for ind in df.index:
            codigo = int(df['Código'][ind])
            nome = df['Nome'][ind]
            login = df['Logname'][ind]
            if Operador.existe(session, codigo):
                logger.info("Operador %s já existe no banco", nome)
            else:
                model_operador = Operador(
                codigo_operador=codigo,
                nome=nome,
                login=login
            )
                session.add(model_operador)
                logger.info("Gravando operador %s no banco", nome)
                del model_operador
        session.commit()

class Transacao(Base):
    """Classe compatível com SQLAlchemy que representa uma transação
    Attrs:
        nsu
        codigo_operador
        pdv
        transacao
        estado_transacao
        data_transacao
    """
    __tablename__ = 'transacao'
    id:Mapped[int] = mapped_column(primary_key = True)
    nsu:Mapped[str] = mapped_column(String(30), unique=True)
    data_transacao = mapped_column(DateTime, nullable=False)
    pdv:Mapped[int] = mapped_column(String(10))
    tipo_transacao:Mapped[str] = mapped_column(String(15))
    estado_transacao:Mapped[str] = mapped_column(String(30))
    codigo_operador:Mapped[int] = mapped_column(ForeignKey("operador.codigo_operador"))
    operador:Mapped["Operador"] = relationship(back_populates="transacao")
    
    class exc():
        class OperadorAusente(Exception):
            """Exceção para operador ausente no banco de dados
            """
            pass

        class ConsultaInvalida(Exception):
            """Exceção para consulta inválida no banco
            """
            pass

    def __repr__(self):
        return f"NSU: {self.nsu}, Data da transação: {self.data_transacao}, PDV: {self.pdv}"

    def to_dict(self):
        """Transforma em um dicionário

        Returns:
            dict: dicionário com os atributos do objeto
        """
        if self.operador is not None:
            return {
                "id": self.id,
                "nsu": self.nsu,
                "data_transacao": self.data_transacao,
                "codigo_operador": self.codigo_operador,
                "nome_operador": self.operador.nome
            }
        else:
             return {
                "id": self.id,
                "nsu": self.nsu,
                "data_transacao": self.data_transacao,
                "codigo_operador": self.codigo_operador,
                "nome_operador": "OPERADOR NÃO CADASTRADO"
            }

    @staticmethod
    def ranking_range_data(session:sqlalchemy.orm.session.Session, data_inicial:datetime, data_final:datetime) -> pd.DataFrame:
        """Consulta todas as transações em determinado período de tempo

        Args:
            session (sqlalchemy.orm.session.Session): Sessão para acesso ao banco
            data_inicial (datetime): Data de início
            data_final (datetime): Data de fim

        Raises:
            Transacao.exc.ConsultaInvalida: Período informado na consulta é inválido

        Returns:
            pd.DataFrame: DataFrame com os dados da consulta
        """
        tabela_transacao = Transacao.__table__
        tabela_operador = Operador.__table__
        consulta = select(
            tabela_transacao.c.codigo_operador,tabela_operador.c.nome, func.count().label("contagem")
            ).join(
                tabela_operador
                ).where(
                    between(Transacao.data_transacao, data_inicial, data_final)
                    ).group_by(
                tabela_transacao.c.codigo_operador
                ).order_by("contagem")
        r = session.execute(consulta).all()
        if r:
            df = pd.DataFrame(r, columns=["codigo_operador", "nome_operador", "contagem_pix"])
            df["codigo_operador"] = df["codigo_operador"].astype(int)
            return df.sort_values("contagem_pix",ascending=False)
        else:
            raise Transacao.exc.ConsultaInvalida("Ranking inválido, não há pix registrados")
    
    @staticmethod
    def tabela_mensal_quantidade_transacoes(session:sqlalchemy.orm.session.Session, mes: int, ano: int) -> pd.DataFrame:
        """
        Args:
        session (sqlalchemy.orm.session.Session)
        mes (int): formato MM
        ano (int): formato YYYY
        """
        
        
        """
        Dataframe com a seguinte query:
        SELECT strftime('%d/%m/%Y', datetime(transacao.data_transacao)) AS "Data", COUNT(*) AS "Contagem de Transações",
        strftime('%H:%M', min(datetime(transacao.data_transacao))) as "Primeira transação", strftime('%H:%M',max(datetime(transacao.data_transacao))) as "Última transação"
        FROM transacao
        WHERE strftime('%Y-%m', transacao.data_transacao) = '2023-10'
        GROUP BY strftime('%d/%m/%Y', datetime(transacao.data_transacao))
        ORDER BY datetime(transacao.data_transacao);

        """
        tabela_transacao = Transacao.__table__
        
        consulta = select(
            sqlalchemy.func.date_format(tabela_transacao.c.data_transacao,'%d/%m/%Y'), func.count().label("Contagem"), 
            sqlalchemy.func.min(sqlalchemy.func.date_format(tabela_transacao.c.data_transacao, '%H:%i')),
            sqlalchemy.func.max(sqlalchemy.func.date_format(tabela_transacao.c.data_transacao, '%H:%i')),
            ).where(sqlalchemy.func.date_format(tabela_transacao.c.data_transacao, '%Y-%m') == f"{int(ano)}-{int(mes)}"
                ).group_by(sqlalchemy.func.date_format(tabela_transacao.c.data_transacao,'%d/%m/%Y'))
        r = session.execute(consulta).all()
        
        if r:
            df = pd.DataFrame(r, columns=["data_movimento", "contagem_transacoes", "primeira_transacao", "ultima_transacao"])
            return df
        else:
            raise Transacao.exc.ConsultaInvalida("Período inválido")
    
    @staticmethod
    def existe(session:sqlalchemy.orm.session.Session, nsu:int) -> bool:
        """Verifica se transação existe no banco baseado no código identificador

        Args:
            session (sqlalchemy.orm.session.Session): Session do SQLAlchemy
            nsu (int): Identificador de transação

        Returns:
            bool: True se transação existe, False se não
        """
        result = session.execute(select(Transacao).where(Transacao.nsu == nsu)).first()
        if result:
            return True
        else:
            return False
    
    @staticmethod
    def gravar_banco(df:pd.DataFrame, session:sqlalchemy.orm.session.Session):
        """Grava os dados de operadores do dataframe no banco identificado pelo Session

        Args:
            df (pandas.DataFrame): DataFrame com dados de operador
            session (sqlalchemy.orm.session.Session): Session do SQLAlchemy
        """
        for ind in df.index:
            pdv = df['Pdv'][ind]
            data_transacao = df['Datetime'][ind]
            nsu = f"{data_transacao}-{pdv}"
            codigo_operador = int(df['Operador'][ind])
            tipo_transacao = df['Transacao'][ind]
            estado_transacao = df['Estado Transacao'][ind]
            

            if Transacao.existe(session, nsu):
                logger.info("Transacao %s já existe no banco", data_transacao)
            else:
                if Operador.existe(session, int(codigo_operador)):
                    model_transacao = Transacao(
                    nsu=nsu,
                    codigo_operador=int(codigo_operador),
                    pdv=pdv,
                    tipo_transacao=tipo_transacao,
                    estado_transacao=estado_transacao,
                    data_transacao=data_transacao
                    )   
                
                    session.add(model_transacao)
                    logger.info("gravando transacao da data %s no banco", data_transacao)
                    del model_transacao
                else:
                    raise Transacao.exc.OperadorAusente("Operador ausente, atualize a tabela de operadores e tente novamente ", codigo_operador)   
        session.commit()

if __name__ == "__main__":
    pass
    