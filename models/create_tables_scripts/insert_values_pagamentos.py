import datetime
import random
from calendar import monthrange
from sqlalchemy.orm import sessionmaker
from src.models.database import engine
from src.models.tables import Pagamentos, Cliente

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Define the year for generating payments
ano_selecionado = 2025

# Generate payment data
def gerar_base_pagamentos():
    linhas = []
    # Define a data limite para pagamento: 15/05 do ano selecionado
    data_limite = datetime.date(ano_selecionado, 5, 15)
    # Data de hoje para cálculo do status dos dias
    hoje = datetime.date.today()

    # Fetch all clients from the Clientes table
    clientes = session.query(Cliente).all()

    # Iterate over the clients
    for cliente in clientes:
        id_empresa = cliente.Id_empresa  # Foreign key reference
        prazo = cliente.Dia_do_Vencimento
        valor = cliente.Valor_da_Conta
        email_destinatario = cliente.Email
        nome_empresa = cliente.Nome_da_Empresa

        # Create a row for each month of the selected year
        for mes in range(1, 13):
            ultimo_dia = monthrange(ano_selecionado, mes)[1]
            dia_vencimento = prazo if prazo <= ultimo_dia else ultimo_dia
            data_vencimento = datetime.date(ano_selecionado, mes, dia_vencimento)

            # Define the payment status
            status = "Pago" if data_vencimento <= data_limite else "Pendente"

            # Calculate the difference in days between the due date and today
            diff = (data_vencimento - hoje).days
            if diff < -15:
                status_dias = "Venceu há mais de 15 dias"
            elif -15 <= diff < 0:
                status_dias = "Venceu há menos de 15 dias"
            elif 0 <= diff <= 5:
                status_dias = "Até 5 dias para o Vencimento"
            elif 5 < diff <= 15:
                status_dias = "5-15 dias para o Vencimento"
            elif 15 < diff <= 30:
                status_dias = "15-30 dias para o Vencimento"
            else:
                status_dias = "+30 dias para o Vencimento"

            # For "Pago" status, generate a random payment date
            if status == "Pago":
                delta = random.randint(-5, 5)
                data_pagamento = data_vencimento + datetime.timedelta(days=delta)
                dias_pagamento_vencimento = (data_pagamento - data_vencimento).days
            else:
                data_pagamento = None
                dias_pagamento_vencimento = None

            # Add the row to the list
            linhas.append({
                "Id_empresa": id_empresa,
                "Nome_da_Empresa": nome_empresa,
                "Prazo_Vencimento": data_vencimento,
                "Email": email_destinatario,
                "Valor_da_Conta": valor,
                "Status_Pagamento": status,
                "Status_Dias_Vencimento": status_dias,
                "Data_do_Pagamento": data_pagamento,
                "Dias_Pagamento_Vencimento": dias_pagamento_vencimento
            })

    # Insert the rows into the Pagamentos table
    for linha in linhas:
        pagamento = Pagamentos(
            Id_empresa=linha["Id_empresa"],
            Nome_da_Empresa=linha["Nome_da_Empresa"],
            Prazo_Vencimento=linha["Prazo_Vencimento"],
            Email=linha["Email"],
            Valor_da_Conta=linha["Valor_da_Conta"],
            Status_Pagamento=linha["Status_Pagamento"],
            Status_Dias_Vencimento=linha["Status_Dias_Vencimento"],
            Data_do_Pagamento=linha["Data_do_Pagamento"],
            Dias_Pagamento_Vencimento=linha["Dias_Pagamento_Vencimento"]
        )
        session.add(pagamento)

    # Commit the transaction
    try:
        session.commit()
        print("Pagamentos inseridos com sucesso!")
    except Exception as e:
        session.rollback()
        print(f"Erro ao inserir pagamentos: {e}")
    finally:
        session.close()

# Run the function
if __name__ == "__main__":
    gerar_base_pagamentos()