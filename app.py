import streamlit as st

# Configuração da página
st.set_page_config(page_title="Sistema de Cobrança", layout="wide")


cadastro_clientes_page = st.Page("cadastro_clientes.py", title="Atualização dos dados", icon=":material/add_circle:")
configuracoes_page = st.Page("configuracoes.py", title="Configurações", icon=":material/settings:")
pagamentos_page = st.Page("pagamentos.py", title="Próximos Vencimentos", icon=":material/notification_important:")
analises_page = st.Page("analises.py", title="Análises", icon=":material/bar_chart:")
#atualiza_pagamentos_page = st.Page("atualiza_pagamentos.py", title="Atualizar pagamentos", icon=":material/refresh:")

if not st.user.is_logged_in:
    if st.button("Log in"):
        st.login()
else:
    if st.button("Log out"):
        st.logout()
    st.write(f"Hello, {st.user.name}!")



    pg = st.navigation(
        {"Menu":[cadastro_clientes_page, 
                configuracoes_page,
                pagamentos_page,
                analises_page,
                #atualiza_pagamentos_page
                ]
        
        })

    pg.run()


