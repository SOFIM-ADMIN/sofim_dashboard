"""
Sofim Financial Dashboard - Pagina Scorecard Indici di Bilancio
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from core.bilancio import get_saldo, get_saldo_attivo, get_saldo_passivo, get_fondo
from utils.formatting import clean_numeric, get_color_indice
from utils.plots import create_radar_chart


def render(df_final: pd.DataFrame) -> None:
    st.title("📊 Scorecard Indici di Bilancio")
    st.info("Calcolati automaticamente dai dati contabili caricati. Confronto anno su anno.")

    anni = sorted(df_final["Anno"].unique())
    if not anni:
        st.warning("Nessun dato disponibile.")
        return

    anno_sel = st.selectbox("Seleziona Anno di Analisi", anni, index=len(anni) - 1, key="indici_anno")
    anno_prec = anno_sel - 1

    def safe_div(num, den, default=0.0):
        return num / den if den != 0 else default

    # --- CALCOLO VOCI ---
    ricavi_c = abs(get_saldo(df_final, ["VE", "VE1", "VE2", "RIA"], anno_sel))
    ricavi_p = abs(get_saldo(df_final, ["VE", "VE1", "VE2", "RIA"], anno_prec))

    va_c = get_saldo(df_final, ["AMMRE", "AUTO", "UT", "CC1", "CA", "CG", "IMP", "OD", "GOD"], anno_sel)
    va_p = get_saldo(df_final, ["AMMRE", "AUTO", "UT", "CC1", "CA", "CG", "IMP", "OD", "GOD"], anno_prec)
    pe_c = get_saldo(df_final, "PE", anno_sel)
    pe_p = get_saldo(df_final, "PE", anno_prec)
    ebitda_c = va_c + pe_c
    ebitda_p = va_p + pe_p

    amm_c = get_saldo(df_final, ["AMMMAT", "AMIMMAT", "PEC", "ACFR"], anno_sel)
    amm_p = get_saldo(df_final, ["AMMMAT", "AMIMMAT", "PEC", "ACFR"], anno_prec)
    ebit_c = ebitda_c + amm_c
    ebit_p = ebitda_p + amm_p

    fin_c = get_saldo(df_final, ["PF", "OF"], anno_sel)
    fin_p = get_saldo(df_final, ["PF", "OF"], anno_prec)
    stra_c = get_saldo(df_final, ["PS", "OS"], anno_sel)
    stra_p = get_saldo(df_final, ["PS", "OS"], anno_prec)
    imp_c = get_saldo(df_final, ["IR", "IRD"], anno_sel)
    imp_p = get_saldo(df_final, ["IR", "IRD"], anno_prec)
    utile_c = ebit_c + fin_c + stra_c + imp_c
    utile_p = ebit_p + fin_p + stra_p + imp_p

    cs_c = get_saldo_passivo(df_final, "CS", anno_sel)
    cs_p = get_saldo_passivo(df_final, "CS", anno_prec)
    pn_c = get_saldo_passivo(df_final, "PN", anno_sel)
    pn_p = get_saldo_passivo(df_final, "PN", anno_prec)
    upn_c = get_saldo_passivo(df_final, "UPN", anno_sel)
    upn_p = get_saldo_passivo(df_final, "UPN", anno_prec)
    patr_netto_c = cs_c + pn_c + upn_c + utile_c
    patr_netto_p = cs_p + pn_p + upn_p + utile_p

    imm_c = get_saldo_attivo(df_final, "IMIMM", anno_sel) - get_fondo(df_final, "FIMMAT", anno_sel)
    imm_p = get_saldo_attivo(df_final, "IMIMM", anno_prec) - get_fondo(df_final, "FIMMAT", anno_prec)
    mat_c = get_saldo_attivo(df_final, "IMMAT", anno_sel) - get_fondo(df_final, "FMAT", anno_sel)
    mat_p = get_saldo_attivo(df_final, "IMMAT", anno_prec) - get_fondo(df_final, "FMAT", anno_prec)
    fin_imm_c = get_saldo_attivo(df_final, "IMMFIN", anno_sel)
    fin_imm_p = get_saldo_attivo(df_final, "IMMFIN", anno_prec)
    att_imm_c = imm_c + mat_c + fin_imm_c
    att_imm_p = imm_p + mat_p + fin_imm_p

    rim_c = get_saldo_attivo(df_final, "RIM", anno_sel)
    rim_p = get_saldo_attivo(df_final, "RIM", anno_prec)
    anf_c = get_saldo_attivo(df_final, "ANF", anno_sel)
    anf_p = get_saldo_attivo(df_final, "ANF", anno_prec)
    cli_c = get_saldo_attivo(df_final, "CLI", anno_sel) - get_fondo(df_final, "CLIF", anno_sel)
    cli_p = get_saldo_attivo(df_final, "CLI", anno_prec) - get_fondo(df_final, "CLIF", anno_prec)
    af_c = get_saldo_attivo(df_final, "AF", anno_sel)
    af_p = get_saldo_attivo(df_final, "AF", anno_prec)
    era_c = get_saldo_attivo(df_final, "ERARIO", anno_sel)
    era_p = get_saldo_attivo(df_final, "ERARIO", anno_prec)
    aa_c = get_saldo_attivo(df_final, ["AA", "RRA"], anno_sel)
    aa_p = get_saldo_attivo(df_final, ["AA", "RRA"], anno_prec)
    banche_c = get_saldo_attivo(df_final, "BANCHE", anno_sel)
    banche_p = get_saldo_attivo(df_final, "BANCHE", anno_prec)
    dl_c = get_saldo_attivo(df_final, "DL", anno_sel)
    dl_p = get_saldo_attivo(df_final, "DL", anno_prec)

    att_corr_c = rim_c + anf_c + cli_c + af_c + era_c + aa_c + banche_c + dl_c
    att_corr_p = rim_p + anf_p + cli_p + af_p + era_p + aa_p + banche_p + dl_p
    tot_att_c = att_imm_c + att_corr_c
    tot_att_p = att_imm_p + att_corr_p

    bp_c = get_saldo_passivo(df_final, "BANCHE", anno_sel)
    bp_p = get_saldo_passivo(df_final, "BANCHE", anno_prec)
    bant_c = get_saldo_passivo(df_final, "BANT", anno_sel)
    bant_p = get_saldo_passivo(df_final, "BANT", anno_prec)
    forn_c = get_saldo_passivo(df_final, "FORN", anno_sel)
    forn_p = get_saldo_passivo(df_final, "FORN", anno_prec)
    antcli_c = get_saldo_passivo(df_final, "ANTCLI", anno_sel)
    antcli_p = get_saldo_passivo(df_final, "ANTCLI", anno_prec)
    erap_c = get_saldo_passivo(df_final, "ERARIO", anno_sel)
    erap_p = get_saldo_passivo(df_final, "ERARIO", anno_prec)
    prev_c = get_saldo_passivo(df_final, "PREV", anno_sel)
    prev_p = get_saldo_passivo(df_final, "PREV", anno_prec)
    ap_c = get_saldo_passivo(df_final, "AP", anno_sel)
    ap_p = get_saldo_passivo(df_final, "AP", anno_prec)
    rrp_c = get_saldo_passivo(df_final, "RRP", anno_sel)
    rrp_p = get_saldo_passivo(df_final, "RRP", anno_prec)

    pass_corr_c = bp_c + bant_c + forn_c + antcli_c + erap_c + prev_c + ap_c + rrp_c
    pass_corr_p = bp_p + bant_p + forn_p + antcli_p + erap_p + prev_p + ap_p + rrp_p

    cap_inv_c = tot_att_c - pass_corr_c
    cap_inv_p = tot_att_p - pass_corr_p

    dcon_c = get_saldo_passivo(df_final, "DCON", anno_sel)
    dcon_p = get_saldo_passivo(df_final, "DCON", anno_prec)
    fmlt_c = get_saldo_passivo(df_final, "FMLT", anno_sel)
    fmlt_p = get_saldo_passivo(df_final, "FMLT", anno_prec)
    fin_p_c = get_saldo_passivo(df_final, "FIN", anno_sel)
    fin_p_p = get_saldo_passivo(df_final, "FIN", anno_prec)
    soci_c = get_saldo_passivo(df_final, "SOCI", anno_sel)
    soci_p = get_saldo_passivo(df_final, "SOCI", anno_prec)
    tfm_c = get_saldo_passivo(df_final, "TFM", anno_sel)
    tfm_p = get_saldo_passivo(df_final, "TFM", anno_prec)
    tfr_c = get_saldo_passivo(df_final, "TFR", anno_sel)
    tfr_p = get_saldo_passivo(df_final, "TFR", anno_prec)
    fondi_c = get_saldo_passivo(df_final, "FONDI", anno_sel)
    fondi_p = get_saldo_passivo(df_final, "FONDI", anno_prec)

    pass_cons_c = dcon_c + fmlt_c + fin_p_c + soci_c + tfm_c + tfr_c + fondi_c
    pass_cons_p = dcon_p + fmlt_p + fin_p_p + soci_p + tfm_p + tfr_p + fondi_p
    tot_debiti_c = pass_corr_c + pass_cons_c
    tot_debiti_p = pass_corr_p + pass_cons_p

    liq_imm_c = banche_c + dl_c
    liq_imm_p = banche_p + dl_p

    # --- INDICI ---
    roe_c = safe_div(utile_c, patr_netto_c)
    roe_p = safe_div(utile_p, patr_netto_p)
    roi_c = safe_div(ebit_c, cap_inv_c)
    roi_p = safe_div(ebit_p, cap_inv_p)
    ros_c = safe_div(ebit_c, ricavi_c)
    ros_p = safe_div(ebit_p, ricavi_p)
    margine_lordo_c = safe_div(get_saldo(df_final, ["VE", "VE1", "VE2", "RIA"], anno_sel) + get_saldo(df_final, ["RI", "ME", "ME1", "ME2", "LA", "CP", "RF"], anno_sel), ricavi_c)
    margine_lordo_p = safe_div(get_saldo(df_final, ["VE", "VE1", "VE2", "RIA"], anno_prec) + get_saldo(df_final, ["RI", "ME", "ME1", "ME2", "LA", "CP", "RF"], anno_prec), ricavi_p)

    leverage_c = safe_div(tot_debiti_c, patr_netto_c)
    leverage_p = safe_div(tot_debiti_p, patr_netto_p)
    ind_liquidita_c = safe_div(liq_imm_c, pass_corr_c)
    ind_liquidita_p = safe_div(liq_imm_p, pass_corr_p)
    ind_solvibilita_c = safe_div(tot_att_c, tot_debiti_c)
    ind_solvibilita_p = safe_div(tot_att_p, tot_debiti_p)
    marg_strutt_c = safe_div(patr_netto_c, att_imm_c)
    marg_strutt_p = safe_div(patr_netto_p, att_imm_p)

    # --- KPI CARDS ---
    st.subheader("🎯 Indicatori Chiave")
    c1, c2, c3, c4 = st.columns(4)

    def fmt_pct(v): return f"{v*100:.1f}%"
    def fmt_x(v): return f"{v:.2f}x"
    def delta_color(v): return "normal" if v >= 0 else "inverse"

    with c1: st.metric("ROE", fmt_pct(roe_c), delta=f"{(roe_c-roe_p)*100:.1f} pp", delta_color=delta_color(roe_c-roe_p))
    with c2: st.metric("ROI", fmt_pct(roi_c), delta=f"{(roi_c-roi_p)*100:.1f} pp", delta_color=delta_color(roi_c-roi_p))
    with c3: st.metric("ROS", fmt_pct(ros_c), delta=f"{(ros_c-ros_p)*100:.1f} pp", delta_color=delta_color(ros_c-ros_p))
    with c4: st.metric("Margine Lordo", fmt_pct(margine_lordo_c), delta=f"{(margine_lordo_c-margine_lordo_p)*100:.1f} pp", delta_color=delta_color(margine_lordo_c-margine_lordo_p))

    c5, c6, c7, c8 = st.columns(4)
    with c5: st.metric("Leverage", fmt_x(leverage_c), delta=f"{leverage_c-leverage_p:.2f}x", delta_color="inverse" if leverage_c > leverage_p else "normal")
    with c6: st.metric("Liquidita", fmt_x(ind_liquidita_c), delta=f"{ind_liquidita_c-ind_liquidita_p:.2f}x", delta_color=delta_color(ind_liquidita_c-ind_liquidita_p))
    with c7: st.metric("Solvibilita", fmt_x(ind_solvibilita_c), delta=f"{ind_solvibilita_c-ind_solvibilita_p:.2f}x", delta_color=delta_color(ind_solvibilita_c-ind_solvibilita_p))
    with c8: st.metric("Marg. Struttura", fmt_x(marg_strutt_c), delta=f"{marg_strutt_c-marg_strutt_p:.2f}x", delta_color=delta_color(marg_strutt_c-marg_strutt_p))

    st.divider()

    # --- TABELLA ---
    st.subheader("📋 Prospetto Completo Indici")

    indici_data = [
        {"Indice": "ROE", "Descrizione": "Return on Equity", "Formula": "Utile Netto / Patrimonio Netto", anno_sel: roe_c, anno_prec: roe_p, "Unita": "%"},
        {"Indice": "ROI", "Descrizione": "Return on Investment", "Formula": "EBIT / Capitale Investito", anno_sel: roi_c, anno_prec: roi_p, "Unita": "%"},
        {"Indice": "ROS", "Descrizione": "Return on Sales", "Formula": "EBIT / Ricavi", anno_sel: ros_c, anno_prec: ros_p, "Unita": "%"},
        {"Indice": "Margine Lordo", "Descrizione": "Margine Commerciale / Ricavi", "Formula": "(Ricavi - Costo Venduto) / Ricavi", anno_sel: margine_lordo_c, anno_prec: margine_lordo_p, "Unita": "%"},
        {"Indice": "Leverage", "Descrizione": "Indebitamento / Patrimonio", "Formula": "Totale Debiti / Patrimonio Netto", anno_sel: leverage_c, anno_prec: leverage_p, "Unita": "x"},
        {"Indice": "Ind. Liquidita", "Descrizione": "Liquidita Immediate / Pass. Correnti", "Formula": "(Banche + Cassa) / Passivita Correnti", anno_sel: ind_liquidita_c, anno_prec: ind_liquidita_p, "Unita": "x"},
        {"Indice": "Ind. Solvibilita", "Descrizione": "Totale Attivo / Totale Debiti", "Formula": "Attivo / (Passivo + Debiti)", anno_sel: ind_solvibilita_c, anno_prec: ind_solvibilita_p, "Unita": "x"},
        {"Indice": "Marg. Struttura", "Descrizione": "PN / Cap. Immobilizzato", "Formula": "Patrimonio Netto / Capitale Immobilizzato", anno_sel: marg_strutt_c, anno_prec: marg_strutt_p, "Unita": "x"},
    ]

    df_indici = pd.DataFrame(indici_data)
    df_indici["Var. Ass"] = df_indici[anno_sel] - df_indici[anno_prec]
    df_indici["Var. %"] = df_indici.apply(lambda r: (r["Var. Ass"] / abs(r[anno_prec]) * 100) if r[anno_prec] != 0 else 0, axis=1)

    # Color map
    color_map = {}
    for idx, row in df_indici.iterrows():
        color_map[idx] = get_color_indice(row["Indice"], row[anno_sel])

    def apply_color_map(row):
        color = color_map.get(row.name, "")
        return [f"background-color: {color};" if color else ""] * len(row)

    df_display = pd.DataFrame(index=df_indici.index)
    df_display["Indice"] = df_indici["Indice"]
    df_display["Descrizione"] = df_indici["Descrizione"]
    df_display["Formula"] = df_indici["Formula"]

    for idx, row in df_indici.iterrows():
        if row["Unita"] == "%":
            df_display.at[idx, anno_prec] = f"{row[anno_prec]*100:+.1f}%"
            df_display.at[idx, anno_sel] = f"{row[anno_sel]*100:+.1f}%"
            df_display.at[idx, "Var. Ass"] = f"{row['Var. Ass']*100:+.1f} pp"
            df_display.at[idx, "Var. %"] = f"{row['Var. %']:.1f}%"
        else:
            df_display.at[idx, anno_prec] = f"{row[anno_prec]:.2f}x"
            df_display.at[idx, anno_sel] = f"{row[anno_sel]:.2f}x"
            df_display.at[idx, "Var. Ass"] = f"{row['Var. Ass']:+.2f}x"
            df_display.at[idx, "Var. %"] = f"{row['Var. %']:.1f}%"

    df_display["Unita"] = df_indici["Unita"]

    st.dataframe(df_display.style.apply(apply_color_map, axis=1), use_container_width=True, hide_index=True)

    # --- RADAR ---
    st.divider()
    st.subheader("📊 Confronto Visivo Indici")

    categories = ["ROE", "ROI", "ROS", "Marg. Lordo", "Liquidita", "Solvibilita", "Marg. Struttura"]
    values_c = [
        min(max(roe_c * 500, 0), 100),
        min(max(roi_c * 625, 0), 100),
        min(max(ros_c * 1000, 0), 100),
        min(max(margine_lordo_c * 200, 0), 100),
        min(max(ind_liquidita_c * 50, 0), 100),
        min(max((ind_solvibilita_c - 1) * 100, 0), 100),
        min(max(marg_strutt_c * 33, 0), 100),
    ]
    values_p = [
        min(max(roe_p * 500, 0), 100),
        min(max(roi_p * 625, 0), 100),
        min(max(ros_p * 1000, 0), 100),
        min(max(margine_lordo_p * 200, 0), 100),
        min(max(ind_liquidita_p * 50, 0), 100),
        min(max((ind_solvibilita_p - 1) * 100, 0), 100),
        min(max(marg_strutt_p * 33, 0), 100),
    ]

    fig_radar = create_radar_chart(categories, values_c, values_p, anno_sel, anno_prec)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.caption("""
    **Legenda scala:** ROE 20%→100 | ROI 16%→100 | ROS 10%→100 | Marg.Lordo 50%→100 | 
    Liquidita 2x→100 | Solvibilita 2x→100 | Marg.Struttura 3x→100
    Valori sopra 100 sono troncati a 100 per leggibilita.
    """)

    # --- DATI SOTTOSTANTI ---
    st.divider()
    st.subheader("📎 Dati Sottostanti (per verifica)")
    with st.expander("Clicca per vedere i valori assoluti usati nei calcoli"):
        dati_underlying = [
            {"Voce": "Ricavi", anno_sel: ricavi_c, anno_prec: ricavi_p},
            {"Voce": "EBITDA", anno_sel: ebitda_c, anno_prec: ebitda_p},
            {"Voce": "EBIT", anno_sel: ebit_c, anno_prec: ebit_p},
            {"Voce": "Utile Netto", anno_sel: utile_c, anno_prec: utile_p},
            {"Voce": "Patrimonio Netto", anno_sel: patr_netto_c, anno_prec: patr_netto_p},
            {"Voce": "Capitale Investito", anno_sel: cap_inv_c, anno_prec: cap_inv_p},
            {"Voce": "Totale Attivo", anno_sel: tot_att_c, anno_prec: tot_att_p},
            {"Voce": "Totale Debiti", anno_sel: tot_debiti_c, anno_prec: tot_debiti_p},
            {"Voce": "Passivita Correnti", anno_sel: pass_corr_c, anno_prec: pass_corr_p},
            {"Voce": "Liquidita Immediate", anno_sel: liq_imm_c, anno_prec: liq_imm_p},
            {"Voce": "Cap. Immobilizzato", anno_sel: att_imm_c, anno_prec: att_imm_p},
        ]
        df_under = pd.DataFrame(dati_underlying)
        st.dataframe(df_under.style.format({anno_sel: "€ {:,.0f}", anno_prec: "€ {:,.0f}"}), use_container_width=True, hide_index=True)

        csv = df_under.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Scarica Dati Sottostanti", data=csv, file_name=f"dati_indici_{anno_sel}.csv", mime="text/csv")
