import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from models.tables import Configuracoes
from models.database import engine
from funcs import send_email,decrypt_database



key_decript = st.secrets["database"]["encryption_key"]

# Decrypt the database file
decrypt_database('encrypted_database.db', 'local_database.db', key_decript) 


# Create a new session
Session = sessionmaker(bind=engine)
session = Session()



# Load or initialize parameters
def load_parametro(nome_parametro):
    parametro = session.query(Configuracoes).filter_by(Nome_Parametro=nome_parametro).first()
    if parametro:
        # Handle boolean values explicitly for "use_tls"
        if nome_parametro == "use_tls":
            return parametro.Valor_Atual == "Yes"  # Return True if "Yes", False otherwise
        return parametro.Valor_Atual
    else:
        return st.error(f"Parâmetro '{nome_parametro}' não encontrado no banco de dados.")

def save_parametro(nome_parametro, valor_atual):
    parametro = session.query(Configuracoes).filter_by(Nome_Parametro=nome_parametro).first()
    if nome_parametro == "use_tls":
        valor_atual = "Yes" if valor_atual else "No"  # Convert boolean to "Yes"/"No"
    if parametro:
        parametro.Valor_Atual = str(valor_atual)
        session.commit()

# Streamlit app
st.title("Sistema de Alertas e Configurações de Remetente")

# Tabs for configuration
tab_alertas, tab_remetente, tab_mensagens = st.tabs(["Alertas", "Dados do Remetente", "Mensagens Personalizadas"])

# ==================== Tab for Alerts ====================
with tab_alertas:
    st.header("Configurações de Alertas Personalizados")

    # Load parameters from the database
    dias_alerta_1 = st.number_input(
        "Dias para o primeiro alerta (antes do vencimento)",
        min_value=1, value=int(load_parametro("dias_alerta_1")), step=1
    )
    dias_alerta_2 = st.number_input(
        "Dias para o segundo alerta (antes do vencimento)",
        min_value=1, value=int(load_parametro("dias_alerta_2")), step=1
    )
    periodicidade_apos = st.number_input(
        "Periodicidade para alertas após o vencimento (em dias)",
        min_value=1, value=int(load_parametro("periodicidade_apos")), step=1
    )

    if st.button("Salvar Configurações de alertas"):
        # Save parameters when the user changes them
        save_parametro("dias_alerta_1", dias_alerta_1)
        save_parametro("dias_alerta_2", dias_alerta_2)
        save_parametro("periodicidade_apos", periodicidade_apos)
        st.success("Configurações dos alertas salvas com sucesso!")

# ==================== Tab for Sender Data ====================
with tab_remetente:
    st.header("Configurações do Remetente")

    remetente_email = st.text_input(
        "Email do Remetente", value=load_parametro("remetente_email")
    )
    remetente_password = st.text_input(
        "Senha", type="password", value=load_parametro("remetente_password")
    )
    smtp_server = st.text_input(
        "Servidor SMTP", value=load_parametro("smtp_server")
    )
    smtp_port = st.number_input(
        "Porta SMTP", value=int(load_parametro("smtp_port")), step=1
    )
    use_tls = st.checkbox(
        "Usar TLS", value=load_parametro("use_tls")  # Load as boolean
    )

    if st.button("Salvar Configurações do Remetente"):
        # Save parameters when the user changes them
        save_parametro("remetente_email", remetente_email)
        save_parametro("remetente_password", remetente_password)
        save_parametro("smtp_server", smtp_server)
        save_parametro("smtp_port", smtp_port)
        save_parametro("use_tls", use_tls)
        st.success("Configurações do remetente salvas com sucesso!")

# ==================== Tab for Custom Messages ====================
with tab_mensagens:
    st.header("Assunto, Mensagem e Simulação do E-mail")

    assunto_antes = st.text_input(
        "Assunto do Alerta Antes do Vencimento", value=load_parametro("assunto_antes")
    )
    mensagem_antes = st.text_area(
        "Mensagem do Alerta Antes do Vencimento", value=load_parametro("mensagem_antes")
    )

    destinatario_antes = st.text_input("Destinatário do E-mail (Antes do Vencimento)", "destinatario@exemplo.com")


    assunto_dia = st.text_input(
        "Assunto do Alerta no Dia do Vencimento", value=load_parametro("assunto_dia")
    )
    mensagem_dia = st.text_area(
        "Mensagem do Alerta no Dia do Vencimento", value=load_parametro("mensagem_dia")
    )
    assunto_pos = st.text_input(
        "Assunto do Alerta Após o Vencimento", value=load_parametro("assunto_pos")
    )
    mensagem_pos = st.text_area(
        "Mensagem do Alerta Após o Vencimento", value=load_parametro("mensagem_pos")
    )

    if st.button("Salvar Mensagens Personalizadas"):
        # Save parameters when the user changes them
        save_parametro("assunto_antes", assunto_antes)
        save_parametro("mensagem_antes", mensagem_antes)
        save_parametro("assunto_dia", assunto_dia)
        save_parametro("mensagem_dia", mensagem_dia)
        save_parametro("assunto_pos", assunto_pos)
        save_parametro("mensagem_pos", mensagem_pos)
        st.success("Mensagens personalizadas salvas com sucesso!")