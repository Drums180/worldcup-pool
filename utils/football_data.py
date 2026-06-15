from typing import Optional

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"  # FIFA World Cup

FINISHED_STATUSES = {"FINISHED"}

# football-data.org "stage" -> our stage names
STAGE_MAP = {
    "GROUP_STAGE": "Grupos",
    "LAST_32": "Dieciseisavos",
    "LAST_16": "Octavos",
    "QUARTER_FINALS": "Cuartos",
    "SEMI_FINALS": "Semifinal",
    "THIRD_PLACE": "Tercer Lugar",
    "FINAL": "Final",
}

# football-data.org match status -> Spanish label
STATUS_MAP = {
    "SCHEDULED": "Programado",
    "TIMED": "Programado",
    "POSTPONED": "Postergado",
    "IN_PLAY": "En juego",
    "PAUSED": "Pausado",
    "SUSPENDED": "Suspendido",
    "FINISHED": "Finalizado",
    "CANCELLED": "Cancelado",
    "AWARDED": "Adjudicado",
}

# English month abbreviations (from strftime) -> Spanish
MONTH_ABBR_ES = {
    "Jan": "ene", "Feb": "feb", "Mar": "mar", "Apr": "abr",
    "May": "may", "Jun": "jun", "Jul": "jul", "Aug": "ago",
    "Sep": "sep", "Oct": "oct", "Nov": "nov", "Dec": "dic",
}


def to_spanish_date(text: str) -> str:
    """Replace English month abbreviations in a formatted date string with Spanish ones."""
    for en, es in MONTH_ABBR_ES.items():
        text = text.replace(en, es)
    return text


# football-data.org team names (English) -> names used in the Equipos sheet (Spanish)
TEAM_NAME_MAP = {
    "France": "Francia",
    "Australia": "Australia",
    "Iran": "Irán",
    "Uzbekistan": "Uzbekistán",
    "Qatar": "Qatar",
    "Netherlands": "Países Bajos",
    "Mexico": "México",
    "Sweden": "Suecia",
    "South Africa": "Sudáfrica",
    "Ecuador": "Ecuador",
    "Algeria": "Argelia",
    "Portugal": "Portugal",
    "Argentina": "Argentina",
    "Brazil": "Brasil",
    "Cape Verde Islands": "Cabo Verde",
    "Czechia": "Chequia",
    "Haiti": "Haití",
    "Paraguay": "Paraguay",
    "Senegal": "Senegal",
    "Croatia": "Croacia",
    "Colombia": "Colombia",
    "Iraq": "Irak",
    "Bosnia-Herzegovina": "Bosnia y Herzegovina",
    "Japan": "Japón",
    "Belgium": "Bélgica",
    "Norway": "Noruega",
    "Panama": "Panamá",
    "Austria": "Austria",
    "Spain": "España",
    "Ghana": "Ghana",
    "New Zealand": "Nueva Zelanda",
    "Ivory Coast": "Costa de Marfil",
    "Morocco": "Marruecos",
    "Tunisia": "Túnez",
    "Saudi Arabia": "Arabia Saudita",
    "Jordan": "Jordania",
    "Congo DR": "RD Congo",
    "Egypt": "Egipto",
    "Scotland": "Escocia",
    "Germany": "Alemania",
    "England": "Inglaterra",
    "South Korea": "Corea del Sur",
    "Uruguay": "Uruguay",
    "United States": "Estados Unidos",
    "Canada": "Canadá",
    "Curaçao": "Curazao",
    "Switzerland": "Suiza",
    "Turkey": "Turquía",
}


def _headers() -> dict:
    return {"X-Auth-Token": st.secrets["api_football_key"]}


def translate_team(name: Optional[str]) -> str:
    if name is None:
        return "Por confirmar"
    return TEAM_NAME_MAP.get(name, name)


def map_stage(stage: str) -> str:
    return STAGE_MAP.get(stage, stage)


def translate_status(status: str) -> str:
    return STATUS_MAP.get(status, status)


def _session_with_retries() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


@st.cache_data(ttl=300)
def fetch_matches() -> list[dict]:
    resp = _session_with_retries().get(
        f"{BASE_URL}/competitions/{COMPETITION}/matches",
        headers=_headers(),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("matches", [])


def normalize_fixtures(matches: list[dict]) -> pd.DataFrame:
    rows = []
    for m in matches:
        score = m.get("score", {})
        full_time = score.get("fullTime", {})
        winner = score.get("winner")
        rows.append({
            "fixture_id": m["id"],
            "date": m["utcDate"],
            "status": m["status"],
            "stage": map_stage(m["stage"]),
            "home_team": translate_team(m["homeTeam"]["name"]),
            "away_team": translate_team(m["awayTeam"]["name"]),
            "home_goals": full_time.get("home"),
            "away_goals": full_time.get("away"),
            "home_winner": winner == "HOME_TEAM",
            "away_winner": winner == "AWAY_TEAM",
        })
    return pd.DataFrame(rows)


def get_fixtures_df() -> pd.DataFrame:
    try:
        matches = fetch_matches()
    except requests.exceptions.RequestException:
        matches = st.session_state.get("_last_good_matches")
        if matches is None:
            raise
    else:
        st.session_state["_last_good_matches"] = matches
    return normalize_fixtures(matches)
