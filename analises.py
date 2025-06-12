import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy.orm import sessionmaker
from models.tables import Pagamentos
from models.database import engine
from datetime import datetime
from funcs import update_status_dias_vencimento
import os


# Initialize the database session
Session = sessionmaker(bind=engine)
session = Session()

st.title("Análise de Pagamentos")

tab1, tab2, tab3 = st.tabs([
    "Status do Vencimento",
    "Ranking por Empresa",
    "Evolução Mensal por Status"
])

with tab1:
    # Filters
    st.sidebar.header("Filtros")

    # Filter: Status_Pagamento
    status_pagamento_options = session.query(Pagamentos.Status_Pagamento).distinct().all()
    status_pagamento_options = [option[0] for option in status_pagamento_options]
    selected_status_pagamento = st.sidebar.multiselect(
        "Status do Pagamento", status_pagamento_options, default="Pendente"
    )

    # Filter: Periodo (start and end date)
    start_date = st.sidebar.date_input("Data Inicial", value=datetime(datetime.now().year, 1, 1))
    end_date = st.sidebar.date_input("Data Final", value=datetime.now())

    # Filter: Tipo_Pagamento
    tipo_pagamento_options = session.query(Pagamentos.Tipo_Pagamento).distinct().all()
    tipo_pagamento_options = [option[0] for option in tipo_pagamento_options]
    selected_tipo_pagamento = st.sidebar.multiselect(
        "Tipo de Pagamento", tipo_pagamento_options, default=["Mensalidade", "Evento"]
    )

    # Filter: Nome_da_Empresa
    nome_da_empresa_options = session.query(Pagamentos.Nome_da_Empresa).distinct().all()
    nome_da_empresa_options = [option[0] for option in nome_da_empresa_options]
    selected_nome_da_empresa = st.sidebar.multiselect(
        "Nome da Empresa", nome_da_empresa_options, default=nome_da_empresa_options
    )

    

    # Query the database with filters
    try:
        pagamentos_query = session.query(
            Pagamentos.Nome_da_Empresa,
            Pagamentos.Status_Dias_Vencimento,
            Pagamentos.Status_Pagamento,
            Pagamentos.Valor_da_Conta,
            Pagamentos.Prazo_Vencimento,
            Pagamentos.Tipo_Pagamento,
        ).filter(
            Pagamentos.Status_Pagamento.in_(selected_status_pagamento),
            Pagamentos.Nome_da_Empresa.in_(selected_nome_da_empresa),
            Pagamentos.Prazo_Vencimento.between(start_date, end_date),
            Pagamentos.Tipo_Pagamento.in_(selected_tipo_pagamento),
        )

        pagamentos_df = pd.read_sql(pagamentos_query.statement, session.bind)

        if not pagamentos_df.empty:
            # Group data by Status_Dias_Vencimento and calculate the sum of Valor_da_Conta
            grouped_data = pagamentos_df.groupby("Status_Dias_Vencimento")["Valor_da_Conta"].sum().reset_index()

            # Define the chronological order for Status_Dias_Vencimento
            status_order = [
                "Venceu há mais de 15 dias",
                "Venceu entre 5 e 15 dias",
                "Venceu há menos de 5 dias",
                "Na data do Vencimento",
                "5 dias ou menos para o Vencimento",
                "6-15 dias para o Vencimento",
                "16-30 dias para o Vencimento",
                "+30 dias para o Vencimento",
            ]

            # Create a bar chart using Altair with inverted axes and sorted categories
            chart = (
                alt.Chart(grouped_data)
                .mark_bar()
                .encode(
                    y=alt.Y(
                        "Status_Dias_Vencimento",
                        sort=status_order,  # Sort categories in chronological order
                        title="Status do Vencimento",  # Updated Y-axis label
                    ),
                    x=alt.X("Valor_da_Conta", title="Valor Total (R$)"),
                    tooltip=["Status_Dias_Vencimento", "Valor_da_Conta"],
                )
                .properties(title="Volume de Pagamentos por Status do Vencimento", width=800, height=400)
                .configure_axis(
                    labelFontSize=12,  # Adjust font size for better readability
                    titleFontSize=14,  # Adjust title font size
                    labelLimit=200,  # Increase the label limit to prevent truncation
                )
            )

            # Display the chart
            st.altair_chart(chart, use_container_width=True)

            # Display the filtered data
            st.subheader("Dados Filtrados")
            st.dataframe(pagamentos_df, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")

with tab2:
    # Os mesmos filtros da tab1
    # (Para evitar duplicidade, pode-se mover os filtros para fora dos tabs e usar em ambos, mas aqui segue o pedido do usuário)
    # Reutilizando as variáveis já definidas acima

    try:
        pagamentos_query2 = session.query(
            Pagamentos.Nome_da_Empresa,
            Pagamentos.Dias_Pagamento_Vencimento,
            Pagamentos.Tipo_Pagamento,
        ).filter(
            Pagamentos.Status_Pagamento.in_(selected_status_pagamento),
            Pagamentos.Nome_da_Empresa.in_(selected_nome_da_empresa),
            Pagamentos.Prazo_Vencimento.between(start_date, end_date),
            Pagamentos.Tipo_Pagamento.in_(selected_tipo_pagamento),
        )

        pagamentos_df2 = pd.read_sql(pagamentos_query2.statement, session.bind)

        if not pagamentos_df2.empty:
            # Agrupa por empresa e calcula a média dos dias de pagamento
            ranking_df = (
                pagamentos_df2.groupby("Nome_da_Empresa")["Dias_Pagamento_Vencimento"]
                .mean()
                .reset_index()
                .sort_values(by="Dias_Pagamento_Vencimento", ascending=False)
            )

            # Gráfico de barras horizontais
            chart2 = (
                alt.Chart(ranking_df)
                .mark_bar()
                .encode(
                    x=alt.X("Dias_Pagamento_Vencimento:Q", title="Média Dias Pagamento x Vencimento"),
                    y=alt.Y("Nome_da_Empresa:N", sort='-x', title="Empresa"),
                    tooltip=["Nome_da_Empresa", "Dias_Pagamento_Vencimento"],
                )
                .properties(title="Ranking por Empresa (Média Dias Pagamento x Vencimento)", width=800, height=400)
                .configure_axis(
                    labelFontSize=12,
                    titleFontSize=14,
                    labelLimit=200,
                )
            )

            st.altair_chart(chart2, use_container_width=True)
            st.subheader("Ranking Detalhado")
            st.dataframe(ranking_df, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
    except Exception as e:
        st.error(f"Erro ao carregar o ranking: {e}")

with tab3:
    # Usa os mesmos filtros das tabs anteriores
    try:
        pagamentos_query3 = session.query(
            Pagamentos.Prazo_Vencimento,
            Pagamentos.Valor_da_Conta,
            Pagamentos.Status_Pagamento
        ).filter(
            Pagamentos.Status_Pagamento.in_(selected_status_pagamento),
            Pagamentos.Nome_da_Empresa.in_(selected_nome_da_empresa),
            Pagamentos.Prazo_Vencimento.between(start_date, end_date),
            Pagamentos.Tipo_Pagamento.in_(selected_tipo_pagamento),
        )

        pagamentos_df3 = pd.read_sql(pagamentos_query3.statement, session.bind)

        if not pagamentos_df3.empty:
            # Extrai o mês/ano da data de vencimento
            pagamentos_df3["Mes"] = pd.to_datetime(pagamentos_df3["Prazo_Vencimento"]).dt.strftime("%m/%Y")
            # Agrupa por mês e status, somando o valor
            evolucao_df = (
                pagamentos_df3.groupby(["Mes", "Status_Pagamento"])["Valor_da_Conta"]
                .sum()
                .reset_index()
            )

            # Ordena os meses cronologicamente
            evolucao_df["Mes_ord"] = pd.to_datetime(evolucao_df["Mes"], format="%m/%Y")
            evolucao_df = evolucao_df.sort_values("Mes_ord")

            chart3 = (
                alt.Chart(evolucao_df)
                .mark_bar()
                .encode(
                    x=alt.X("Mes:N", sort=list(evolucao_df["Mes"].unique()), title="Mês"),
                    y=alt.Y("Valor_da_Conta:Q", title="Soma Valor da Conta"),
                    color=alt.Color("Status_Pagamento:N", title="Status do Pagamento"),
                    tooltip=["Mes", "Status_Pagamento", "Valor_da_Conta"]
                )
                .properties(title="Evolução Mensal por Status de Pagamento", width=800, height=400)
                .configure_axis(
                    labelFontSize=12,
                    titleFontSize=14,
                    labelLimit=200,
                )
            )

            st.altair_chart(chart3, use_container_width=True)
            st.subheader("Evolução Mensal Detalhada")
            st.dataframe(evolucao_df.drop(columns=["Mes_ord"]), hide_index=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
    except Exception as e:
        st.error(f"Erro ao carregar a evolução mensal: {e}")