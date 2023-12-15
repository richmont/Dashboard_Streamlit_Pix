import pandas as pd
import io
from datetime import datetime

class ParserRelatorioSITEF():
    def __init__(self, csv_conteudo:io.StringIO) -> None:
        self.df = pd.read_csv(csv_conteudo, sep=";")
        self._filtrar_colunas()
        self._converter_datetime()
        self._filtrar_transacoes_efetuadas()
        self.df["Operador"] = self.df["Operador"].astype(int)
        
    def _filtrar_colunas(self):
        self.df = self.df[["Data", "Hora", "Pdv", "Transacao", "Operador", "Estado Transacao", "Nsu"]]
        
    def _converter_datetime(self):
        """Gera a coluna "Datetime e converte para um objeto datetime mais versátil que string
        """
        
        self.df['Datetime'] = self.df.apply(lambda x: f"{x['Data']} {x['Hora']}", axis=1)
        self.df['Datetime'] = self.df.apply(lambda x: datetime.strptime(f"{x['Datetime']}", "%d/%m/%Y %H:%M:%S"), axis=1)
    
    def _filtrar_transacoes_efetuadas(self):
        """Descarta todas as transações que falharam ou que foram em outra forma de pagamento senão pix
        """
        self.df = self.df[self.df["Estado Transacao"] == "Efetuada PDV"]
        self.df = self.df[self.df["Transacao"] == "Compra Pix"]


class ParserPlanilhaOperadores():
    def __init__(self, planilha) -> None:
        self.df = pd.read_csv(planilha, sep=";", usecols=['Código', 'Nome', 'Logname'], encoding = 'cp1252')


    
if __name__ == "__main__":
    pass
    