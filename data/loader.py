"""
Sofim Financial Dashboard - Caricamento e Preparazione Dati
"""

import streamlit as st
import pandas as pd
from utils.formatting import clean_numeric


@st.cache_data(show_spinner="Caricamento movimenti contabili...")
def load_dati(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(
        pd.io.common.BytesIO(file_bytes),
        sep=None,
        engine="python",
        dtype=str,
        encoding='latin1'
    )
    df.columns = df.columns.str.strip()
    return df


@st.cache_data(show_spinner="Caricamento mappatura conti...")
def load_mappa(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
    df.columns = df.columns.str.strip()
    return df


@st.cache_data(show_spinner="Elaborazione dati...")
def prepara_dati(dati_bytes: bytes, mappa_bytes: bytes) -> tuple[pd.DataFrame, list[str]]:
    df = load_dati(dati_bytes)
    df_mappa = load_mappa(mappa_bytes)
    warnings = []

    df.columns = df.columns.str.strip()
    df_mappa.columns = df_mappa.columns.str.strip()

    for frame, nome_f in [(df, "CSV"), (df_mappa, "Mappa")]:
        if "Codice Conto" not in frame.columns:
            candidati = [c for c in frame.columns if "COD" in c.upper() and "CONTO" in c.upper()]
            if candidati:
                frame.rename(columns={candidati[0]: "Codice Conto"}, inplace=True)
            else:
                st.error(f"Errore nel file {nome_f}: Colonna 'Codice Conto' non trovata. Colonne presenti: {list(frame.columns)}")
                st.stop()

    for frame in (df, df_mappa):
        frame["Codice Conto"] = (
            frame["Codice Conto"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        )

    df["Data Operazione"] = pd.to_datetime(df["Data Operazione"], dayfirst=True, errors="coerce")
    n_date_ko = df["Data Operazione"].isna().sum()
    if n_date_ko > 0:
        warnings.append(f"⚠️ {n_date_ko} righe con data non leggibile (ignorate).")
    df = df.dropna(subset=["Data Operazione"])

    df["Anno"] = df["Data Operazione"].dt.year.astype(int)
    df["Mese_Num"] = df["Data Operazione"].dt.month.astype(int)

    df["Importo_Netto"] = (
        df["Avere"].apply(clean_numeric) - df["Dare"].apply(clean_numeric)
    )

    mask_tecnica = df["Descrizione Causale Testata"].str.contains(
        r"CHIUSURA|APERTURA", case=False, na=False
    )
    df_reale = df[~mask_tecnica].copy()

    cols_mappa = ["Codice Conto", "Categoria"]
    if "Tipo" in df_mappa.columns:
        cols_mappa.append("Tipo")
    else:
        warnings.append("⚠️ Colonna 'Tipo' assente nella mappatura — filtri per tipo disabilitati.")
        df_mappa["Tipo"] = "N/D"
        cols_mappa.append("Tipo")

    df_final = pd.merge(df_reale, df_mappa[cols_mappa], on="Codice Conto", how="left")
    df_final["Cat_Safe"] = df_final["Categoria"].fillna("NON MAPPATO").str.upper().str.strip()

    n_no_map = (df_final["Cat_Safe"] == "NON MAPPATO").sum()
    if n_no_map > 0:
        warnings.append(f"ℹ️ {n_no_map} righe con conto non mappato (categoria = NON MAPPATO).")

    return df_final, warnings
