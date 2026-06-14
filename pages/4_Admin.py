import streamlit as st

from utils import football_data, scoring, sheets

st.set_page_config(page_title="Admin - Copa Mundial 2026", page_icon="⚙️", layout="wide")

st.title("⚙️ Admin")

admin_password = st.secrets.get("admin_password")
if admin_password:
    entered = st.text_input("Contraseña de admin", type="password")
    if entered != admin_password:
        st.warning("Ingresa la contraseña para continuar.")
        st.stop()

st.write(
    "Sincroniza los resultados y el calendario desde football-data.org y recalcula los puntos."
)

if st.button("🔄 Sincronizar resultados ahora", type="primary"):
    with st.spinner("Obteniendo calendario y resultados..."):
        fixtures_df = football_data.get_fixtures_df()
        resultados_df = scoring.build_resultados(fixtures_df)
        bonuses_df = scoring.build_bonuses(fixtures_df)

        sheets.write_resultados(resultados_df)
        sheets.write_bonuses(bonuses_df)

        picks_df = sheets.read_picks()
        picks_long = scoring.normalize_picks(picks_df)
        leaderboard = scoring.compute_leaderboard(picks_long, resultados_df, bonuses_df)

    st.success(f"Sincronización completa: {len(resultados_df) // 2} partidos finalizados procesados.")
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)
