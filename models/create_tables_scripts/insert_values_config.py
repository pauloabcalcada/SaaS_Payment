from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from models.tables import Configuracoes

# Database configuration
DATABASE_URL = (
    "mssql+pyodbc://fish-storm-app-server-admin:m67A$nxUGYc4n8my@fish-storm-app-server.database.windows.net:1433/fish-storm-app-database"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=900"
)

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL)


# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Parameters from configuracoes.py
parametros = {
    "dias_alerta_1": 5,
    "dias_alerta_2": 1,
    "alerta_no_dia": 0,
    "periodicidade_apos": 2,
    "assunto_antes": "Aviso de Pagamento Pendente",
    "mensagem_antes": "Olá, {NOME_EMPRESA}! Seu pagamento de {VALOR_PAGAMENTO} está programado para vencer em {DIAS_VENCIMENTO} dias. Por favor, verifique suas pendências.",
    "assunto_dia": "Pagamento Vence Hoje",
    "mensagem_dia": "Olá, {NOME_EMPRESA}, hoje é o dia do vencimento do seu pagamento de {VALOR_PAGAMENTO}. Por favor, regularize sua situação.",
    "assunto_pos": "Pagamento Vencido",
    "mensagem_pos": "Olá, {NOME_EMPRESA}! Seu pagamento de {VALOR_PAGAMENTO} venceu há {DIAS_VENCIMENTO} dias. Por favor, regularize sua situação o quanto antes.",
    "remetente_email": "exemplo@dominio.com",
    "remetente_password": "",
    "smtp_server": "smtp.dominio.com",
    "smtp_port": 587,
    "use_tls": True,
}

# Insert or update parameters in the Configuracoes table
for nome_parametro, valor_atual in parametros.items():
    # Check if the parameter already exists
    parametro = session.query(Configuracoes).filter_by(Nome_Parametro=nome_parametro).first()
    if parametro:
        # Update the existing parameter
        parametro.Valor_Atual = str(valor_atual)
    else:
        # Insert a new parameter
        new_parametro = Configuracoes(Nome_Parametro=nome_parametro, Valor_Atual=str(valor_atual))
        session.add(new_parametro)

# Commit the changes
try:
    session.commit()
    print("Configurações inseridas/atualizadas com sucesso!")
except Exception as e:
    session.rollback()
    print(f"Erro ao inserir/atualizar configurações: {e}")
finally:
    session.close()