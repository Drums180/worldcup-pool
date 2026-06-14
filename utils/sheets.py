import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

RESULTADOS_HEADERS = ["fixture_id", "team", "opponent", "stage", "status", "result", "points"]
BONUSES_HEADERS = ["team", "stage_reached", "bonus_points"]


@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["spreadsheet_id"])


def _get_or_create_worksheet(sheet, name, headers):
    try:
        ws = sheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows=100, cols=len(headers))
        ws.append_row(headers)
    return ws


def read_picks() -> pd.DataFrame:
    sheet = get_spreadsheet()
    try:
        ws = sheet.worksheet("Picks")
    except gspread.WorksheetNotFound:
        ws = sheet.worksheet("Equipos")
    records = ws.get_all_records()
    return pd.DataFrame(records)


def read_resultados() -> pd.DataFrame:
    sheet = get_spreadsheet()
    ws = _get_or_create_worksheet(sheet, "Resultados", RESULTADOS_HEADERS)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=RESULTADOS_HEADERS)
    return df


def read_bonuses() -> pd.DataFrame:
    sheet = get_spreadsheet()
    ws = _get_or_create_worksheet(sheet, "Bonuses", BONUSES_HEADERS)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=BONUSES_HEADERS)
    return df


def write_resultados(df: pd.DataFrame):
    sheet = get_spreadsheet()
    ws = _get_or_create_worksheet(sheet, "Resultados", RESULTADOS_HEADERS)
    df = df[RESULTADOS_HEADERS]
    ws.clear()
    ws.append_row(RESULTADOS_HEADERS)
    if not df.empty:
        ws.append_rows(df.astype(str).values.tolist())


def write_bonuses(df: pd.DataFrame):
    sheet = get_spreadsheet()
    ws = _get_or_create_worksheet(sheet, "Bonuses", BONUSES_HEADERS)
    df = df[BONUSES_HEADERS]
    ws.clear()
    ws.append_row(BONUSES_HEADERS)
    if not df.empty:
        ws.append_rows(df.astype(str).values.tolist())
