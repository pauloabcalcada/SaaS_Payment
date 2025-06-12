import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct,and_, extract
from models.tables import Pagamentos,Configuracoes
from models.database import engine
from sqlalchemy.sql import text
from datetime import datetime
import calendar
import streamlit as st
from cryptography.fernet import Fernet


# functions beginning

def send_email(remetente_email, remetente_password, smtp_server, smtp_port, use_tls, destinatario, assunto, mensagem):
    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = remetente_email
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        # Connect to the SMTP server
        if use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Upgrade the connection to secure
        else:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)

        # Log in to the SMTP server
        server.login(remetente_email, remetente_password)

        # Send the email
        server.sendmail(remetente_email, destinatario, msg.as_string())
        server.quit()

        return "E-mail enviado com sucesso!"
    except Exception as e:
        return f"Erro ao enviar e-mail: {e}"



# Function to retrieve distinct Status_Dias_Vencimento for Pendente payments using ORM
def get_distinct_status_dias_vencimento():
    # Create a new session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query distinct Status_Dias_Vencimento where Status_Pagamento = 'Pendente'
        results = session.query(
            distinct(Pagamentos.Status_Dias_Vencimento)
        ).filter(
            Pagamentos.Status_Pagamento == 'Pendente'
        ).all()

        # Convert the results to a DataFrame
        df = pd.DataFrame(results, columns=["Status_Dias_Vencimento"])
        return df
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        session.close()

# Function to retrieve distinct Status_Dias_Vencimento for Pago payments using ORM
def categorize_status_dias_vencimento(days_difference):
    if days_difference < -15:
        return "Venceu há mais de 15 dias"
    elif -15 <= days_difference <= -5:
        return "Venceu entre 5 e 15 dias"
    elif -5 < days_difference <= -1:
        return "Venceu há menos de 5 dias"
    elif days_difference == 0:
        return "Na data do Vencimento"
    elif 1 <= days_difference <= 5:
        return "5 dias ou menos para o Vencimento"
    elif 5 < days_difference <= 15:
        return "6-15 dias para o Vencimento"
    elif 15 < days_difference <= 30:
        return "16-30 dias para o Vencimento"
    else:
        return "+30 dias para o Vencimento"




def generate_pagamentos(session, cliente):
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    for month in range(1, 13):  # From current month to December
        # Calculate the due date for the payment
        last_day_of_month = calendar.monthrange(current_year, month)[1]
        due_date = datetime(
            current_year, month, min(cliente.Dia_do_Vencimento, last_day_of_month)
        )

        days_difference = (due_date - current_date).days
        status_dias_vencimento = categorize_status_dias_vencimento(days_difference)
        data_do_pagamento = None
        dias_pagamento_vencimento = None
        tipo_pagamento = "Mensalidade"  # Default value

        # ORM query for existing payment in the same year, month, and Tipo_Pagamento
        existing_payment = session.query(Pagamentos).filter(
            Pagamentos.Id_empresa == cliente.Id_empresa,
            extract('year', Pagamentos.Prazo_Vencimento) == current_year,
            extract('month', Pagamentos.Prazo_Vencimento) == month,
            Pagamentos.Tipo_Pagamento == tipo_pagamento
        ).first()

        if existing_payment:
            # If the due date is in the past, update only Nome_da_Empresa and Email
            if existing_payment.Status_Pagamento == "Pago" or (
                existing_payment.Status_Pagamento == "Pendente" and due_date < current_date
            ):
                existing_payment.Nome_da_Empresa = cliente.Nome_da_Empresa
                existing_payment.Email = cliente.Email
            # If the due date is today or in the future, update all fields
            elif existing_payment.Status_Pagamento == "Pendente" and due_date >= current_date:
                existing_payment.Nome_da_Empresa = cliente.Nome_da_Empresa
                existing_payment.Email = cliente.Email
                existing_payment.Valor_da_Conta = cliente.Valor_da_Conta
                existing_payment.Prazo_Vencimento = due_date.date()
                existing_payment.Status_Pagamento = "Pendente"
                existing_payment.Status_Dias_Vencimento = status_dias_vencimento
                existing_payment.Data_do_Pagamento = data_do_pagamento
                existing_payment.Dias_Pagamento_Vencimento = dias_pagamento_vencimento
                existing_payment.Tipo_Pagamento = tipo_pagamento
        else:
            # If no record exists, insert a new payment record
            if month >= current_month:
                novo_pagamento = Pagamentos(
                    Id_empresa=cliente.Id_empresa,
                    Nome_da_Empresa=cliente.Nome_da_Empresa,
                    Prazo_Vencimento=due_date.date(),
                    Email=cliente.Email,
                    Valor_da_Conta=cliente.Valor_da_Conta,
                    Status_Pagamento="Pendente",
                    Status_Dias_Vencimento=status_dias_vencimento,
                    Data_do_Pagamento=data_do_pagamento,
                    Dias_Pagamento_Vencimento=dias_pagamento_vencimento,
                    Tipo_Pagamento=tipo_pagamento
                )
                session.add(novo_pagamento)
    session.commit()

    

