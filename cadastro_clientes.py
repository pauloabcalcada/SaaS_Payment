import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, text
from sqlalchemy.orm import sessionmaker
from models.tables import Cliente,Pagamentos
from models.database import engine
from datetime import datetime, timedelta
from funcs import generate_pagamentos,delete_pagamentos,categorize_status_dias_vencimento,update_status_dias_vencimento,decrypt_database
import calendar
from io import BytesIO
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
import os


key_decript = st.secrets["database"]["encryption_key"]

if not os.path.exists('local_database.db'):
    decrypt_database('encrypted_database.db', 'local_database.db', key_decript)


Session = sessionmaker(bind=engine)
session = Session()

# Streamlit app
st.title("Atualização dos dados")

tab_client, tab_pagamentos = st.tabs(["Clientes", "Pagamentos"])
# Pagamentos tab
with tab_pagamentos:

    # Add a new payment
    with st.expander("Adicionar Pagamento"):
        # Fetch all clients and format the selectbox options
        clients = session.query(Cliente).all()
        client_options = {f"{cliente.Id_empresa} - {cliente.Nome_da_Empresa}": cliente.Id_empresa for cliente in clients}
        selected_option = st.selectbox("Selecione o Cliente", list(client_options.keys()), key="select_cliente_pagamento")

        # Get the corresponding Id_empresa for the selected option
        selected_id = client_options[selected_option]

        # Fetch the selected client
        cliente = session.query(Cliente).filter(Cliente.Id_empresa == selected_id).first()

        # Input widget for the month of the payment
        mes_pagamento = st.selectbox(
            "Mês do Pagamento",
            [f"{month:02d}-{datetime.now().year}" for month in range(1, 13)],
            index=datetime.now().month - 1,
            key="mes_pagamento",
        )

        # Display Dia do Vencimento from the Cliente table
        dia_do_vencimento = cliente.Dia_do_Vencimento if cliente else 1
        st.number_input(
            "Dia do Vencimento",
            min_value=1,
            max_value=31,
            value=dia_do_vencimento,
            step=1,
            key="dia_do_vencimento",
            disabled=True,
        )

        # Fetch the selected month and year
        selected_month, selected_year = map(int, mes_pagamento.split("-"))

        # Fetch the corresponding Valor_da_Conta for the selected client and month
        valor_da_conta_default = cliente.Valor_da_Conta if cliente else 0.0

        # Input widget for payment details
        data_pagamento = st.date_input("Data do Pagamento", value=datetime.today(), key="data_pagamento")
        valor_pagamento = st.number_input(
            "Valor do Pagamento", format="%.2f", value=valor_da_conta_default, key="valor_pagamento"
        )

        # Check if a payment for this month already exists
        if st.button("Adicionar Pagamento", key="adicionar_pagamento"):
            # Calculate Prazo_Vencimento based on Dia_do_Vencimento
            last_day_of_month = calendar.monthrange(selected_year, selected_month)[1]
            prazo_vencimento = datetime(
                selected_year, selected_month, min(dia_do_vencimento, last_day_of_month)
            ).date()

            existing_payment = session.query(Pagamentos).filter(
                Pagamentos.Id_empresa == cliente.Id_empresa,
                text("strftime('%Y-%m', Prazo_Vencimento) = :year_month"),
            ).params(year_month=f"{selected_year}-{selected_month:02d}").first()

            # Store the state to indicate an existing payment or new payment details
            st.session_state["payment_action"] = {
                "existing_payment": existing_payment,
                "prazo_vencimento": prazo_vencimento,
                "data_pagamento": data_pagamento,
                "valor_pagamento": valor_pagamento,
                "cliente": cliente,
            }

        # Handle existing payment actions
        if "payment_action" in st.session_state:
            payment_action = st.session_state["payment_action"]
            existing_payment = payment_action["existing_payment"]
            prazo_vencimento = payment_action["prazo_vencimento"]
            data_pagamento = payment_action["data_pagamento"]
            valor_pagamento = payment_action["valor_pagamento"]
            cliente = payment_action["cliente"]

            if existing_payment:
                st.warning("Já existe um pagamento para este mês. Escolha uma ação abaixo.")
                col1_add_pay, col2_add_pay = st.columns(2)

                with col1_add_pay:
                    if st.button("Substituir o pagamento existente", key="replace_payment"):
                        try:
                            # Explicitly update the existing payment using an SQL query
                            session.execute(
                                text(
                                    """
                                    UPDATE Pagamentos
                                    SET Data_do_Pagamento = :data_pagamento,
                                        Valor_da_Conta = :valor_pagamento,
                                        Status_Pagamento = 'Pago',
                                        Dias_Pagamento_Vencimento = :dias_pagamento_vencimento,
                                        Status_Dias_Vencimento = :status_dias_vencimento
                                    WHERE Id_empresa = :id_empresa AND strftime('%Y-%m', Prazo_Vencimento) = :year_month
                                    """
                                ),
                                {
                                    "data_pagamento": data_pagamento,
                                    "valor_pagamento": valor_pagamento,
                                    "dias_pagamento_vencimento": (data_pagamento - prazo_vencimento).days,
                                    "status_dias_vencimento": categorize_status_dias_vencimento(
                                        (prazo_vencimento - datetime.now().date()).days
                                    ),
                                    "id_empresa": cliente.Id_empresa,
                                    "year_month": f"{selected_year}-{selected_month:02d}",
                                },
                            )
                            session.commit()
                            st.success("Pagamento existente substituído com sucesso!")
                            del st.session_state["payment_action"]  # Clear the state after action
                        except Exception as e:
                            session.rollback()
                            st.error(f"Erro ao substituir pagamento: {e}")

                with col2_add_pay:
                    if st.button("Adicionar outro pagamento para este mês", key="add_new_payment"):
                        try:
                            # Insert a new payment for the same month
                            new_pagamento = Pagamentos(
                                Id_empresa=cliente.Id_empresa,
                                Nome_da_Empresa=cliente.Nome_da_Empresa,
                                Prazo_Vencimento=prazo_vencimento,
                                Email=cliente.Email,
                                Valor_da_Conta=valor_pagamento,
                                Status_Pagamento="Pago",
                                Status_Dias_Vencimento=categorize_status_dias_vencimento(
                                    (prazo_vencimento - datetime.now().date()).days
                                ),
                                Data_do_Pagamento=data_pagamento,
                                Dias_Pagamento_Vencimento=(data_pagamento - prazo_vencimento).days,
                            )
                            session.add(new_pagamento)
                            session.commit()
                            st.success("Novo pagamento adicionado com sucesso!")
                            del st.session_state["payment_action"]  # Clear the state after action
                        except Exception as e:
                            session.rollback()
                            st.error(f"Erro ao adicionar novo pagamento: {e}")
            else:
                # Insert the new payment if no existing payment is found
                try:
                    new_pagamento = Pagamentos(
                        Id_empresa=cliente.Id_empresa,
                        Nome_da_Empresa=cliente.Nome_da_Empresa,
                        Prazo_Vencimento=prazo_vencimento,
                        Email=cliente.Email,
                        Valor_da_Conta=valor_pagamento,
                        Status_Pagamento="Pago",
                        Status_Dias_Vencimento=categorize_status_dias_vencimento(
                            (prazo_vencimento - datetime.now().date()).days
                        ),
                        Data_do_Pagamento=data_pagamento,
                        Dias_Pagamento_Vencimento=(data_pagamento - prazo_vencimento).days,
                    )
                    session.add(new_pagamento)
                    session.commit()
                    st.success("Pagamento adicionado com sucesso!")
                    del st.session_state["payment_action"]  # Clear the state after action
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao adicionar pagamento: {e}")
        

    # View all payments
    with st.expander("Visualizar Pagamentos"):
        try:
            update_status_dias_vencimento(session)
            # Use pandas to read the SQL query into a DataFrame
            query = "SELECT * FROM Pagamentos"
            pagamentos_df = pd.read_sql(query, con=engine).loc[:, ["Nome_da_Empresa", "Prazo_Vencimento","Data_do_Pagamento","Status_Pagamento","Status_Dias_Vencimento" ,"Valor_da_Conta"]]
            # Rename columns for better readability
            pagamentos_df.columns = ["Nome da Empresa","Prazo do Vencimento" ,"Data do Pagamento","Status do Pagamento","Status do Vencimento" ,"Valor do Pagamento"]

            if not pagamentos_df.empty:
                st.dataframe(pagamentos_df, hide_index=True)  # Display the DataFrame in Streamlit
            else:
                st.warning("Nenhum pagamento encontrado.")
        except SQLAlchemyError as e:
            st.error(f"Erro ao consultar pagamentos: {e}")
    
    # Delete a payment
    with st.expander("Deletar Pagamento"):
        # Fetch all clients and format the selectbox options
        clients = session.query(Cliente).all()
        client_options = {cliente.Nome_da_Empresa: cliente.Id_empresa for cliente in clients}
        selected_option = st.selectbox("Selecione o Cliente", list(client_options.keys()), key="delete_payment_client")

        # Get the corresponding Id_empresa for the selected Nome_da_Empresa
        selected_id = client_options[selected_option]

        # Provide two options for deletion
        delete_option = st.radio(
            "Escolha uma opção de exclusão:",
            ("Deletar todos os pagamentos pendentes", "Deletar pagamentos de um mês específico"),
            key="delete_payment_option",
        )

        if delete_option == "Deletar todos os pagamentos pendentes":
            if st.button("Deletar Pagamentos Pendentes"):
                try:
                    # Use the delete_pagamentos function to delete all pending payments
                    delete_pagamentos(session, selected_id)
                    session.commit()
                    st.success("Todos os pagamentos pendentes foram deletados com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao deletar pagamentos pendentes: {e}")

        elif delete_option == "Deletar pagamentos de um mês específico":
            # Input widget for the month of the payment
            mes_pagamento = st.selectbox(
                "Mês do Pagamento",
                [f"{month:02d}-{datetime.now().year}" for month in range(1, 13)],
                index=datetime.now().month - 1,
                key="mes_pagamento_delete",
            )

            # Fetch the selected month and year
            selected_month, selected_year = map(int, mes_pagamento.split("-"))

            if st.button("Deletar Pagamentos do Mês"):
                try:
                    # Delete payments for the selected month and year
                    session.query(Pagamentos).filter(
                        Pagamentos.Id_empresa == selected_id,
                        text("strftime('%Y-%m', Prazo_Vencimento) = :year_month"),
                    ).params(year_month=f"{selected_year}-{selected_month:02d}").delete(synchronize_session=False)
                    session.commit()
                    st.success("Pagamentos do mês selecionado foram deletados com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao deletar pagamentos do mês selecionado: {e}")
