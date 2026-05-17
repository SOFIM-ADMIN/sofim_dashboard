"""
Sofim Financial Dashboard - Pagina Analisi Dettaglio (Moviola Contabile)
"""

import streamlit as st
import pandas as pd
from utils.formatting import clean_numeric


def render(df_final: pd.DataFrame) -> None:
    st.title("🔍 Analisi Dettaglio Movimenti")
    st.info("Utilizza i filtri per navigare nei dettagli analitici di ogni singola registrazione.")

    c1, c2, c3 = st.columns(3)

    with c1:
        anni = sorted(df_final["Anno"].unique(), reverse=True)
        anno_sel = st.selectbox("Seleziona Anno", anni, key="det_anno")

    with c2:
        categorie = sorted(df_final["Cat_Safe"].unique())
        cat_sel = st.selectbox("Filtra per Categoria", ["TUTTE"] + categorie, key="det_cat")

    df_filtered = df_final[df_final["Anno"] == anno_sel].copy()
    if cat_sel != "TUTTE":
        df_filtered = df_filtered[df_filtered["Cat_Safe"] == cat_sel]

    with c3:
        conti = sorted(df_filtered["Descrizione Conto"].unique())
        conto_sel = st.selectbox("Seleziona Conto Specifico", ["TUTTI"] + conti, key="det_conto")

    if conto_sel != "TUTTI":
        df_filtered = df_filtered[df_filtered["Descrizione Conto"] == conto_sel]

    tot_dare = df_filtered["Dare"].apply(clean_numeric).sum()
    tot_avere = df_filtered["Avere"].apply(clean_numeric).sum()
    saldo = tot_avere - tot_dare

    k1, k2, k3 = st.columns(3)
    k1.metric("Totale Dare", f"€ {tot_dare:,.2f}")
    k2.metric("Totale Avere", f"€ {tot_avere:,.2f}")
    k3.metric("Saldo Netto", f"€ {saldo:,.2f}", delta_color="off")

    st.divider()

    if not df_filtered.empty:
        df_view = df_filtered.sort_values("Data Operazione", ascending=False).copy()
        df_view["Data_Fmt"] = df_view["Data Operazione"].dt.strftime("%d/%m/%Y")
        df_view["Dare"] = df_view["Dare"].apply(clean_numeric)
        df_view["Avere"] = df_view["Avere"].apply(clean_numeric)
        df_view["Importo"] = df_view["Avere"] - df_view["Dare"]

        cols_base = ["Data_Fmt", "Codice Conto", "Descrizione Conto", "Descrizione Causale Testata", "Dare", "Avere", "Importo"]
        for col in ["Ragione Sociale", "Numero Documento", "Descrizione Riga"]:
            if col in df_view.columns:
                cols_base.insert(4, col)

        st.dataframe(
            df_view[cols_base].style.format({"Dare": "€ {:,.2f}", "Avere": "€ {:,.2f}", "Importo": "€ {:,.2f}"}),
            use_container_width=True, hide_index=True
        )

        csv = df_view[cols_base].to_csv(index=False).encode('latin1')
        st.download_button(
            label="📥 Esporta questa vista in CSV",
            data=csv,
            file_name=f"estratto_conto_{anno_sel}_{cat_sel}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Nessun movimento trovato per i filtri selezionati.")