# Function to delete only future payment records (Status_Pagamento == "Pendente")
def delete_pagamentos(session, id_empresa):
    session.query(Pagamentos).filter(
        Pagamentos.Id_empresa == id_empresa,
        Pagamentos.Status_Pagamento == "Pendente"
    ).delete(synchronize_session=False)


def update_status_dias_vencimento(session):
    """
    Updates the Status_Dias_Vencimento column for all records in the Pagamentos table
    where Status_Pagamento is 'Pendente'.
    """
    try:
        # Fetch all records with Status_Pagamento == 'Pendente'
        pending_payments = session.query(Pagamentos).filter(Pagamentos.Status_Pagamento == "Pendente").all()

        # Get the current date
        current_date = datetime.now().date()

        # Iterate through the fetched records and update Status_Dias_Vencimento
        for payment in pending_payments:
            prazo_vencimento = payment.Prazo_Vencimento

            # Calculate days difference
            days_difference = (prazo_vencimento - current_date).days

            # Categorize the status
            status_dias_vencimento = categorize_status_dias_vencimento(days_difference)

            # Update the record
            payment.Status_Dias_Vencimento = status_dias_vencimento

        # Commit the changes
        session.commit()
        #print("Status_Dias_Vencimento updated successfully for all pending payments.")
    except Exception as e:
        session.rollback()
        #print(f"Error updating Status_Dias_Vencimento: {e}")

# Load or initialize parameters
def load_parametro(nome_parametro):

    Session = sessionmaker(bind=engine)
    session = Session()

    parametro = session.query(Configuracoes).filter_by(Nome_Parametro=nome_parametro).first()
    if parametro:
        # Handle boolean values explicitly for "use_tls"
        if nome_parametro == "use_tls":
            return parametro.Valor_Atual == "Yes"  # Return True if "Yes", False otherwise
        return parametro.Valor_Atual
    else:
        return st.error(f"Parâmetro '{nome_parametro}' não encontrado no banco de dados.")

def save_parametro(nome_parametro, valor_atual):

    Session = sessionmaker(bind=engine)
    session = Session()

    parametro = session.query(Configuracoes).filter_by(Nome_Parametro=nome_parametro).first()
    if nome_parametro == "use_tls":
        valor_atual = "Yes" if valor_atual else "No"  # Convert boolean to "Yes"/"No"
    if parametro:
        parametro.Valor_Atual = str(valor_atual)
        session.commit()


# def decrypt_database(input_file, output_file, key):
#     """
#     Decrypts the encrypted SQLite database file.
#     :param input_file: Path to the encrypted database file.
#     :param output_file: Path to save the decrypted database file.
#     :param key: Encryption key (used for decryption).
#     """
#     # Read the encrypted database file
#     with open(input_file, 'rb') as f:
#         encrypted_data = f.read()

#     # Decrypt the data
#     fernet = Fernet(key)
#     decrypted_data = fernet.decrypt(encrypted_data)

#     # Save the decrypted data to a new file
#     with open(output_file, 'wb') as f:
#         f.write(decrypted_data)

# Load the encryption key from secrets.toml
#encryption_key = st.secrets["database"]["encryption_key"]

# Decrypt the database
#decrypt_database('local_database.db', 'decrypted_database.db', encryption_key)
