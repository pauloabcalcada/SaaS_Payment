import streamlit as st

# Configuração da página
st.set_page_config(page_title="Ecofuture", layout="wide")
st.logo("https://static.wixstatic.com/media/e2c1bb_0089a806f76e4f13849e3dc66ab3c7de~mv2.png/v1/crop/x_0,y_0,w_855,h_402/fill/w_266,h_125,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/eco.png",  
        size="large", 
        link="https://www.ecofuturebrasil.com", icon_image=None)

pagamentos_page = st.Page("pagamentos.py", title="Próximos Vencimentos", icon=":material/notification_important:",default=True)
analises_page = st.Page("analises.py", title="Análises", icon=":material/bar_chart:",default=False)
cadastro_clientes_page = st.Page("cadastro_clientes.py", title="Atualização dos dados", icon=":material/add_circle:",default=False)
configuracoes_page = st.Page("configuracoes.py", title="Configurações", icon=":material/settings:",default=False)


# if not st.user.is_logged_in:
#     if st.button("Log in"):
#         st.login()
# else:
#     if st.button("Log out"):
#         st.logout()
#     st.write(f"Hello, {st.user.name}!")



pg = st.navigation(
    {"Menu":[
            pagamentos_page,
            analises_page,
            cadastro_clientes_page, 
            configuracoes_page
            ]
    
    })

pg.run()