# Clientes tab
with tab_client:
    # Add a new client
    with st.expander("Adicionar Cliente"):
        tab1_add, tab2_add = st.tabs(["Via tela", "Via carga de dados"])

        with tab1_add:
            nome_da_empresa = st.text_input("Nome da Empresa",key="Nome_da_empresa_add")  # New field for Nome_da_Empresa
            cnpj = st.text_input("CNPJ",key="CNPJ_add")
            telefone = st.text_input("Telefone",key="Telefone_add")
            email = st.text_input("E-mail",key="Email_add")
            endereco = st.text_input("Endereço",key="Endereco_add")
            dia_do_vencimento = st.number_input("Dia do Vencimento", min_value=1, max_value=31, step=1,key="Dia_do_Vencimento_add")
            valor_da_conta = st.number_input("Valor da Conta", format="%.2f", key="Valor_da_Conta_add")

            # Inside the "Adicionar Cliente" button logic
            if st.button("Adicionar Cliente"):
                try:
                    # Add the new client to the Clientes table
                    new_cliente = Cliente(
                        Nome_da_Empresa=nome_da_empresa,
                        CNPJ=cnpj,
                        Telefone=telefone,
                        Email=email,
                        Endereco=endereco,
                        Dia_do_Vencimento=dia_do_vencimento,
                        Valor_da_Conta=valor_da_conta,
                    )
                    session.add(new_cliente)
                    session.commit()
                    # Retrieve the newly added client to get Id_empresa
                    new_cliente = session.query(Cliente).filter_by(
                        Nome_da_Empresa=nome_da_empresa,
                        CNPJ=cnpj,
                        Telefone=telefone,
                        Email=email,
                    ).first()

                    # Generate payments for the new client
                    generate_pagamentos(session, new_cliente)
                    session.commit()
                    st.success("Cliente e pagamentos adicionados com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao adicionar cliente e gerar pagamentos: {e}")

        with tab2_add:

        # Download a CSV of the Clientes table:
            col1_add,col2_add = st.columns(2)
            with col1_add:
                st.write("Baixa planilha modelo de carga")
                if st.button("Baixar CSV",key="download_csv_add"):
                    try:
                        # Fetch all clients from the database
                        query = "SELECT Nome_da_Empresa, CNPJ, Telefone, Email, Endereco, Dia_do_Vencimento, Valor_da_Conta FROM Clientes"
                        clientes_df = pd.read_sql(query, con=engine)

                        # Convert the DataFrame to a CSV file
                        csv_buffer = BytesIO()
                        clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                        csv_buffer.seek(0)

                        # Provide the CSV file for download
                        st.download_button(
                            label="Clique para baixar",
                            data=csv_buffer,
                            file_name="Clientes_add.csv",
                            mime="text/csv",
                        )
                    except Exception as e:
                        st.error(f"Erro ao exportar clientes: {e}")
            with col2_add:
            # Import a CSV to add new clients
                st.write("Importar novos clientes via CSV ou Excel")
                # Import a CSV or Excel file to add new clients
                uploaded_file = st.file_uploader(
                    "Selecione o arquivo (CSV ou Excel)", type=["csv", "xlsx", "xls"]
                )

                if uploaded_file is not None:
                    try:
                        # Determine the file type and read the file into a DataFrame
                        if uploaded_file.name.endswith(".csv"):
                            new_clients_df = pd.read_csv(uploaded_file, sep=None, engine="python")
                        elif uploaded_file.name.endswith((".xlsx", ".xls")):
                            new_clients_df = pd.read_excel(uploaded_file)

                        # Validate the required columns
                        required_columns = [
                            "Nome_da_Empresa",
                            "CNPJ",
                            "Telefone",
                            "Email",
                            "Endereco",
                            "Dia_do_Vencimento",
                            "Valor_da_Conta",
                        ]
                        if not all(column in new_clients_df.columns for column in required_columns):
                            st.error(
                                "O arquivo deve conter as colunas obrigatórias: "
                                + ", ".join(required_columns)
                            )
                        else:
                            # Add each row from the DataFrame to the Clientes table
                            for _, row in new_clients_df.iterrows():
                                new_cliente = Cliente(
                                    Nome_da_Empresa=row["Nome_da_Empresa"],
                                    CNPJ=row["CNPJ"],
                                    Telefone=row["Telefone"],
                                    Email=row["Email"],
                                    Endereco=row["Endereco"],
                                    Dia_do_Vencimento=int(row["Dia_do_Vencimento"]),
                                    Valor_da_Conta=float(row["Valor_da_Conta"]),
                                )
                                session.add(new_cliente)
                                session.commit()
                                # Retrieve the newly added client to get Id_empresa
                                new_cliente = session.query(Cliente).filter_by(
                                    Nome_da_Empresa=row["Nome_da_Empresa"],
                                    CNPJ=row["CNPJ"],
                                    Telefone=row["Telefone"],
                                    Email=row["Email"],
                                ).first()
                                # Generate payments for the new client
                                generate_pagamentos(session, new_cliente)
                                # Commit the changes to the database
                                session.commit()
                            st.success("Clientes e pagamentos importados com sucesso!")                        
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao importar clientes: {e}")
    # View all clients
    with st.expander("Visualizar Clientes"):
        try:
            # Use pandas to read the SQL query into a DataFrame
            query = "SELECT * FROM Clientes"
            clientes_df = pd.read_sql(query, con=engine).loc[:, ["Nome_da_Empresa", "CNPJ", "Telefone", "Email", "Endereco", "Dia_do_Vencimento", "Valor_da_Conta"]]
            # Rename columns for better readability
            clientes_df.columns = ["Nome da Empresa", "CNPJ", "Telefone", "E-mail", "Endereço", "Dia do Vencimento", "Valor da Conta"]

            if not clientes_df.empty:
                st.dataframe(clientes_df, hide_index=True)  # Display the DataFrame in Streamlit
            else:
                st.warning("Nenhum cliente encontrado.")
        except SQLAlchemyError as e:
            st.error(f"Erro ao consultar clientes: {e}")

    # Update a client
    with st.expander("Atualizar Cliente"):
        tab1_update, tab2_update = st.tabs(["Via tela", "Via carga de dados"])

        # Update client via form
        with tab1_update:
            # Fetch all clients and format the selectbox options
            clients = session.query(Cliente).all()
            client_options = {cliente.Nome_da_Empresa: cliente.Id_empresa for cliente in clients}
            selected_option = st.selectbox("Selecione o Cliente", list(client_options.keys()), key="update_client")

            # Get the corresponding Id_empresa for the selected Nome_da_Empresa
            selected_id = client_options[selected_option]

            cliente = session.query(Cliente).filter(Cliente.Id_empresa == selected_id).first()

            if cliente:
                nome_da_empresa = st.text_input("Novo Nome da Empresa", value=cliente.Nome_da_Empresa)
                cnpj = st.text_input("Novo CNPJ", value=cliente.CNPJ)
                telefone = st.text_input("Novo Telefone", value=cliente.Telefone)
                email = st.text_input("Novo E-mail", value=cliente.Email)
                endereco = st.text_input("Novo Endereço", value=cliente.Endereco)
                dia_do_vencimento = st.number_input(
                    "Novo Dia do Vencimento", min_value=1, max_value=31, step=1, value=cliente.Dia_do_Vencimento
                )
                valor_da_conta = st.number_input(
                    "Novo Valor da Conta", format="%.2f", value=cliente.Valor_da_Conta
                )

                if st.button("Atualizar Cliente"):
                    try:
                        # Update client details
                        cliente.Nome_da_Empresa = nome_da_empresa
                        cliente.CNPJ = cnpj
                        cliente.Telefone = telefone
                        cliente.Email = email
                        cliente.Endereco = endereco
                        cliente.Dia_do_Vencimento = dia_do_vencimento
                        cliente.Valor_da_Conta = valor_da_conta
                        # Delete old payment records and generate new ones
                        delete_pagamentos(session, cliente.Id_empresa)
                        generate_pagamentos(session, cliente)
                        session.commit()
                        st.success("Cliente e pagamentos atualizados com sucesso!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao atualizar cliente: {e}")
            else:
                st.warning("Cliente não encontrado.")

        # Update client via CSV
        # Update clients via file upload
    with tab2_update:
        col1_update, col2_update = st.columns(2)

        # Column to download a CSV file with all Cliente records
        with col1_update:
            st.write("Baixar todos os clientes em CSV")
            if st.button("Baixar CSV", key="download_csv_update"):  
                try:
                    # Fetch all clients from the database
                    query = "SELECT Id_empresa, Nome_da_Empresa, CNPJ, Telefone, Email, Endereco, Dia_do_Vencimento, Valor_da_Conta FROM Clientes"
                    clientes_df = pd.read_sql(query, con=engine)

                    # Convert the DataFrame to a CSV file
                    csv_buffer = BytesIO()
                    clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                    csv_buffer.seek(0)

                    # Provide the CSV file for download
                    st.download_button(
                        label="Clique para baixar",
                        data=csv_buffer,
                        file_name="Clientes_update.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Erro ao exportar clientes: {e}")

        # Column to upload a CSV or Excel file for updates
        with col2_update:
            st.write("Atualizar clientes via CSV ou Excel")
            uploaded_file = st.file_uploader(
                "Selecione o arquivo (CSV ou Excel)", type=["csv", "xlsx", "xls"], key="update_file"
            )

            if uploaded_file is not None:
                try:
                    # Determine the file type and read the file into a DataFrame
                    if uploaded_file.name.endswith(".csv"):
                        update_clients_df = pd.read_csv(uploaded_file, sep=None, engine="python")
                    elif uploaded_file.name.endswith((".xlsx", ".xls")):
                        update_clients_df = pd.read_excel(uploaded_file)

                    # Validate the required columns
                    required_columns = [
                        "Id_empresa",
                        "Nome_da_Empresa",
                        "CNPJ",
                        "Telefone",
                        "Email",
                        "Endereco",
                        "Dia_do_Vencimento",
                        "Valor_da_Conta",
                    ]
                    if not all(column in update_clients_df.columns for column in required_columns):
                        st.error(
                            "O arquivo deve conter as colunas obrigatórias: "
                            + ", ".join(required_columns)
                        )
                    else:
                        # Update each client from the DataFrame
                        for _, row in update_clients_df.iterrows():
                            cliente = session.query(Cliente).filter_by(Id_empresa=row["Id_empresa"]).first()
                            if cliente:
                                # Update client details
                                cliente.Nome_da_Empresa = row["Nome_da_Empresa"]
                                cliente.CNPJ = row["CNPJ"]
                                cliente.Telefone = row["Telefone"]
                                cliente.Email = row["Email"]
                                cliente.Endereco = row["Endereco"]
                                cliente.Dia_do_Vencimento = int(row["Dia_do_Vencimento"])
                                cliente.Valor_da_Conta = float(row["Valor_da_Conta"])

                                # Delete old payment records and generate new ones
                                delete_pagamentos(session, cliente.Id_empresa)
                                generate_pagamentos(session, cliente)
                            else:
                                st.warning(f"Cliente com Id_empresa {row['Id_empresa']} não encontrado.")

                        # Commit the changes to the database
                        session.commit()
                        st.success("Clientes e pagamentos atualizados com sucesso!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Erro ao atualizar clientes: {e}")

    # Delete a client
    with st.expander("Deletar Cliente"):
        tab1_delete, tab2_delete = st.tabs(["Via tela", "Via carga de dados"])

        # Delete client via form
        with tab1_delete:
            # Fetch all clients and format the selectbox options
            clients = session.query(Cliente).all()
            client_options = {cliente.Nome_da_Empresa: cliente.Id_empresa for cliente in clients}
            selected_option = st.selectbox("Selecione o Cliente", list(client_options.keys()), key="delete_client")

            # Get the corresponding Id_empresa for the selected Nome_da_Empresa
            selected_id = client_options[selected_option]

            if st.button("Deletar Cliente"):
                cliente = session.query(Cliente).filter(Cliente.Id_empresa == selected_id).first()
                if cliente:
                    try:
                        delete_pagamentos(session, cliente.Id_empresa)
                        session.delete(cliente)
                        session.commit()
                        st.success("Cliente deletado com sucesso!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao deletar cliente: {e}")
                else:
                    st.warning("Cliente não encontrado.")

        # Delete clients via file upload
        with tab2_delete:
            col1_delete, col2_delete = st.columns(2)

            # Column to download a CSV template for deletion
            with col1_delete:
                st.write("Baixar modelo de CSV para exclusão")
                if st.button("Baixar CSV", key="download_csv_delete"):
                    try:
                        # Fetch all clients from the database
                        query = "SELECT Id_empresa, Nome_da_Empresa, CNPJ FROM Clientes"
                        clientes_df = pd.read_sql(query, con=engine)

                        # Convert the DataFrame to a CSV file
                        csv_buffer = BytesIO()
                        clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                        csv_buffer.seek(0)

                        # Provide the CSV file for download
                        st.download_button(
                            label="Clique para baixar",
                            data=csv_buffer,
                            file_name="Clientes_delete.csv",
                            mime="text/csv",
                        )
                    except Exception as e:
                        st.error(f"Erro ao exportar clientes: {e}")

            # Column to upload a CSV or Excel file for deletion
            with col2_delete:
                st.write("Excluir clientes via CSV ou Excel")
                uploaded_file = st.file_uploader(
                    "Selecione o arquivo (CSV ou Excel)", type=["csv", "xlsx", "xls"], key="delete_file"
                )

                if uploaded_file is not None:
                    try:
                        # Determine the file type and read the file into a DataFrame
                        if uploaded_file.name.endswith(".csv"):
                            delete_clients_df = pd.read_csv(uploaded_file, sep=None, engine="python")
                        elif uploaded_file.name.endswith((".xlsx", ".xls")):
                            delete_clients_df = pd.read_excel(uploaded_file)

                        # Validate the required columns
                        required_columns = ["Id_empresa"]
                        if not all(column in delete_clients_df.columns for column in required_columns):
                            st.error(
                                "O arquivo deve conter a coluna obrigatória: " + ", ".join(required_columns)
                            )
                        else:
                            # Delete each client from the DataFrame
                            for _, row in delete_clients_df.iterrows():
                                cliente = session.query(Cliente).filter_by(Id_empresa=row["Id_empresa"]).first()
                                if cliente:
                                    try:
                                        delete_pagamentos(session, cliente.Id_empresa)
                                        session.delete(cliente)
                                    except Exception as e:
                                        st.warning(f"Erro ao deletar cliente com Id_empresa {row['Id_empresa']}: {e}")
                                else:
                                    st.warning(f"Cliente com Id_empresa {row['Id_empresa']} não encontrado.")

                            # Commit the changes to the database
                            session.commit()
                            st.success("Clientes deletados com sucesso!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao excluir clientes: {e}")


