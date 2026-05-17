"""
Sofim Financial Dashboard - Pagina Analisi Ricavi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from config import MESI_NOMI
from utils.formatting import clean_numeric, style_delta, fmt_eur
from utils.plots import create_clean_pie


def render(df_final: pd.DataFrame, mask_ricavi: pd.Series) -> None:
    st.title("💰 BI - Gestione Ricavi")

    anni = sorted(df_final["Anno"].unique())
    if len(anni) < 1:
        st.warning("Dati insufficienti per l'analisi.")
        return

    anno_sel = st.selectbox("Seleziona Anno di Analisi", anni, index=len(anni) - 1)
    anno_prec = anno_sel - 1

    tab1, tab2, tab3 = st.tabs(["📋 Tabella Comparativa", "📈 Dettaglio Vendite", "🍰 Composizione Vendite"])

    with tab1:
        st.subheader(f"Confronto Conti Ricavi: {anno_sel} vs {anno_prec}")
        df_ric_all = df_final[mask_ricavi & df_final["Anno"].isin([anno_sel, anno_prec])]

        has_tipo = "Tipo" in df_final.columns and df_final["Tipo"].ne("N/D").any()
        index_cols = ["Tipo", "Descrizione Conto"] if has_tipo else ["Descrizione Conto"]

        pivot = (
            df_ric_all
            .pivot_table(index=index_cols, columns="Anno", values="Importo_Netto", aggfunc="sum")
            .reset_index()
            .fillna(0)
        )
        for a in [anno_sel, anno_prec]:
            if a not in pivot.columns:
                pivot[a] = 0.0

        pivot["Var. Assoluta €"] = pivot[anno_sel] - pivot[anno_prec]
        pivot["Var. %"] = (
            (pivot["Var. Assoluta €"] / pivot[anno_prec].abs() * 100)
            .replace([np.inf, -np.inf], 0)
            .fillna(0)
        )
        pivot = pivot.sort_values([index_cols[0], anno_sel] if has_tipo else [anno_sel], ascending=False)

        fmt_cols = {anno_prec: "€ {:,.2f}", anno_sel: "€ {:,.2f}", "Var. Assoluta €": "€ {:,.2f}", "Var. %": "{:+.1f}%"}
        st.dataframe(
            pivot.style.format(fmt_cols).map(style_delta, subset=["Var. Assoluta €", "Var. %"]),
            use_container_width=True, hide_index=True,
        )

    with tab2:
        st.subheader("📈 Analisi Temporale e Comparativa")

        has_tipo = "Tipo" in df_final.columns
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            opzioni_tipo = ["VE", "VE1"] if has_tipo else []
            tipi_scelti = st.multiselect("Seleziona Tipo Ricavo:", opzioni_tipo, default=opzioni_tipo)
            mask_ve = df_final["Tipo"].isin(tipi_scelti) if tipi_scelti else pd.Series(True, index=df_final.index)

        with col_f2:
            is_prog_globale = st.radio("Visualizzazione Totale:", ["Mensile", "Progressivo"], horizontal=True, key="radio_glob") == "Progressivo"

        df_base = df_final[mask_ricavi & mask_ve].copy()

        pivot_mesi = (
            df_base[df_base["Anno"].isin([anno_sel, anno_prec])]
            .pivot_table(index="Mese_Num", columns="Anno", values="Importo_Netto", aggfunc="sum")
            .reindex(range(1, 13), fill_value=0)
        )

        for a in [anno_sel, anno_prec]:
            if a not in pivot_mesi.columns:
                pivot_mesi[a] = 0.0

        if is_prog_globale:
            pivot_mesi = pivot_mesi.cumsum()

        pivot_mesi["Var. Assoluta €"] = pivot_mesi[anno_sel] - pivot_mesi[anno_prec]
        pivot_mesi["Var. %"] = ((pivot_mesi[anno_sel] - pivot_mesi[anno_prec]) / pivot_mesi[anno_prec].replace(0, np.nan).abs() * 100).fillna(0)
        pivot_mesi.index = [f"{i:02d} - {MESI_NOMI[i-1]}" for i in pivot_mesi.index]

        st.markdown(f"**Prospetto Totale Vendite ({'Progressivo' if is_prog_globale else 'Mensile'})**")
        st.dataframe(
            pivot_mesi.style.format({anno_prec: "€ {:,.2f}", anno_sel: "€ {:,.2f}", "Var. Assoluta €": "€ {:,.2f}", "Var. %": "{:+.1f}%"})
            .map(style_delta, subset=["Var. Assoluta €", "Var. %"]),
            use_container_width=True
        )

        st.markdown(f"**Trend Grafico: {anno_sel} vs {anno_prec}**")
        st.area_chart(pivot_mesi[[anno_prec, anno_sel]], height=250)

        st.divider()
        st.subheader("🔍 Analisi di Dettaglio per Conto")

        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            conti_disponibili = sorted(df_base["Descrizione Conto"].unique())
            conto_scelto = st.selectbox("Seleziona un conto:", ["---"] + conti_disponibili)
        with col_c2:
            is_prog_conto = st.checkbox("Valori Progressivi (Conto)", value=False, key="check_prog_conto")

        if conto_scelto != "---":
            df_conto = df_base[df_base["Descrizione Conto"] == conto_scelto]
            pivot_conto = (
                df_conto[df_conto["Anno"].isin([anno_sel, anno_prec])]
                .pivot_table(index="Mese_Num", columns="Anno", values="Importo_Netto", aggfunc="sum")
                .reindex(range(1, 13), fill_value=0)
            )

            for a in [anno_sel, anno_prec]:
                if a not in pivot_conto.columns: pivot_conto[a] = 0.0

            if is_prog_conto:
                pivot_conto = pivot_conto.cumsum()

            pivot_conto["Var. Assoluta €"] = pivot_conto[anno_sel] - pivot_conto[anno_prec]
            pivot_conto["Var. %"] = ((pivot_conto[anno_sel] - pivot_conto[anno_prec]) / pivot_conto[anno_prec].replace(0, np.nan).abs() * 100).fillna(0)
            pivot_conto.index = [f"{i:02d} - {MESI_NOMI[i-1]}" for i in pivot_conto.index]

            st.dataframe(
                pivot_conto.style.format({anno_prec: "€ {:,.2f}", anno_sel: "€ {:,.2f}", "Var. Assoluta €": "€ {:,.2f}", "Var. %": "{:+.1f}%"})
                .map(style_delta, subset=["Var. Assoluta €", "Var. %"]),
                use_container_width=True
            )

        st.divider()
        st.subheader("📑 Riepilogo per Cliente e Confronto Anni")

        if conto_scelto == "---":
            st.warning("⚠️ Seleziona un conto nella sezione superiore per visualizzare il dettaglio clienti.")
        else:
            c_mov1, c_mov2 = st.columns([1, 3])
            with c_mov1:
                is_prog_lista = st.checkbox("Metodo Progressivo", value=False, key="check_prog_lista")
            with c_mov2:
                mese_attuale_idx = max(pd.Timestamp.now().month - 2, 0)
                mesi_sel = st.multiselect("Filtra Mese/i per il riepilogo:", MESI_NOMI, default=[MESI_NOMI[mese_attuale_idx]])

            if mesi_sel:
                nums = [MESI_NOMI.index(m) + 1 for m in mesi_sel]
                range_mesi = range(1, max(nums) + 1) if is_prog_lista else nums

                df_mov_filtered = df_base[
                    (df_base["Descrizione Conto"] == conto_scelto) &
                    (df_base["Mese_Num"].isin(range_mesi))
                ]

                if not df_mov_filtered.empty:
                    col_cliente = "Ragione Sociale" if "Ragione Sociale" in df_mov_filtered.columns else "Descrizione Riga"

                    riepilogo_cli = (
                        df_mov_filtered[df_mov_filtered["Anno"].isin([anno_sel, anno_prec])]
                        .pivot_table(index=col_cliente, columns="Anno", values="Importo_Netto", aggfunc="sum")
                        .fillna(0)
                        .reset_index()
                    )

                    for a in [anno_sel, anno_prec]:
                        if a not in riepilogo_cli.columns:
                            riepilogo_cli[a] = 0.0

                    riepilogo_cli["Delta €"] = riepilogo_cli[anno_sel] - riepilogo_cli[anno_prec]
                    riepilogo_cli["Var %"] = (
                        (riepilogo_cli["Delta €"] / riepilogo_cli[anno_prec].replace(0, np.nan).abs() * 100)
                        .fillna(0)
                    )

                    riepilogo_cli = riepilogo_cli.sort_values(anno_sel, ascending=False)

                    st.markdown(f"**Analisi Clienti per: {conto_scelto} ({'Progressivo' if is_prog_lista else 'Mesi selezionati'})**")

                    st.dataframe(
                        riepilogo_cli.style.format({
                            anno_prec: "€ {:,.2f}",
                            anno_sel: "€ {:,.2f}",
                            "Delta €": "€ {:,.2f}",
                            "Var %": "{:+.1f}%"
                        }).map(style_delta, subset=["Delta €", "Var %"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(f"Nessun dato trovato per il conto '{conto_scelto}' nei mesi selezionati.")

    with tab3:
        st.subheader("🍰 Analisi Mix Vendite")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            mese_corrente_idx = max(pd.Timestamp.now().month - 2, 0)
            mese_comp = st.select_slider("Fino al Mese di:", options=MESI_NOMI, value=MESI_NOMI[mese_corrente_idx])
            idx_m = MESI_NOMI.index(mese_comp) + 1
        with col_c2:
            prog_comp = st.checkbox("Analisi Progressiva (Cumulata)", value=True)

        mask_f = (df_final["Mese_Num"] <= idx_m) if prog_comp else (df_final["Mese_Num"] == idx_m)
        mask_ve2 = df_final["Tipo"].isin(["VE", "VE1"]) if has_tipo else pd.Series(True, index=df_final.index)
        df_c = df_final[mask_ricavi & mask_ve2 & mask_f]

        st.subheader("🥧 Visualizzazione Mix Ricavi")
        col_p1, col_p2 = st.columns(2)
        for col_ui, anno, label in [(col_p1, anno_prec, f"Mix Ricavi {anno_prec}"), (col_p2, anno_sel, f"Mix Ricavi {anno_sel}")]:
            with col_ui:
                df_pie = df_c[df_c["Anno"] == anno].groupby("Descrizione Conto")["Importo_Netto"].sum().reset_index()
                if not df_pie.empty and df_pie["Importo_Netto"].sum() > 0:
                    st.plotly_chart(create_clean_pie(df_pie, label), use_container_width=True)
                else:
                    st.info(f"Dati {anno} non disponibili.")

        st.divider()
        st.subheader("📊 Tabella Comparativa Mix Ricavi con Incidenza %")
        df_mix = (
            df_c.pivot_table(index="Descrizione Conto", columns="Anno", values="Importo_Netto", aggfunc="sum")
            .fillna(0)
            .reset_index()
        )
        for a in [anno_sel, anno_prec]:
            if a not in df_mix.columns:
                df_mix[a] = 0.0

        tot_curr = df_mix[anno_sel].sum() or 1
        tot_prev = df_mix[anno_prec].sum() or 1
        col_pct_curr = f"% Su Tot {anno_sel}"
        col_pct_prev = f"% Su Tot {anno_prec}"
        df_mix[col_pct_curr] = df_mix[anno_sel] / tot_curr * 100
        df_mix[col_pct_prev] = df_mix[anno_prec] / tot_prev * 100
        df_mix["Variazione €"] = df_mix[anno_sel] - df_mix[anno_prec]
        df_mix["Var. %"] = (
            (df_mix["Variazione €"] / df_mix[anno_prec].abs() * 100)
            .replace([np.inf, -np.inf], 0)
            .fillna(0)
        )
        cols_ord = ["Descrizione Conto", anno_prec, col_pct_prev, anno_sel, col_pct_curr, "Variazione €", "Var. %"]
        df_mix = df_mix[cols_ord].sort_values(anno_sel, ascending=False)

        styler = df_mix.style.format({
            anno_prec: "€ {:,.2f}", anno_sel: "€ {:,.2f}",
            col_pct_prev: "{:.1f}%", col_pct_curr: "{:.1f}%",
            "Variazione €": "€ {:,.2f}", "Var. %": "{:+.1f}%",
        })
        try:
            import matplotlib
            styler = styler.background_gradient(cmap="Blues", subset=[col_pct_prev, col_pct_curr])
        except ImportError:
            st.info("💡 Installa `matplotlib` per la colorazione delle percentuali.")
        styler = styler.map(style_delta, subset=["Variazione €", "Var. %"])
        st.dataframe(styler, use_container_width=True, hide_index=True)
