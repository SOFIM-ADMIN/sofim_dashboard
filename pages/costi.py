"""
Sofim Financial Dashboard - Pagina Analisi Costi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import MESI_NOMI
from utils.formatting import clean_numeric, style_delta
from utils.plots import create_pareto_chart


def render(df_final: pd.DataFrame) -> None:
    st.title("💸 BI - Analisi Costi")

    anni = sorted(df_final["Anno"].unique())
    if len(anni) < 1:
        st.warning("Dati insufficienti per l'analisi.")
        return

    anno_sel = st.selectbox("Seleziona Anno", anni, index=len(anni)-1, key="costi_anno")
    anno_prec = anno_sel - 1
    mask_costi = df_final["Cat_Safe"].str.contains(r"COST|ACQUIST|USCIT|PERSONALE", na=False)

    t1, t2, t3, t4 = st.tabs(["📋 Tabella & Dettaglio", "📉 Trend Mensile", "📊 Incidenza Ricavi", "🎯 Pareto"])

    with t1:
        placeholder_dettaglio = st.empty()
        st.subheader(f"Dettaglio Costi: {anno_sel} vs {anno_prec}")

        df_c = df_final[mask_costi & df_final["Anno"].isin([anno_sel, anno_prec])].copy()
        df_c["Valore_Costo"] = df_c["Dare"].apply(clean_numeric) - df_c["Avere"].apply(clean_numeric)

        pivot_costi = df_c.pivot_table(
            index=["Codice Conto", "Tipo", "Descrizione Conto"],
            columns="Anno",
            values="Valore_Costo",
            aggfunc="sum"
        ).fillna(0).reset_index()

        for a in [anno_sel, anno_prec]:
            if a not in pivot_costi.columns: pivot_costi[a] = 0.0

        evento_selezione = st.dataframe(
            pivot_costi.style.format({anno_prec: "€ {:,.2f}", anno_sel: "€ {:,.2f}"}),
            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row"
        )

        if len(evento_selezione.selection.rows) > 0:
            idx = evento_selezione.selection.rows[0]
            riga = pivot_costi.iloc[idx]
            codice_sel = riga["Codice Conto"]

            with placeholder_dettaglio.container():
                st.markdown(f"### 🔍 Analisi Movimenti: **{riga['Descrizione Conto']}**")

                df_drill = df_final[
                    (df_final["Codice Conto"] == codice_sel) & (df_final["Anno"] == anno_sel)
                ].copy()
                df_drill["Importo_Netto"] = df_drill["Dare"].apply(clean_numeric) - df_drill["Avere"].apply(clean_numeric)
                df_drill = df_drill.sort_values("Data Operazione", ascending=True)
                df_drill["Saldo Progressivo"] = df_drill["Importo_Netto"].cumsum()
                df_drill["Data_Fmt"] = df_drill["Data Operazione"].dt.strftime("%d/%m/%Y")

                for col in ["Protocollo", "Numero Documento", "Data Documento"]:
                    if col not in df_drill.columns: df_drill[col] = "-"

                if not df_drill.empty:
                    cols_view = ["Data_Fmt", "Descrizione Causale Testata", "Protocollo",
                                 "Numero Documento", "Data Documento", "Importo_Netto", "Saldo Progressivo"]
                    if "Descrizione Riga" in df_drill.columns: cols_view.insert(2, "Descrizione Riga")

                    st.dataframe(
                        df_drill[cols_view].style.format({"Importo_Netto": "€ {:,.2f}", "Saldo Progressivo": "€ {:,.2f}"})
                        .map(style_delta, subset=["Importo_Netto"]),
                        use_container_width=True, hide_index=True
                    )
                    if st.button("Chiudi Dettaglio ❌"): st.rerun()
                else:
                    st.info(f"Nessun movimento trovato per {riga['Descrizione Conto']}")
                st.divider()

    with t2:
        st.subheader("Andamento Temporale Costi")
        df_trend = df_c[df_c["Anno"].isin([anno_sel, anno_prec])].pivot_table(
            index="Mese_Num", columns="Anno", values="Valore_Costo", aggfunc="sum"
        ).reindex(range(1, 13), fill_value=0)
        df_trend.index = [f"{i:02d}-{MESI_NOMI[i-1]}" for i in df_trend.index]
        st.line_chart(df_trend)
        st.caption("Confronto andamento costi mensili tra l'anno selezionato e l'anno precedente.")

    with t3:
        mese_limite = st.session_state.get("mese_incidenza_new", 12)
        mask_periodo = df_final["Mese_Num"] <= mese_limite
        mask_ric = df_final["Cat_Safe"].str.contains(r"RICAV|VENDIT", na=False)
        tot_ric_sel = df_final[(df_final["Anno"] == anno_sel) & mask_ric & mask_periodo]["Importo_Netto"].abs().sum()
        tot_ric_prec = df_final[(df_final["Anno"] == anno_prec) & mask_ric & mask_periodo]["Importo_Netto"].abs().sum()

        m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
        with m_col1:
            mese_limite = st.selectbox("Fino al mese di:", range(1, 13), index=mese_limite-1,
                                       format_func=lambda x: MESI_NOMI[x-1], key="mese_incidenza_new")
        with m_col2: st.metric(f"Fatturato {anno_sel}", f"€ {tot_ric_sel:,.0f}")
        with m_col3: st.metric(f"Fatturato {anno_prec}", f"€ {tot_ric_prec:,.0f}")

        df_c_periodo = df_c[df_c["Mese_Num"] <= mese_limite].copy()
        pivot_inc = df_c_periodo.pivot_table(index=["Codice Conto", "Descrizione Conto"], columns="Anno",
                                              values="Valore_Costo", aggfunc="sum").fillna(0).reset_index()

        if tot_ric_sel > 0:
            pivot_inc[f"Incidenza % {anno_sel}"] = (pivot_inc[anno_sel] / tot_ric_sel) * 100
            pivot_inc[f"Incidenza % {anno_prec}"] = (pivot_inc[anno_prec] / (tot_ric_prec if tot_ric_prec > 0 else 1)) * 100
            pivot_inc["Var. P.P."] = pivot_inc[f"Incidenza % {anno_sel}"] - pivot_inc[f"Incidenza % {anno_prec}"]
            df_view = pivot_inc[~pivot_inc["Descrizione Conto"].str.contains("RIMANENZE", case=False)].sort_values(f"Incidenza % {anno_sel}", ascending=False)

            st.dataframe(df_view[["Descrizione Conto", f"Incidenza % {anno_prec}", f"Incidenza % {anno_sel}", "Var. P.P."]].style.format(
                {f"Incidenza % {anno_prec}": "{:.2f}%", f"Incidenza % {anno_sel}": "{:.2f}%", "Var. P.P.": "{:+.2f}"}
            ).background_gradient(subset=["Var. P.P."], cmap="PiYG_r", vmin=-3, vmax=3)
              .map(lambda v: 'color: white; font-weight: bold;' if abs(v) > 1.5 else 'color: black;', subset=["Var. P.P."]),
              use_container_width=True, hide_index=True)

            fig_inc = px.pie(df_view.head(10), values=f"Incidenza % {anno_sel}", names="Descrizione Conto", hole=0.4, template="plotly_white")
            fig_inc.update_traces(textposition='outside', textinfo='percent+label')
            fig_inc.update_layout(showlegend=False, height=600)
            st.plotly_chart(fig_inc, use_container_width=True)

    with t4:
        st.subheader("Analisi di Pareto sui Costi (Regola 80/20)")
        st.info("Questa analisi identifica le voci di spesa che pesano maggiormente sul totale.")
        mese_limite_pareto = st.session_state.get("mese_incidenza_new", 12)

        df_display = pivot_inc[~pivot_inc["Descrizione Conto"].str.contains("RIMANENZE", case=False)].copy()
        totale_costi_periodo = df_display[anno_sel].sum()

        if totale_costi_periodo > 0:
            df_display = df_display.sort_values(anno_sel, ascending=False)
            df_display["Peso %"] = (df_display[anno_sel] / totale_costi_periodo) * 100
            df_display["% Cumulata"] = df_display["Peso %"].cumsum()

            def assegna_classe(cum):
                if cum <= 80: return "A (Critico)"
                if cum <= 95: return "B (Medio)"
                return "C (Marginale)"

            df_display["Classe"] = df_display["% Cumulata"].apply(assegna_classe)

            fig_pareto = create_pareto_chart(df_display, anno_sel, mese_limite_pareto)
            st.plotly_chart(fig_pareto, use_container_width=True)

            st.markdown("### 📋 Classificazione delle Spese")
            st.dataframe(
                df_display[["Classe", "Codice Conto", "Descrizione Conto", anno_sel, "Peso %", "% Cumulata"]].style.format(
                    {anno_sel: "€ {:,.2f}", "Peso %": "{:.1f}%", "% Cumulata": "{:.1f}%"}
                ).map(lambda x: 'background-color: #f8d7da;' if x == "A (Critico)" else
                             ('background-color: #fff3cd;' if x == "B (Medio)" else ''), subset=["Classe"]),
                use_container_width=True, hide_index=True
            )
            voci_a = len(df_display[df_display["Classe"] == "A (Critico)"])
            st.success(f"**Insight:** Solo {voci_a} voci di costo rappresentano l'80% della tua spesa totale.")
        else:
            st.warning("Dati insufficienti per generare il diagramma di Pareto.")
