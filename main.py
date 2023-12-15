from models import Operador, Transacao, Base
from parsers import ParserPlanilhaOperadores, ParserRelatorioSITEF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, extract
from datetime import datetime

if __name__ == "__main__":
    engine = create_engine('sqlite:///pix.db')
    Session = sessionmaker(engine)
    session = Session()
    Base.metadata.create_all(engine)
    
    #hoje = datetime.now()
    data_inicio_str = "21/10/2023 00:00:00"
    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y %H:%M:%S")
    data_fim_str = "21/10/2023 23:59:59"
    data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y %H:%M:%S")
    
    #df = Transacao.ranking_range_data(session,data_inicio,data_fim)
    df = Transacao.tabela_mensal_quantidade_transacoes(session, 10, 2023)
    print(df)
    
    
    #df = Operador.todos_para_df(session)
    #print(df)
    #r = Operador.todos(session)
    #for x in r:
    #    print(x.codigo_operador)
    #q = session.query(Transacao).filter(extract('month', Transacao.data_transacao)==10).all()
    #q = select(Transacao).where(Transacao.data_transacao.like("2023-10%"))
    #q = select(Transacao).where(extract("month", Transacao.data_transacao) == "10").where(extract("day", Transacao.data_transacao) == "21")
    #result = session.execute(q)
    #result.scalars()
    #for t in result.scalars().all():
    #    print(t)
    session.close()
