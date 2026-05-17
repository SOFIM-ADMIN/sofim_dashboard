"""
Sofim Financial Dashboard - Pagina Posizione Finanziaria Netta
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import MESI_NOMI
from utils.formatting import clean_numeric, color_pfn_val, style_delta


def render(df_final: pd.DataFrame) -> None:
    st.title("🏦 BI - Posizione Finanziaria Netta (PFN)")

    anni = sorted(df_final["Anno"].unique())
    if not anni:
        st.warning("Nessun dato disponibile.")
        return

    anno_sel = st.selectbox("Seleziona Anno", anni, index=len(anni)-1, key="pfn_anno")

    df_pfn = df_final[df_final["Anno"] == anno_sel].copy()
    df_pfn["Saldo_Monetario"] = df_pfn["Dare"].apply(clean_numeric) - df_pfn["Avere"].apply(clean_numeric)

    def mappa_pfn(tipo):
        tipo = str(tipo).upper().strip()
        if tipo == "DL": return "Disponibilita Liquide"
        if tipo == "BANCHE": return "Banche c/c"
        if tipo == "FIN": return "Finanziamenti (Passivi)"
        return None

    df_pfn["Macro_PFN"] = df_pfn["Tipo"].apply(mappa_pfn)
    df_pfn = df_pfn.dropna(subset=["Macro_PFN"])

    pivot_pfn = df_pfn.pivot_table(
        index="Macro_PFN", columns="Mese_Num", values="Saldo_Monetario", aggfunc="sum"
    ).reindex(columns=range(1, 13), fill_value=0)

    pfn_mensile = pivot_pfn.cumsum(axis=1)
    totale_pfn = pfn_mensile.sum(axis=0)
    pfn_mensile.loc["POSIZIONE FINANZIARIA NETTA"] = totale_pfn
    var_mensile = totale_pfn.diff().fillna(0)

    df_view = pfn_mensile.T
    df_view["Variazione vs Mese Prec."] = var_mensile
    df_view.index = [f"{i:02d} - {MESI_NOMI[i-1]}" for i in df_view.index]

    st.subheader(f"Analisi dell'Indebitamento e Liquidita - Anno {anno_sel}")

    styler = df_view.style.format("€ {:,.2f}")
    styler = styler.map(color_pfn_val, subset=["POSIZIONE FINANZIARIA NETTA"])
    styler = styler.map(style_delta, subset=["Variazione vs Mese Prec."])

    st.markdown("""
        <style>
            .stDataFrame thead tr th {
                white-space: normal !important;
                word-wrap: break-word !important;
                vertical-align: bottom !important;
                line-height: 1.2 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.dataframe(styler, use_container_width=True)

    st.divider()
    df_plot = df_view.reset_index().rename(columns={'index': 'Mese'})
    fig_pfn = px.bar(
        df_plot, x="Mese", y="POSIZIONE FINANZIARIA NETTA",
        title="Evoluzione Mensile PFN",
        color="POSIZIONE FINANZIARIA NETTA",
        color_continuous_scale=['#e74c3c', '#2ecc71'],
        color_continuous_midpoint=0
    )
    st.plotly_chart(fig_pfn, use_container_width=True)
