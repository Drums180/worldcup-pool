import streamlit as st

st.set_page_config(page_title="Copa Mundial 2026", page_icon="🏆", layout="wide")

home = st.Page("views/home.py", title="Home", icon="🏆", default=True)
partidos_dia = st.Page("pages/6_Partidos_del_Dia.py", title="Partidos del Día", icon="🔥")
calendario = st.Page("pages/1_Calendario.py", title="Calendario", icon="📅")
mis_estadisticas = st.Page("pages/5_Mis_Estadisticas.py", title="Mis Estadísticas", icon="📈")
estadisticas = st.Page("pages/2_Estadisticas.py", title="Estadísticas", icon="📊")
equipos = st.Page("pages/3_Equipos.py", title="Equipos", icon="🎯")
prestamos = st.Page("pages/7_Prestamos.py", title="Préstamos", icon="🔄")
admin = st.Page("pages/4_Admin.py", title="Admin", icon="⚙️")

pg = st.navigation([
    home,
    partidos_dia,
    calendario,
    mis_estadisticas,
    estadisticas,
    equipos,
    prestamos,
    admin,
])
pg.run()
