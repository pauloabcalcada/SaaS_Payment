import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy.orm import sessionmaker
from models.tables import Pagamentos
from models.database import engine
from datetime import datetime
from funcs import update_status_dias_vencimento

# Initialize the database session
Session = sessionmaker(bind=engine)
session = Session()

update_status_dias_vencimento(session)

# Streamlit app for analysis
st.title("Análise de Pagamentos")

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
    ).filter(
        Pagamentos.Status_Pagamento.in_(selected_status_pagamento),
        Pagamentos.Nome_da_Empresa.in_(selected_nome_da_empresa),
        Pagamentos.Prazo_Vencimento.between(start_date, end_date),
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
        st.dataframe(pagamentos_df,hide_index=True)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")