"""
Sofim Financial Dashboard — Versione Refactorizzata
Architettura modulare: config, utils, core, views
"""

import streamlit as st
import pandas as pd

from config import MENU_ORDINE
from data.loader import prepara_dati
from core.alert_engine import calcola_alert

from views import controllo, alert, indici, ricavi, costi, clienti
from views import ce_riclassificato, stato_patrimoniale, pfn, dettaglio

# ---------------------------------------------------------------------------
# CONFIGURAZIONE PAGINA
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Sofim Dashboard - BI", layout="wide")

# ---------------------------------------------------------------------------
# SIDEBAR - CARICAMENTO DATI
# ---------------------------------------------------------------------------
st.sidebar.header("📂 Caricamento Dati")
file_dati = st.sidebar.file_uploader("1. Movimenti Contabili (CSV)", type="csv")
file_mappa = st.sidebar.file_uploader("2. Classificazione Conti (Excel)", type="xlsx")

st.sidebar.divider()
menu = st.sidebar.radio("Seleziona Analisi:", MENU_ORDINE)

# ---------------------------------------------------------------------------
# STATO INIZIALE
# ---------------------------------------------------------------------------
if not file_dati or not file_mappa:
    st.title("📈 Sofim Financial Dashboard")
    st.info("👈 Carica i file nella sidebar per iniziare l'analisi.")
    if file_dati and not file_mappa:
        st.warning("Manca il file Excel di mappatura conti (colonne: Codice Conto, Categoria, Tipo).")
    st.stop()

# ---------------------------------------------------------------------------
# CARICAMENTO E PREPARAZIONE
# ---------------------------------------------------------------------------
try:
    df_final, warnings = prepara_dati(file_dati.read(), file_mappa.read())
except ValueError as e:
    st.error(str(e))
    st.stop()

for w in warnings:
    st.sidebar.warning(w)

# ---------------------------------------------------------------------------
# BADGE ALERT SIDEBAR
# ---------------------------------------------------------------------------
try:
    tipi_badge = ["RICAVI", "COSTI"]
    df_badge = calcola_alert(df_final, 15, 30, tipi_badge)
    if not df_badge.empty:
        n_crit = len(df_badge[df_badge["Stato"] == "🔴 CRITICO"])
        n_att = len(df_badge[df_badge["Stato"] == "🟡 ATTENZIONE"])
        n_opp = len(df_badge[df_badge["Stato"] == "🟢 OPPORTUNITA"])

        if n_crit > 0:
            st.sidebar.error(f"🔴 {n_crit} critici | 🟡 {n_att} attenzione | 🟢 {n_opp} opportunita")
        elif n_att > 0:
            st.sidebar.warning(f"🟡 {n_att} attenzione | 🟢 {n_opp} opportunita")
        elif n_opp > 0:
            st.sidebar.success(f"🟢 {n_opp} opportunita | Nessun problema")
        else:
            st.sidebar.info("⚪ Nessun alert attivo")
except Exception:
    pass

# ---------------------------------------------------------------------------
# MASCHERA RICAVI (condivisa tra più pagine)
# ---------------------------------------------------------------------------
mask_ricavi = df_final["Cat_Safe"].str.contains(r"RICAV|VENDIT|ENTRAT", na=False)

# ---------------------------------------------------------------------------
# ROUTING PAGINE
# ---------------------------------------------------------------------------
PAGINE = {
    "🏠 Dashboard di Controllo": lambda: controllo.render(df_final),
    "🚨 Alert Scostamenti": lambda: alert.render(df_final),
    "📊 Scorecard Indici": lambda: indici.render(df_final),
    "💰 Analisi Ricavi": lambda: ricavi.render(df_final, mask_ricavi),
    "💸 Analisi Costi": lambda: costi.render(df_final),
    "👥 Analisi Clienti": lambda: clienti.render(df_final, mask_ricavi),
    "📈 Conto Economico": lambda: ce_riclassificato.render(df_final),
    "📊 Stato Patrimoniale": lambda: stato_patrimoniale.render(df_final),
    "🏦 Posizione Finanziaria Netta": lambda: pfn.render(df_final),
    "🔍 Analisi Dettaglio": lambda: dettaglio.render(df_final),
}

# Esegui pagina selezionata
PAGINE[menu]()
