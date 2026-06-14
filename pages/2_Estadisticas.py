import pandas as pd
import streamlit as st

from utils import sheets

st.set_page_config(page_title="Estadísticas - Copa Mundial 2026", page_icon="📊", layout="wide")

st.title("📊 Estadísticas")

historial_df = sheets.read_historial()

if historial_df.empty:
    st.info(
        "Aún no hay historial guardado. Cada vez que se sincronicen resultados en la página "
        "de Admin se guardará una nueva instantánea de la tabla de posiciones."
    )
    st.stop()

historial_df = historial_df.copy()
historial_df["timestamp"] = pd.to_datetime(historial_df["timestamp"])
historial_df["total"] = pd.to_numeric(historial_df["total"], errors="coerce")

st.subheader("Evolución del total de puntos")
pivot = historial_df.pivot_table(index="timestamp", columns="persona", values="total", aggfunc="last")
pivot = pivot.sort_index().ffill()
pivot.index = pivot.index.strftime("%b %d")
st.line_chart(pivot)

st.subheader("¿Quién ha liderado en cada momento?")
leader_per_snapshot = historial_df.loc[historial_df.groupby("timestamp")["total"].idxmax()]
leader_counts = leader_per_snapshot["persona"].value_counts().rename("Veces en el primer lugar")
st.dataframe(leader_counts, use_container_width=True)

st.subheader("Última instantánea")
last_ts = historial_df["timestamp"].max()
last_snapshot = historial_df[historial_df["timestamp"] == last_ts].sort_values("total", ascending=False)
st.caption(f"Tomada el {last_ts}")
st.dataframe(
    last_snapshot[["persona", "match_points", "bonus_points", "total"]].rename(columns={
        "persona": "Persona",
        "match_points": "Puntos Partidos",
        "bonus_points": "Puntos Eliminación",
        "total": "Total",
    }),
    use_container_width=True,
    hide_index=True,
)
