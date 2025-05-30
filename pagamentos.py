import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.tables import Pagamentos
from configuracoes import load_parametro,send_email
from funcs import decrypt_database
import os

key_decript = st.secrets["database"]["encryption_key"]

if not os.path.exists('local_database.db'):
    decrypt_database('encrypted_database.db', 'local_database.db', key_decript)

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Function to fetch pending payments with due dates within 30 days
def get_pagamentos_pendentes():
    query = """
    SELECT 
        *
    FROM 
        Pagamentos
    WHERE 
        [Status_Pagamento] = 'Pendente' AND 
        [Status_Dias_Vencimento] IN ('Venceu entre 5 e 15 dias',
            'Venceu há menos de 5 dias',
            'Na data do Vencimento')
    """
    try:
        df = pd.read_sql_query(query, con=engine)
        return df
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    finally:
        session.close()


# Function to calculate email alerts based on rules and dynamic messages
def get_email_alerts():
    # Initialize session to None
    session = None
    try:
        # Load configuration parameters
        dias_alerta_1 = int(load_parametro("dias_alerta_1"))
        dias_alerta_2 = int(load_parametro("dias_alerta_2"))
        periodicidade_apos = int(load_parametro("periodicidade_apos"))

        # Load dynamic messages and subjects
        assunto_antes = load_parametro("assunto_antes")
        mensagem_antes = load_parametro("mensagem_antes")
        assunto_dia = load_parametro("assunto_dia")
        mensagem_dia = load_parametro("mensagem_dia")
        assunto_pos = load_parametro("assunto_pos")
        mensagem_pos = load_parametro("mensagem_pos")

        # Create a new session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Fetch all pending payments
        pagamentos = session.query(Pagamentos).filter(Pagamentos.Status_Pagamento == 'Pendente').all()

        # Prepare email alerts
        email_alerts = []
        for pagamento in pagamentos:
            diff = (pagamento.Prazo_Vencimento - pd.Timestamp.now().date()).days

            if diff == dias_alerta_1:
                email_alerts.append({
                    "Email": pagamento.Email,
                    "Assunto": assunto_antes,
                    "Mensagem": mensagem_antes
                        .replace("{NOME_EMPRESA}", pagamento.Nome_da_Empresa)
                        .replace("{VALOR_PAGAMENTO}", f"{pagamento.Valor_da_Conta:.2f}")
                        .replace("{DIAS_VENCIMENTO}", str(diff))
                })
            elif diff == dias_alerta_2:
                email_alerts.append({
                    "Email": pagamento.Email,
                    "Assunto": assunto_antes,
                    "Mensagem": mensagem_antes
                        .replace("{NOME_EMPRESA}", pagamento.Nome_da_Empresa)
                        .replace("{VALOR_PAGAMENTO}", f"R$ {pagamento.Valor_da_Conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        .replace("{DIAS_VENCIMENTO}", str(diff))
                })
            elif diff < 0 and abs(diff) % periodicidade_apos == 0:
                email_alerts.append({
                    "Email": pagamento.Email,
                    "Assunto": assunto_pos,
                    "Mensagem": mensagem_pos
                        .replace("{NOME_EMPRESA}", pagamento.Nome_da_Empresa)
                        .replace("{VALOR_PAGAMENTO}", f"R$ {pagamento.Valor_da_Conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        .replace("{DIAS_VENCIMENTO}", str(abs(diff)))
                })
            elif diff == 0:
                email_alerts.append({
                    "Email": pagamento.Email,
                    "Assunto": assunto_dia,
                    "Mensagem": mensagem_dia
                        .replace("{NOME_EMPRESA}", pagamento.Nome_da_Empresa)
                        .replace("{VALOR_PAGAMENTO}", f"R$ {pagamento.Valor_da_Conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                })

        # Convert the alerts to a DataFrame
        return pd.DataFrame(email_alerts)
    except Exception as e:
        if session:  # Check if session exists before rolling back
            session.rollback()
        st.error(f"Erro ao calcular alertas de e-mail: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    finally:
        if session:  # Check if session exists before closing
            session.close()
    
    

# Streamlit app for Pagamentos
def display_pagamentos_page():
    st.title("Gestão de Pagamentos")

    # Section 1: Display pending payments
    st.header("Pagamentos Pendentes com Vencimentos em até 15 dias")
    df_pendentes = get_pagamentos_pendentes()
    df_pendentes= df_pendentes.loc[:, ["Nome_da_Empresa", "Email", "Valor_da_Conta", "Prazo_Vencimento", "Status_Dias_Vencimento"]]
    df_pendentes.rename(columns={
        "Nome_da_Empresa": "Empresa",
        "Email": "E-mail",
        "Valor_da_Conta": "Valor da Conta",
        "Prazo_Vencimento": "Data de Vencimento",
        "Status_Dias_Vencimento": "Status Dias Vencimento"
    }, inplace=True)
    df_pendentes = df_pendentes.sort_values(by="Data de Vencimento", ascending=True)
    if not df_pendentes.empty:
        st.dataframe(df_pendentes,hide_index=True)
    else:
        st.info("Nenhum pagamento pendente encontrado.")

    # Section 2: Display email alerts
    st.header("Alertas de E-mail")
    df_alerts = get_email_alerts()
    if not df_alerts.empty:
        st.dataframe(df_alerts,hide_index=True)
        
        # Button to send emails
        if st.button("Enviar E-mails para Todos os Alertas"):
            # Load sender configurations
            remetente_email = load_parametro("remetente_email")
            remetente_password = load_parametro("remetente_password")
            smtp_server = load_parametro("smtp_server")
            smtp_port = int(load_parametro("smtp_port"))
            use_tls = load_parametro("use_tls")

            # Iterate through the alerts and send emails
            for _, alert in df_alerts.iterrows():
                resultado = send_email(
                    remetente_email,
                    remetente_password,
                    smtp_server,
                    smtp_port,
                    use_tls,
                    alert["Email"],
                    alert["Assunto"],
                    alert["Mensagem"]
                )
                st.info(f"E-mail enviado para {alert['Email']}: {resultado}")
    else:
        st.info("Nenhum alerta de e-mail a ser enviado.")

display_pagamentos_page()