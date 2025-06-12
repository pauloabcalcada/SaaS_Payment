import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, text,extract
from sqlalchemy.orm import sessionmaker
from models.tables import Cliente,Pagamentos
from models.database import engine
from datetime import datetime, timedelta
from funcs import generate_pagamentos,delete_pagamentos,categorize_status_dias_vencimento,update_status_dias_vencimento
import calendar
from io import BytesIO
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
import os


# key_decript = st.secrets["database"]["encryption_key"]

# if not os.path.exists('local_database.db'):
#     decrypt_database('encrypted_database.db', 'local_database.db', key_decript)


Session = sessionmaker(bind=engine)
session = Session()

# Streamlit app
st.title("Atualização dos dados")

tab_client, tab_pagamentos = st.tabs(["Clientes", "Pagamentos"])
# Pagamentos tab
with tab_pagamentos:

    # Add a new payment
    with st.expander("Adicionar Pagamento"):
        tab1_add_pay, tab2_add_pay = st.tabs(["Via tela", "Via carga de dados"])

        # --- VIA TELA ---
        with tab1_add_pay:
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

            # Fetch unique payment types from the Pagamentos table
            tipos_pagamento = session.query(Pagamentos.Tipo_Pagamento).distinct().all()
            tipos_pagamento = [tp[0] for tp in tipos_pagamento if tp[0]]  # Remove None values

            # If no types exist yet, provide some defaults
            if not tipos_pagamento:
                tipos_pagamento = ["Mensalidade","Evento", "Outro"]

            tipo_pagamento = st.selectbox(
                "Tipo de Pagamento",
                tipos_pagamento,
                key="tipo_pagamento"
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
                    text('TO_CHAR("Prazo_Vencimento", \'YYYY-MM\') = :year_month'),
                ).params(year_month=f"{selected_year}-{selected_month:02d}").first()

                # Store the state to indicate an existing payment or new payment details
                st.session_state["payment_action"] = {
                    "existing_payment": existing_payment,
                    "prazo_vencimento": prazo_vencimento,
                    "data_pagamento": data_pagamento,
                    "valor_pagamento": valor_pagamento,
                    "cliente": cliente,
                    "tipo_pagamento": tipo_pagamento,
                }

            # Handle existing payment actions
            if "payment_action" in st.session_state:
                payment_action = st.session_state["payment_action"]
                existing_payment = payment_action["existing_payment"]
                prazo_vencimento = payment_action["prazo_vencimento"]
                data_pagamento = payment_action["data_pagamento"]
                valor_pagamento = payment_action["valor_pagamento"]
                cliente = payment_action["cliente"]
                tipo_pagamento = payment_action["tipo_pagamento"]

                if existing_payment:
                    st.warning("Já existe um pagamento para este mês. Escolha uma ação abaixo.")
                    col1_add_pay, col2_add_pay = st.columns(2)

                    with col1_add_pay:
                        if st.button("Substituir o pagamento existente", key="replace_payment"):
                            try:
                                # Explicitly update the existing payment using an SQL query
                                # Fetch the existing payment(s) for the given month and client
                                pagamentos_to_update = session.query(Pagamentos).filter(
                                    Pagamentos.Id_empresa == cliente.Id_empresa,
                                    text('TO_CHAR("Prazo_Vencimento", \'YYYY-MM\') = :year_month'),
                                ).params(year_month=f"{selected_year}-{selected_month:02d}").all()

                                for pagamento in pagamentos_to_update:
                                    pagamento.Data_do_Pagamento = data_pagamento
                                    pagamento.Valor_da_Conta = valor_pagamento
                                    pagamento.Status_Pagamento = "Pago"
                                    pagamento.Dias_Pagamento_Vencimento = (data_pagamento - prazo_vencimento).days
                                    pagamento.Status_Dias_Vencimento = categorize_status_dias_vencimento(
                                        (prazo_vencimento - datetime.now().date()).days
                                    )
                                    pagamento.Tipo_Pagamento = tipo_pagamento

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
                                    Tipo_Pagamento = tipo_pagamento,
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
                            Tipo_Pagamento = tipo_pagamento,
                        )
                        session.add(new_pagamento)
                        session.commit()
                        st.success("Pagamento adicionado com sucesso!")
                        del st.session_state["payment_action"]  # Clear the state after action
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao adicionar pagamento: {e}")


        # --- VIA CARGA DE DADOS ---
        with tab2_add_pay:
            col1_pay_add, col2_pay_add = st.columns(2)

            # Download modelo de pagamentos
            with col1_pay_add:
                st.write("Baixar todos os pagamentos em CSV ou XLSX")
                download_format_pay = st.selectbox("Formato do arquivo", ["XLSX", "CSV"], key="download_format_pay")
                if st.button("Baixar Arquivo", key="download_file_pay"):
                    try:
                        pagamentos = session.query(Pagamentos).all()
                        pagamentos_data = [
                            {
                                "Id_pagamento": p.Id_pagamento,
                                "Id_empresa": p.Id_empresa,
                                "Nome_da_Empresa": p.Nome_da_Empresa,
                                "Prazo_Vencimento": p.Prazo_Vencimento,
                                "Email": p.Email,
                                "Valor_da_Conta": p.Valor_da_Conta,
                                "Status_Pagamento": p.Status_Pagamento,
                                "Status_Dias_Vencimento": p.Status_Dias_Vencimento,
                                "Data_do_Pagamento": p.Data_do_Pagamento,
                                "Dias_Pagamento_Vencimento": p.Dias_Pagamento_Vencimento,
                                "Tipo_Pagamento": p.Tipo_Pagamento,
                            }
                            for p in pagamentos
                        ]
                        pagamentos_df = pd.DataFrame(pagamentos_data)
                        if download_format_pay == "CSV":
                            csv_buffer = BytesIO()
                            pagamentos_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                            csv_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=csv_buffer,
                                file_name="Pagamentos_add.csv",
                                mime="text/csv",
                            )
                        else:
                            xlsx_buffer = BytesIO()
                            pagamentos_df.to_excel(xlsx_buffer, index=False, engine="openpyxl")
                            xlsx_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=xlsx_buffer,
                                file_name="Pagamentos_add.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                    except Exception as e:
                        st.error(f"Erro ao exportar pagamentos: {e}")

            # Upload e processamento do arquivo
            with col2_pay_add:
                st.write("Importar pagamentos via CSV ou Excel")
                uploaded_file = st.file_uploader(
                    "Selecione o arquivo (CSV ou Excel)", type=["csv", "xlsx", "xls"], key="upload_payments"
                )

                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith(".csv"):
                            payments_df = pd.read_csv(uploaded_file, sep=None, engine="python")
                        elif uploaded_file.name.endswith((".xlsx", ".xls")):
                            payments_df = pd.read_excel(uploaded_file)

                        # Checagem das colunas obrigatórias
                        required_columns = [
                            "Id_empresa", "Nome_da_Empresa", "Prazo_Vencimento", "Email", "Valor_da_Conta",
                            "Status_Pagamento", "Status_Dias_Vencimento", "Data_do_Pagamento",
                            "Dias_Pagamento_Vencimento", "Tipo_Pagamento"
                        ]
                        missing_cols = [col for col in required_columns if col not in payments_df.columns]
                        if missing_cols:
                            st.error(f"O arquivo deve conter as colunas obrigatórias: {', '.join(missing_cols)}")
                        else:
                            # Normaliza datas
                            payments_df["Prazo_Vencimento"] = pd.to_datetime(payments_df["Prazo_Vencimento"]).dt.date
                            if "Data_do_Pagamento" in payments_df.columns:
                                payments_df["Data_do_Pagamento"] = pd.to_datetime(payments_df["Data_do_Pagamento"], errors="coerce").dt.date

                            # Verificação de pagamentos existentes
                            existing_payments = []
                            new_payments = []
                            for _, row in payments_df.iterrows():
                                # Chave composta: Id_empresa, mês/ano de Prazo_Vencimento, Tipo_Pagamento
                                prazo_vencimento = row["Prazo_Vencimento"]
                                tipo_pagamento = row["Tipo_Pagamento"]
                                id_empresa = row["Id_empresa"]
                                month = prazo_vencimento.month
                                year = prazo_vencimento.year

                                existing = session.query(Pagamentos).filter(
                                    Pagamentos.Id_empresa == id_empresa,
                                    Pagamentos.Tipo_Pagamento == tipo_pagamento,
                                    extract('year', Pagamentos.Prazo_Vencimento) == year,
                                    extract('month', Pagamentos.Prazo_Vencimento) == month
                                ).first()

                                if existing:
                                    existing_payments.append({
                                        "Id_empresa": id_empresa,
                                        "Nome_da_Empresa": row["Nome_da_Empresa"],
                                        "Prazo_Vencimento": prazo_vencimento,
                                        "Tipo_Pagamento": tipo_pagamento,
                                        "Id_pagamento": existing.Id_pagamento
                                    })
                                else:
                                    new_payments.append(row)

                            # Se houver pagamentos existentes, exibe e pede confirmação
                            if existing_payments:
                                st.warning("Pagamentos já existentes encontrados para os seguintes registros:")
                                st.dataframe(pd.DataFrame(existing_payments),hide_index=True)
                                if st.button("Substituir pagamentos existentes e adicionar novos", key="replace_existing_payments"):
                                    try:
                                        # Substitui pagamentos existentes
                                        for ep in existing_payments:
                                            pagamento = session.query(Pagamentos).filter_by(Id_pagamento=ep["Id_pagamento"]).first()
                                            if pagamento:
                                                row = payments_df[
                                                    (payments_df["Id_empresa"] == ep["Id_empresa"]) &
                                                    (payments_df["Prazo_Vencimento"] == ep["Prazo_Vencimento"]) &
                                                    (payments_df["Tipo_Pagamento"] == ep["Tipo_Pagamento"])
                                                ].iloc[0]
                                                pagamento.Nome_da_Empresa = row["Nome_da_Empresa"]
                                                pagamento.Prazo_Vencimento = row["Prazo_Vencimento"]
                                                pagamento.Email = row["Email"]
                                                pagamento.Valor_da_Conta = float(row["Valor_da_Conta"]) if pd.notnull(row["Valor_da_Conta"]) else None
                                                pagamento.Status_Pagamento = row["Status_Pagamento"]
                                                pagamento.Status_Dias_Vencimento = row["Status_Dias_Vencimento"]
                                                pagamento.Data_do_Pagamento = row["Data_do_Pagamento"]
                                                pagamento.Dias_Pagamento_Vencimento = int(row["Dias_Pagamento_Vencimento"]) if pd.notnull(row["Dias_Pagamento_Vencimento"]) else None
                                                pagamento.Tipo_Pagamento = row["Tipo_Pagamento"]
                                        # Adiciona novos pagamentos
                                        for row in new_payments:
                                            novo_pagamento = Pagamentos(
                                                Id_empresa=int(row["Id_empresa"]),
                                                Nome_da_Empresa=row["Nome_da_Empresa"],
                                                Prazo_Vencimento=row["Prazo_Vencimento"],
                                                Email=row["Email"],
                                                Valor_da_Conta=float(row["Valor_da_Conta"]) if pd.notnull(row["Valor_da_Conta"]) else None,
                                                Status_Pagamento=row["Status_Pagamento"],
                                                Status_Dias_Vencimento=row["Status_Dias_Vencimento"],
                                                Data_do_Pagamento=data_pagamento,
                                                Dias_Pagamento_Vencimento=int(row["Dias_Pagamento_Vencimento"]) if pd.notnull(row["Dias_Pagamento_Vencimento"]) else None,
                                                Tipo_Pagamento=row["Tipo_Pagamento"],
                                            )
                                            session.add(novo_pagamento)
                                        session.commit()
                                        st.success("Pagamentos substituídos/adicionados com sucesso!")
                                    except Exception as e:
                                        session.rollback()
                                        st.error(f"Erro ao substituir/adicionar pagamentos: {e}")
                                if st.button("Cancelar operação", key="cancel_replace_payments"):
                                    session.rollback()
                                    st.info("Operação cancelada. Nenhuma alteração foi feita.")
                            else:
                                # Se não houver conflitos, adiciona todos como novos pagamentos
                                try:
                                    for _, row in payments_df.iterrows():
                                        novo_pagamento = Pagamentos(
                                            Id_empresa=row["Id_empresa"],
                                            Nome_da_Empresa=row["Nome_da_Empresa"],
                                            Prazo_Vencimento=row["Prazo_Vencimento"],
                                            Email=row["Email"],
                                            Valor_da_Conta=row["Valor_da_Conta"],
                                            Status_Pagamento=row["Status_Pagamento"],
                                            Status_Dias_Vencimento=row["Status_Dias_Vencimento"],
                                            Data_do_Pagamento=row["Data_do_Pagamento"],
                                            Dias_Pagamento_Vencimento=row["Dias_Pagamento_Vencimento"],
                                            Tipo_Pagamento=row["Tipo_Pagamento"],
                                        )
                                        session.add(novo_pagamento)
                                    session.commit()
                                    st.success("Pagamentos adicionados com sucesso!")
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"Erro ao adicionar pagamentos: {e}")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Erro ao importar pagamentos: {e}")        

    # View all payments
    with st.expander("Visualizar Pagamentos"):
        try:
            update_status_dias_vencimento(session)
            # Use pandas to read the SQL query into a DataFrame
            # Fetch all payments using ORM and convert to DataFrame
            pagamentos = session.query(Pagamentos).all()
            pagamentos_data = [
                {
                    "Nome_da_Empresa": p.Nome_da_Empresa,
                    "Prazo_Vencimento": p.Prazo_Vencimento,
                    "Data_do_Pagamento": p.Data_do_Pagamento,
                    "Status_Pagamento": p.Status_Pagamento,
                    "Status_Dias_Vencimento": p.Status_Dias_Vencimento,
                    "Valor_da_Conta": p.Valor_da_Conta,
                    "Tipo_Pagamento": p.Tipo_Pagamento,
                }
                for p in pagamentos
            ]
            pagamentos_df = pd.DataFrame(pagamentos_data)
            pagamentos_df = pagamentos_df.loc[:, [
                "Nome_da_Empresa",
                "Prazo_Vencimento",
                "Data_do_Pagamento",
                "Status_Pagamento",
                "Status_Dias_Vencimento",
                "Valor_da_Conta",
                "Tipo_Pagamento"
            ]]
            # Ordena por Nome da Empresa e Prazo do Vencimento
            pagamentos_df = pagamentos_df.sort_values(by=["Nome_da_Empresa", "Prazo_Vencimento"], ascending=[True, True])
            # Rename columns for better readability
            pagamentos_df.columns = [
                "Nome da Empresa",
                "Prazo do Vencimento",
                "Data do Pagamento",
                "Status do Pagamento",
                "Status do Vencimento",
                "Valor do Pagamento",
                "Tipo de Pagamento"
            ]

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
                    st.rerun()  # Refresh the page to reflect changes
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
                        text('TO_CHAR("Prazo_Vencimento", \'YYYY-MM\') = :year_month'),
                    ).params(year_month=f"{selected_year}-{selected_month:02d}").delete(synchronize_session=False)
                    session.commit()
                    st.success("Pagamentos do mês selecionado foram deletados com sucesso!")
                    st.rerun()  # Refresh the page to reflect changes
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
                download_format = st.selectbox("Formato do arquivo", ["XLSX","CSV"], key="download_format_add")
                if st.button("Baixar Arquivo", key="download_file_add"):
                    try:
                        # Fetch all clients from the database using ORM
                        clientes = session.query(Cliente).all()
                        # Convert ORM objects to a list of dicts for DataFrame
                        clientes_data = [
                            {
                                "Nome_da_Empresa": c.Nome_da_Empresa,
                                "CNPJ": c.CNPJ,
                                "Telefone": c.Telefone,
                                "Email": c.Email,
                                "Endereco": c.Endereco,
                                "Dia_do_Vencimento": c.Dia_do_Vencimento,
                                "Valor_da_Conta": c.Valor_da_Conta,
                            }
                            for c in clientes
                        ]
                        clientes_df = pd.DataFrame(clientes_data)

                        file_name = "Clientes_add"
                        if download_format == "CSV":
                            csv_buffer = BytesIO()
                            clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                            csv_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=csv_buffer,
                                file_name=f"{file_name}.csv",
                                mime="text/csv",
                            )
                        else:  # XLSX
                            xlsx_buffer = BytesIO()
                            clientes_df.to_excel(xlsx_buffer, index=False, engine="openpyxl")
                            xlsx_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=xlsx_buffer,
                                file_name=f"{file_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
                                    Nome_da_Empresa=str(row["Nome_da_Empresa"]),
                                    CNPJ=str(row["CNPJ"]),
                                    Telefone=str(row["Telefone"]),
                                    Email=str(row["Email"]),
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
            clientes = session.query(Cliente).all()
            # Convert ORM objects to a list of dicts for DataFrame
            clientes_data = [
                {
                    "Nome_da_Empresa": c.Nome_da_Empresa,
                    "CNPJ": c.CNPJ,
                    "Telefone": c.Telefone,
                    "Email": c.Email,
                    "Endereco": c.Endereco,
                    "Dia_do_Vencimento": c.Dia_do_Vencimento,
                    "Valor_da_Conta": c.Valor_da_Conta,
                }
                for c in clientes
            ]
            clientes_df = pd.DataFrame(clientes_data)
            clientes_df = clientes_df.loc[:, ["Nome_da_Empresa", "CNPJ", "Telefone", "Email", "Endereco", "Dia_do_Vencimento", "Valor_da_Conta"]]
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

    with col1_update:
        st.write("Baixar todos os clientes em CSV ou XLSX")
        download_format_update = st.selectbox("Formato do arquivo", ["XLSX","CSV"], key="download_format_update")
        if st.button("Baixar Arquivo", key="download_file_update"):  
            try:
                # Fetch all clients from the database using ORM
                clientes = session.query(Cliente).all()
                # Convert ORM objects to a list of dicts for DataFrame
                clientes_data = [
                    {
                        "Id_empresa": c.Id_empresa,
                        "Nome_da_Empresa": c.Nome_da_Empresa,
                        "CNPJ": c.CNPJ,
                        "Telefone": c.Telefone,
                        "Email": c.Email,
                        "Endereco": c.Endereco,
                        "Dia_do_Vencimento": c.Dia_do_Vencimento,
                        "Valor_da_Conta": c.Valor_da_Conta,
                    }
                    for c in clientes
                ]
                clientes_df = pd.DataFrame(clientes_data)

                if download_format_update == "CSV":
                    csv_buffer = BytesIO()
                    clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                    csv_buffer.seek(0)
                    st.download_button(
                        label="Clique para baixar",
                        data=csv_buffer,
                        file_name="Clientes_update.csv",
                        mime="text/csv",
                    )
                else:  # XLSX
                    xlsx_buffer = BytesIO()
                    clientes_df.to_excel(xlsx_buffer, index=False, engine="openpyxl")
                    xlsx_buffer.seek(0)
                    st.download_button(
                        label="Clique para baixar",
                        data=xlsx_buffer,
                        file_name="Clientes_update.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
                st.write("Baixar modelo de CSV ou XLSX para exclusão")
                download_format_delete = st.selectbox("Formato do arquivo", ["XLSX", "CSV"], key="download_format_delete")
                if st.button("Baixar Arquivo", key="download_file_delete"):
                    try:
                        # Fetch all clients from the database using ORM
                        clientes = session.query(Cliente).all()
                        # Convert ORM objects to a list of dicts for DataFrame
                        clientes_data = [
                            {
                                "Id_empresa": c.Id_empresa,
                                "Nome_da_Empresa": c.Nome_da_Empresa,
                                "CNPJ": c.CNPJ,
                            }
                            for c in clientes
                        ]
                        clientes_df = pd.DataFrame(clientes_data)

                        if download_format_delete == "CSV":
                            csv_buffer = BytesIO()
                            clientes_df.to_csv(csv_buffer, index=False, encoding="utf-8")
                            csv_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=csv_buffer,
                                file_name="Clientes_delete.csv",
                                mime="text/csv",
                            )
                        else:  # XLSX
                            xlsx_buffer = BytesIO()
                            clientes_df.to_excel(xlsx_buffer, index=False, engine="openpyxl")
                            xlsx_buffer.seek(0)
                            st.download_button(
                                label="Clique para baixar",
                                data=xlsx_buffer,
                                file_name="Clientes_delete.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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


