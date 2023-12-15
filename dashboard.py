import io
import os
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st
from models import Operador, Transacao, Base
from parsers import ParserPlanilhaOperadores, ParserRelatorioSITEF


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise Exception("Variável de ambiente 'DATABASE_URL' faltando, necessária para iniciar")
# problemas ao gravar campos DateTime usando o conector do MariaDB, este usa Timestamp e não Datetime por padrão

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(engine, autoflush=False)
session = Session()

def atualizar_operadores(session, conteudo_csv_operadores):
    o = ParserPlanilhaOperadores(conteudo_csv_operadores)
    Operador.gravar_banco(o.df, session)

def atualizar_transacoes(session, conteudo_csv_transacoes):
    
    t = ParserRelatorioSITEF(conteudo_csv_transacoes)
    Transacao.gravar_banco(t.df, session)
    

def gerar_ranking(session, data_inicial, data_final):
    df_ranking = Transacao.ranking_range_data(session, data_inicial, data_final)
    df_ranking["codigo_operador"] = df_ranking["codigo_operador"].astype(int)
    
    return df_ranking

hoje = datetime.now()
df = Operador.todos_para_df(session)
st.set_page_config(layout="wide")
col1, col2, col3 = st.columns(3)

#data_inicio_str = "21/10/2023 00:00:00"
#data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y %H:%M:%S")
#data_fim_str = "21/10/2023 23:59:59"
#data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y %H:%M:%S")

with col1:
   input_data_inicio = st.date_input("Data de início", value=hoje, format="DD/MM/YYYY")
   data_inicio = datetime.strptime(f"{input_data_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
   

with col2:
    
    input_data_fim = st.date_input("Data de fim", value=hoje, format="DD/MM/YYYY")
    data_fim = datetime.strptime(f"{input_data_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")
    
lateral_upload_relatorios = st.sidebar
with lateral_upload_relatorios:
    csv_operadores = st.file_uploader("Atualizar relação de operadores", type=["csv"])
    if csv_operadores is not None:
        st.button("Atualizar operadores", on_click=atualizar_operadores, args=(session, csv_operadores))
    
    csv_transacoes = st.file_uploader("Atualizar transações", type=["csv"])
    if csv_transacoes is not None:
        
        st.button("Atualizar transações", on_click=atualizar_transacoes, args=(session, csv_transacoes))


st.title('Ranking de transações do Pix por operador')

try:
    df_ranking = gerar_ranking(session, data_inicio, data_fim)
    st.dataframe(df_ranking,use_container_width=True, height=1500)
except Transacao.exc.ConsultaInvalida as e:
    "Período sem transações para exibir, verifique a data ou alimente relatório deste período"

st.title('Quantidade de transações por período')
try:
    mes = input_data_inicio.strftime("%m")
    ano = input_data_inicio.strftime("%Y")
    df_mensal = Transacao.tabela_mensal_quantidade_transacoes(
        session, 
        int(mes),
        int(ano)
        )
    st.dataframe(df_mensal, use_container_width=True)
    st.bar_chart(data=df_mensal, x="data_movimento", y="contagem_transacoes")
except Transacao.exc.ConsultaInvalida as e:
    f"Período do mês {mes}/{ano} sem transações para exibir"
#print(df_ranking)
