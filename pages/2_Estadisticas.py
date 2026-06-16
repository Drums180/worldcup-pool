import matplotlib.pyplot as plt
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

fig, ax = plt.subplots(figsize=(10, 4))
for col in pivot.columns:
    ax.plot(pivot.index.tolist(), pivot[col].tolist(), marker="o", label=col)
ax.set_ylabel("Puntos")
ax.legend(loc="upper left")
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.subheader("¿Quién ha liderado en cada momento?")
leader_per_date = history_df.loc[history_df.groupby("date")["total"].idxmax()]
leader_counts = leader_per_date["persona"].value_counts().rename("Días en el primer lugar")
st.dataframe(leader_counts, use_container_width=True)
