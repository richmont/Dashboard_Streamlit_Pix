# Processo de instalação para GNU/Linux

## Requisitos
- Servidor MySQL/MariaDB 10.5 ou superior
- Python 3.9 ou superior

## systemd
 Instalação como serviço do systemd, é necessário permissão de root  

 Por padrão o software fica localizado no diretório:  
 ```
 /opt/dashboard_pix
 ```
 Caso precise utilizar outra pasta, adapte o caminho também no arquivo dashboard_pix.service
 
 Os comandos abaixo irão criar a pasta /opt/dashboard_pix e dar a posse dela ao seu usuário atual, dessa maneira é preciso dar permissão de root menos vezes.  


```bash
sudo mkdir /opt/dashboard_pix/
sudo chown $USER /opt/dashboard_pix
```

 ### Criando ambiente virtual python

```bash
python3 -m venv /opt/dashboard_pix/
```

Ative o ambiente virtual

```bash
cd /opt/dashboard_pix/
source bin/activate
```
Observe que o interpretador irá mudar, com o começo exibindo:  
```bash
(dashboard_pix) usuario@maquina$
```

### Clonando os arquivos do repositório

```bash
git clone https://github.com/richmont/Dashboard_Streamlit_Pix
```

### Instalando as bibliotecas
```bash
cd Dashboard_Streamlit_Pix
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```
Aguarde a instalação de todas as bibliotecas ser concluída.

### Configurando o serviço do systemd
Copie o arquivo de configuração
```bash
cp /opt/dashboard_pix/Dashboard_Streamlit_Pix/dashboard_pix.conf /opt/dashboard_pix/
```
O conteúdo do arquivo é para definir variável de ambiente e configurar o acesso ao banco de dados.  
No arquivo há um exemplo da URL:  
```bash
DATABASE_URL=mysql://usuario:senha@127.0.0.1:3306
```
usuario e senha separados com um símbolo de dois pontos (:), após o arroba (@) o endereço e porta do servidor.  
Altere com o editor de sua preferência para conter as informações do seu servidor de banco MySQL/MariaDB.  

Copie o módulo do serviço para o diretório do systemd:  
```bash
cp /opt/dashboard_pix/Dashboard_Streamlit_Pix/dashboard_pix.service /etc/systemd/system/
```

Ative o serviço e inicie
```
sudo systemctl enable dashboard_pix.service
sudo systemctl start dashboard_pix.service
```

Acesse o servidor pelo navegador:
http://localhost:8581

Substitua "localhost" pelo IP de sua máquina, caso acesse de outros computadores