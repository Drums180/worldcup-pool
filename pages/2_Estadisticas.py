import pandas as pd
import streamlit as st

from utils import football_data, loans, scoring, sheets

st.title("📊 Estadísticas")

try:
    fixtures_df = football_data.get_fixtures_df()
except Exception as e:
    st.error(f"No se pudo obtener el calendario desde la API: {e}")
    st.stop()

try:
    picks_df = sheets.read_picks()
except Exception as e:
    st.error(f"No se pudieron obtener los equipos desde Google Sheets: {e}")
    st.stop()
picks_long = scoring.normalize_picks(picks_df)
history_df = scoring.build_history_with_loans(fixtures_df, picks_long, loans.LOANS)

if history_df.empty:
    st.info("Aún no hay partidos finalizados.")
    st.stop()

st.subheader("Evolución del total de puntos")
pivot = history_df.pivot_table(index="date", columns="persona", values="total", aggfunc="last")
pivot.index = pd.to_datetime(pivot.index).strftime("%d-%b").map(football_data.to_spanish_date)
st.line_chart(pivot)

st.subheader("¿Quién ha liderado en cada momento?")
leader_per_date = history_df.loc[history_df.groupby("date")["total"].idxmax()]
leader_counts = leader_per_date["persona"].value_counts().rename("Días en el primer lugar")
st.dataframe(leader_counts, use_container_width=True)
