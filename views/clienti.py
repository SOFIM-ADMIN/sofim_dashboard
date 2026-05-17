"""
Sofim Financial Dashboard - Pagina Analisi Clienti
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import MESI_NOMI
from utils.formatting import style_delta


def render(df_final: pd.DataFrame, mask_ricavi: pd.Series) -> None:
    st.title("👥 BI - Analisi Clienti")

    anni = sorted(df_final["Anno"].unique())
    if len(anni) < 1:
        st.warning("Dati insufficienti per l'analisi.")
        return

    anno_sel = st.selectbox("Anno di riferimento", anni, index=len(anni) - 1, key="clienti_anno")
    anno_prec = anno_sel - 1

    has_tipo = "Tipo" in df_final.columns and df_final["Tipo"].ne("N/D").any()
    mask_ve = df_final["Tipo"].isin(["VE", "VE1"]) if has_tipo else pd.Series(True, index=df_final.index)
    df_cli_ricavi = df_final[mask_ricavi & mask_ve].copy()

    nome_col = "Ragione Sociale" if "Ragione Sociale" in df_final.columns else "Descrizione Riga"
    df_cli_ricavi[nome_col] = df_cli_ricavi[nome_col].fillna("CLIENTE NON DEFINITO").astype(str)

    pivot = (
        df_cli_ricavi[df_cli_ricavi["Anno"].isin([anno_sel, anno_prec])]
        .pivot_table(index=nome_col, columns="Anno", values="Importo_Netto", aggfunc="sum")
        .fillna(0)
        .reset_index()
    )
    for a in [anno_sel, anno_prec]:
        if a not in pivot.columns: pivot[a] = 0.0

    pivot["Delta €"] = pivot[anno_sel] - pivot[anno_prec]
    pivot["Var %"] = ((pivot["Delta €"] / pivot[anno_prec].abs() * 100).replace([pd.np.inf, -pd.np.inf], 0).fillna(0))

    t1, t2, t3, t4, t5 = st.tabs([
        "🔝 Top Clienti", "📈 Trend per Cliente", "📈 Variazioni (Gain/Loss)",
        "🔄 Turnover Nuovi/Persi", "💳 Crediti"
    ])

    with t1:
        st.subheader(f"Classifica Fatturato Clienti: {anno_sel} vs {anno_prec}")
        df_tab = pivot.sort_values(anno_sel, ascending=False)
        st.dataframe(
            df_tab.style.format({anno_sel: "€ {:,.2f}", anno_prec: "€ {:,.2f}", "Delta €": "€ {:,.2f}", "Var %": "{:+.1f}%"})
            .map(style_delta, subset=["Delta €", "Var %"]),
            use_container_width=True, hide_index=True,
        )

    with t2:
        st.subheader("Analisi Dettaglio per Cliente")
        clienti_lista = sorted(df_cli_ricavi[nome_col].unique().astype(str))
        sel_clienti = st.multiselect("Seleziona Clienti", clienti_lista)
        if sel_clienti:
            df_sel = df_cli_ricavi[df_cli_ricavi[nome_col].isin(sel_clienti) & (df_cli_ricavi["Anno"] == anno_sel)]
            trend = (
                df_sel.groupby(["Mese_Num", nome_col])["Importo_Netto"]
                .sum().unstack(fill_value=0).reindex(range(1, 13), fill_value=0)
            )
            trend.index = [f"{i:02d}-{MESI_NOMI[i-1]}" for i in trend.index]
            st.line_chart(trend)

    with t3:
        st.subheader("📈 Analisi Incrementi e Decrementi")
        n_rank = st.number_input("Mostra primi N:", 5, 30, 10)
        col_gain, col_loss = st.columns(2)
        with col_gain:
            st.markdown("#### 🟢 Maggiori Incrementi")
            df_gain = pivot[pivot["Delta €"] > 0].sort_values("Delta €", ascending=False).head(n_rank)
            if not df_gain.empty:
                st.plotly_chart(px.bar(df_gain.sort_values("Delta €"), y=nome_col, x="Delta €", orientation="h", color_discrete_sequence=["#2ecc71"]), use_container_width=True)
        with col_loss:
            st.markdown("#### 🔴 Maggiori Decrementi")
            df_loss = pivot[pivot["Delta €"] < 0].sort_values("Delta €").head(n_rank).copy()
            if not df_loss.empty:
                df_loss["Delta_Abs"] = df_loss["Delta €"].abs()
                st.plotly_chart(px.bar(df_loss.sort_values("Delta_Abs"), y=nome_col, x="Delta_Abs", orientation="h", color_discrete_sequence=["#e74c3c"]), use_container_width=True)

    with t4:
        st.subheader(f"🔄 Analisi Turnover Clienti ({anno_sel} vs {anno_prec})")
        nuovi = pivot[(pivot[anno_sel] > 0) & (pivot[anno_prec] <= 0)].sort_values(anno_sel, ascending=False)
        persi = pivot[(pivot[anno_sel] <= 0) & (pivot[anno_prec] > 0)].sort_values(anno_prec, ascending=False)
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"🌟 Nuovi Clienti acquisiti: {len(nuovi)}")
            st.dataframe(nuovi[[nome_col, anno_sel]].style.format({anno_sel: "€ {:,.2f}"}), use_container_width=True, hide_index=True)
        with c2:
            st.error(f"⚠️ Clienti persi (Churn): {len(persi)}")
            st.dataframe(persi[[nome_col, anno_prec]].style.format({anno_prec: "€ {:,.2f}"}), use_container_width=True, hide_index=True)

    with t5:
        st.subheader("🏦 Analisi Crediti e Incidenza su Vendite (%)")

        mask_cli = df_final["Tipo"].str.upper().str.strip() == "CLI"
        df_crediti = df_final[mask_cli].copy()
        df_crediti["Saldo_Mov"] = df_crediti["Dare"].apply(clean_numeric) - df_crediti["Avere"].apply(clean_numeric)

        mask_ve = df_final["Tipo"].str.upper().str.strip().isin(["VE", "VE1"])
        df_vendite = df_final[mask_ve].copy()
        df_vendite["Valore_VE"] = df_vendite["Avere"].apply(clean_numeric) - df_vendite["Dare"].apply(clean_numeric)

        placeholder_l1 = st.empty()
        placeholder_l2 = st.empty()

        tipo_view = st.radio("Seleziona Valore da Visualizzare:",
                             ["Saldo Progressivo", "Variazione Mensile", "Incidenza su Vendite (%)"],
                             horizontal=True, key="radio_t5_percentuale")

        if not df_crediti.empty:
            piv_crediti = df_crediti.pivot_table(index="Mese_Num", columns="Anno", values="Saldo_Mov", aggfunc="sum").fillna(0)
            piv_vendite = df_vendite.pivot_table(index="Mese_Num", columns="Anno", values="Valore_VE", aggfunc="sum").fillna(0)

            def genera_prospetto(mode):
                if mode == "Variazione Mensile":
                    return piv_crediti
                prog_crediti = piv_crediti.cumsum()
                prog_vendite = piv_vendite.cumsum()
                if mode == "Saldo Progressivo":
                    return prog_crediti
                if mode == "Incidenza su Vendite (%)":
                    perc_table = pd.DataFrame(index=range(1, 13), columns=piv_crediti.columns)
                    for anno in piv_crediti.columns:
                        for mese in range(1, 13):
                            c_prog = prog_crediti.loc[mese, anno] if mese in prog_crediti.index else 0
                            v_prog = prog_vendite.loc[mese, anno] if mese in prog_vendite.index else 0
                            if v_prog > 0:
                                v_ragguagliate = (v_prog / mese) * 12
                                perc_table.loc[mese, anno] = (c_prog / v_ragguagliate) * 100
                            else:
                                perc_table.loc[mese, anno] = 0
                    return perc_table.astype(float)

            prospetto_final = genera_prospetto(tipo_view)
            prospetto_final.index = [f"{i:02d} - {MESI_NOMI[i-1]}" for i in prospetto_final.index]

            formato = "{:.2f} %" if "%" in tipo_view else "€ {:,.2f}"
            st.info(f"Visualizzazione: **{tipo_view}**")
            ev_mese = st.dataframe(
                prospetto_final[[a for a in [anno_prec, anno_sel] if a in prospetto_final.columns]].style.format(formato),
                use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_t5_percent"
            )

            if len(ev_mese.selection.rows) > 0:
                m_sel = ev_mese.selection.rows[0] + 1
                with placeholder_l1.container():
                    st.markdown(f"#### 📁 Dettaglio Conti - {MESI_NOMI[m_sel-1]} {anno_sel}")
                    is_prog_drill = "Variazione" not in tipo_view
                    mask_t = (df_crediti["Mese_Num"] <= m_sel if is_prog_drill else df_crediti["Mese_Num"] == m_sel) & (df_crediti["Anno"] == anno_sel)
                    df_p = df_crediti[mask_t].copy()

                    def raggruppa_final(row):
                        cod = str(row["Codice Conto"]).upper().strip()
                        des = str(row["Descrizione Conto"]).upper().strip()
                        isolati = ["1B", "2B", "4B", "SBF", "FATTURE DA EMETTERE", "ANTICIPO"]
                        if any(x in cod for x in isolati) or any(x in des for x in isolati):
                            return f"{row['Codice Conto']} - {row['Descrizione Conto']}"
                        return "CLIENTI (Totale Nominativi)"

                    df_p["Gruppo_Sintetico"] = df_p.apply(raggruppa_final, axis=1)
                    res_l1 = df_p.groupby("Gruppo_Sintetico")["Saldo_Mov"].sum().reset_index()

                    ev_l1 = st.dataframe(
                        res_l1.sort_values("Saldo_Mov", ascending=False).style.format({"Saldo_Mov": "€ {:,.2f}"}),
                        use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key=f"t5_l1_perc_{m_sel}"
                    )

                    if len(ev_l1.selection.rows) > 0:
                        g_sel = res_l1.sort_values("Saldo_Mov", ascending=False).iloc[ev_l1.selection.rows[0]]["Gruppo_Sintetico"]
                        with placeholder_l2.container():
                            st.markdown(f"#### 👤 Dettaglio Analitico: {g_sel}")
                            df_ana = df_p[df_p["Gruppo_Sintetico"] == g_sel]
                            res_ana = df_ana.groupby(["Codice Conto", "Descrizione Conto"])["Saldo_Mov"].sum().reset_index()
                            st.dataframe(res_ana[res_ana["Saldo_Mov"]!=0].style.format({"Saldo_Mov": "€ {:,.2f}"}), use_container_width=True, hide_index=True)
