"""
Sofim Financial Dashboard - Pagina Stato Patrimoniale
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import MESI_NOMI
from core.bilancio import calcola_utile_ce, get_saldo_attivo, get_saldo_passivo, get_saldo_passivo_multi, get_saldo_bifurcato, get_fondo, get_saldo_cli_lordo, get_saldo_forn_lordo
from utils.formatting import clean_numeric


def render(df_final: pd.DataFrame) -> None:
    colonna_data = "Data" if "Data" in df_final.columns else "Data Operazione"
    if colonna_data in df_final.columns:
        df_final[colonna_data] = pd.to_datetime(df_final[colonna_data])
        df_final["Mese"] = df_final[colonna_data].dt.month
    else:
        st.error(f"Errore: Colonna '{colonna_data}' non trovata.")
        return

    st.title("📊 Stato Patrimoniale Completo")

    anni = sorted(df_final["Anno"].unique(), reverse=True)
    anno_sel = st.radio("Seleziona l'Anno di Analisi", anni, horizontal=True)
    anno_prec = anno_sel - 1

    mesi_nomi = {i: MESI_NOMI[i-1] for i in range(1, 13)}

    dati_anno = df_final[df_final["Anno"] == anno_sel]
    ultimo_mese_disp = int(dati_anno["Mese"].max()) if not dati_anno.empty else 12
    mese_sel = st.select_slider("Situazione alla fine di:", options=list(mesi_nomi.keys()),
                                format_func=lambda x: mesi_nomi[x], value=ultimo_mese_disp)

    def get_dati_attivo(anno, mese):
        era_att, _ = get_saldo_bifurcato(df_final, "ERARIO", anno, mese)
        banche_att, _ = get_saldo_bifurcato(df_final, "BANCHE", anno, mese)
        return {
            'imm_n': get_saldo_attivo(df_final, "IMIMM", anno, mese) - get_fondo(df_final, "FIMMAT", anno, mese),
            'mat_n': get_saldo_attivo(df_final, "IMMAT", anno, mese) - get_fondo(df_final, "FMAT", anno, mese),
            'fin': get_saldo_attivo(df_final, "IMMFIN", anno, mese),
            'rim': get_saldo_attivo(df_final, "RIM", anno, mese),
            'anf': get_saldo_attivo(df_final, "ANF", anno, mese),
            'cli_n': get_saldo_cli_lordo(df_final, anno, mese),
            'af': get_saldo_attivo(df_final, "AF", anno, mese),
            'era': era_att,
            'aa': get_saldo_attivo(df_final, ["AA", "RRA"], anno, mese),
            'banche': banche_att,
            'dl': get_saldo_attivo(df_final, "DL", anno, mese),
        }

    def get_dati_passivo(anno, mese):
        _, era_pass = get_saldo_bifurcato(df_final, "ERARIO", anno, mese)
        _, banche_pass = get_saldo_bifurcato(df_final, "BANCHE", anno, mese)
        return {
            'utile': calcola_utile_ce(df_final, anno, mese),
            'cs': get_saldo_passivo(df_final, "CS", anno, mese),
            'pn': get_saldo_passivo(df_final, "PN", anno, mese),
            'upn': get_saldo_passivo(df_final, "UPN", anno, mese),
            'dcon': get_saldo_passivo(df_final, "DCON", anno, mese),
            'fmlt': get_saldo_passivo(df_final, "FMLT", anno, mese),
            'fin_p': get_saldo_passivo(df_final, "FIN", anno, mese),
            'soci': get_saldo_passivo(df_final, "SOCI", anno, mese),
            'tfm': get_saldo_passivo(df_final, "TFM", anno, mese),
            'tfr': get_saldo_passivo(df_final, "TFR", anno, mese),
            'fondi': get_saldo_passivo(df_final, "FONDI", anno, mese),
            'b_p': banche_pass,
            'bant': get_saldo_passivo(df_final, "BANT", anno, mese),
            'forn': get_saldo_forn_lordo(df_final, anno, mese),
            'antcli': get_saldo_passivo(df_final, "ANTCLI", anno, mese),
            'era_p': era_pass,
            'prev': get_saldo_passivo(df_final, "PREV", anno, mese),
            'ap': get_saldo_passivo(df_final, "AP", anno, mese),
            'rrp': get_saldo_passivo(df_final, "RRP", anno, mese),
        }

    def style_rows(row):
        n_cols = len(row)
        color_delta = 'color: green;' if row.Variazione > 0 else 'color: red;' if row.Variazione < 0 else 'color: black;'
        is_attivo = any(k in str(row.get('Descrizione', '')).upper() for k in ['ATTIVO', 'INVESTITO', 'IMMOBILIZZATO', 'CIRCOLANTE'])

        if row.Livello in ['H1', 'TOTAL']:
            bg = "#1b5e20" if row.Livello == 'H1' and is_attivo else "#2e7d32" if row.Livello == 'TOTAL' and is_attivo else "#1f4e78" if row.Livello == 'H1' else "#2e75b6"
            return [f'background-color: {bg}; color: white; font-weight: bold; font-size: 13px; height: 35px;'] * n_cols
        if row.Livello == 'H2':
            return ['background-color: #e8f5e9; color: black; font-weight: bold; font-size: 12px; height: 30px;'] * n_cols if is_attivo else ['background-color: #deeaf6; color: black; font-weight: bold; font-size: 12px; height: 30px;'] * n_cols
        if row.Livello == 'SUB':
            stile_s = f'font-size: 10px; color: #666; height: 18px;'
            return [stile_s] * (n_cols - 1) + [f'{stile_s} {color_delta}']
        return ['font-size: 11px; height: 26px;'] * (n_cols - 1) + [f'font-size: 11px; {color_delta}']

    tab_att, tab_pass, tab_check, tab_grafici = st.tabs(["🔹 ATTIVO", "🔸 PASSIVO & NETTO", "🔍 QUADRATURA", "📊 GRAFICI"])

    with tab_att:
        a_c = get_dati_attivo(anno_sel, mese_sel)
        a_p = get_dati_attivo(anno_prec, 12)

        tot_A_c = a_c['imm_n'] + a_c['mat_n'] + a_c['fin']
        tot_A_p = a_p['imm_n'] + a_p['mat_n'] + a_p['fin']
        tot_B_c = a_c['rim'] + a_c['anf'] + a_c['cli_n'] + a_c['af'] + a_c['era'] + a_c['aa'] + a_c['banche'] + a_c['dl']
        tot_B_p = a_p['rim'] + a_p['anf'] + a_p['cli_n'] + a_p['af'] + a_p['era'] + a_p['aa'] + a_p['banche'] + a_p['dl']

        str_a = [
            {"Descrizione": "A) CAPITALE IMMOBILIZZATO", "Corrente": tot_A_c, "Precedente": tot_A_p, "Livello": "H1", "Tipo": None},
            {"Descrizione": "  • Imm. Immateriali (IMIMM)", "Corrente": a_c['imm_n'], "Precedente": a_p['imm_n'], "Livello": "D", "Tipo": "IMIMM"},
            {"Descrizione": "  • Imm. Materiali (IMMAT)", "Corrente": a_c['mat_n'], "Precedente": a_p['mat_n'], "Livello": "D", "Tipo": "IMMAT"},
            {"Descrizione": "  • Imm. Finanziarie (IMMFIN)", "Corrente": a_c['fin'], "Precedente": a_p['fin'], "Livello": "D", "Tipo": "IMMFIN"},
            {"Descrizione": "B) CAPITALE CIRCOLANTE LORDO", "Corrente": tot_B_c, "Precedente": tot_B_p, "Livello": "H1", "Tipo": None},
            {"Descrizione": "  I. RIMANENZE", "Corrente": a_c['rim'] + a_c['anf'], "Precedente": a_p['rim'] + a_p['anf'], "Livello": "H2", "Tipo": None},
            {"Descrizione": "     Materie e Merci (RIM)", "Corrente": a_c['rim'], "Precedente": a_p['rim'], "Livello": "SUB", "Tipo": "RIM"},
            {"Descrizione": "     Anticipi a Fornitori (ANF)", "Corrente": a_c['anf'], "Precedente": a_p['anf'], "Livello": "SUB", "Tipo": "ANF"},
            {"Descrizione": "  II. LIQUIDITA DIFFERITE", "Corrente": a_c['cli_n'] + a_c['af'] + a_c['era'] + a_c['aa'], "Precedente": a_p['cli_n'] + a_p['af'] + a_p['era'] + a_p['aa'], "Livello": "H2", "Tipo": None},
            {"Descrizione": "     Clienti Netti (CLI)", "Corrente": a_c['cli_n'], "Precedente": a_p['cli_n'], "Livello": "SUB", "Tipo": "CLI"},
            {"Descrizione": "     Attivita Finanziarie (AF)", "Corrente": a_c['af'], "Precedente": a_p['af'], "Livello": "SUB", "Tipo": "AF"},
            {"Descrizione": "     Erario (ERARIO)", "Corrente": a_c['era'], "Precedente": a_p['era'], "Livello": "SUB", "Tipo": "ERARIO"},
            {"Descrizione": "     Ratei e Risconti Attivi (AA-RRA)", "Corrente": a_c['aa'], "Precedente": a_p['aa'], "Livello": "SUB", "Tipo": "AA_RRA"},
            {"Descrizione": "  III. LIQUIDITA IMMEDIATE", "Corrente": a_c['banche'] + a_c['dl'], "Precedente": a_p['banche'] + a_p['dl'], "Livello": "H2", "Tipo": None},
            {"Descrizione": "     Banche C/C (BANCHE)", "Corrente": a_c['banche'], "Precedente": a_p['banche'], "Livello": "SUB", "Tipo": "BANCHE"},
            {"Descrizione": "     Cassa e Valori (DL)", "Corrente": a_c['dl'], "Precedente": a_p['dl'], "Livello": "SUB", "Tipo": "DL"},
            {"Descrizione": "TOTALE CAPITALE INVESTITO", "Corrente": tot_A_c + tot_B_c, "Precedente": tot_A_p + tot_B_p, "Livello": "TOTAL", "Tipo": None}
        ]

        df_a = pd.DataFrame(str_a)
        df_a["Variazione"] = df_a["Corrente"] - df_a["Precedente"]

        detail_container_att = st.empty()
        event_att = st.dataframe(
            df_a.style.apply(style_rows, axis=1).format({"Corrente": "€ {:,.2f}", "Precedente": "€ {:,.2f}", "Variazione": "€ {:+,.2f}"}).hide(axis='index'),
            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="sp_attivo_select"
        )

        if event_att.selection.rows:
            idx_sel = event_att.selection.rows[0]
            row_sel = df_a.iloc[idx_sel]
            tipo_sel = row_sel["Tipo"]
            _render_drill_down_attivo(df_final, detail_container_att, tipo_sel, row_sel, anno_sel, anno_prec, mese_sel, mesi_nomi)

    with tab_pass:
        p_c = get_dati_passivo(anno_sel, mese_sel)
        p_p = get_dati_passivo(anno_prec, 12)

        tot_proprio_c = p_c['cs'] + p_c['pn'] + p_c['upn'] + p_c.get('utile', 0.0)
        tot_proprio_p = p_p['cs'] + p_p['pn'] + p_p['upn'] + p_p.get('utile', 0.0)
        tot_cons_c = p_c['dcon'] + p_c['fmlt'] + p_c['fin_p'] + p_c['soci'] + p_c['tfm'] + p_c['tfr'] + p_c['fondi']
        tot_cons_p = p_p['dcon'] + p_p['fmlt'] + p_p['fin_p'] + p_p['soci'] + p_p['tfm'] + p_p['tfr'] + p_p['fondi']
        tot_corr_c = p_c['b_p'] + p_c['bant'] + p_c['forn'] + p_c['antcli'] + p_c['era_p'] + p_c['prev'] + p_c['ap'] + p_c['rrp']
        tot_corr_p = p_p['b_p'] + p_p['bant'] + p_p['forn'] + p_p['antcli'] + p_p['era_p'] + p_p['prev'] + p_p['ap'] + p_p['rrp']

        str_p = [
            {"Descrizione": "CAPITALE PROPRIO", "Corrente": tot_proprio_c, "Precedente": tot_proprio_p, "Livello": "H1", "Tipo": None},
            {"Descrizione": "   Capitale apportato", "Corrente": p_c['cs'], "Precedente": p_p['cs'], "Livello": "SUB", "Tipo": "CS"},
            {"Descrizione": "   Riserve", "Corrente": p_c['pn'], "Precedente": p_p['pn'], "Livello": "SUB", "Tipo": "PN"},
            {"Descrizione": "   Utili/perdite es. prec.", "Corrente": p_c['upn'], "Precedente": p_p['upn'], "Livello": "SUB", "Tipo": "UPN"},
            {"Descrizione": "   Utile/perdita d'esercizio", "Corrente": p_c.get('utile', 0.0), "Precedente": p_p.get('utile', 0.0), "Livello": "SUB", "Tipo": "UTILE"},
            {"Descrizione": "PASSIVITA CONSOLIDATE", "Corrente": tot_cons_c, "Precedente": tot_cons_p, "Livello": "H1", "Tipo": None},
            {"Descrizione": "   Finanziamenti (FIN)", "Corrente": p_c['fin_p'], "Precedente": p_p['fin_p'], "Livello": "SUB", "Tipo": "FIN"},
            {"Descrizione": "   Debiti v/soci", "Corrente": p_c['soci'], "Precedente": p_p['soci'], "Livello": "SUB", "Tipo": "SOCI"},
            {"Descrizione": "   TFR", "Corrente": p_c['tfr'], "Precedente": p_p['tfr'], "Livello": "SUB", "Tipo": "TFR"},
            {"Descrizione": "   TFM", "Corrente": p_c['tfm'], "Precedente": p_p['tfm'], "Livello": "SUB", "Tipo": "TFM"},
            {"Descrizione": "   Fondi", "Corrente": p_c['fondi'], "Precedente": p_p['fondi'], "Livello": "SUB", "Tipo": "FONDI"},
            {"Descrizione": "PASSIVITA CORRENTI", "Corrente": tot_corr_c, "Precedente": tot_corr_p, "Livello": "H1", "Tipo": None},
            {"Descrizione": "   Debiti verso banche c/c (BANCHE)", "Corrente": p_c['b_p'], "Precedente": p_p['b_p'], "Livello": "SUB", "Tipo": "BANCHE"},
            {"Descrizione": "   Debiti verso banche anticipi (BANT)", "Corrente": p_c['bant'], "Precedente": p_p['bant'], "Livello": "SUB", "Tipo": "BANT"},
            {"Descrizione": "   Debiti verso fornitori netti (FORN + FOCF)", "Corrente": p_c['forn'], "Precedente": p_p['forn'], "Livello": "SUB", "Tipo": "FORN_FOCF"},
            {"Descrizione": "   Anticipi da clienti (ANTCLI)", "Corrente": p_c['antcli'], "Precedente": p_p['antcli'], "Livello": "SUB", "Tipo": "ANTCLI"},
            {"Descrizione": "   Debiti tributari (ERARIO)", "Corrente": p_c['era_p'], "Precedente": p_p['era_p'], "Livello": "SUB", "Tipo": "ERARIO"},
            {"Descrizione": "   Altri debiti (AP)", "Corrente": p_c['ap'], "Precedente": p_p['ap'], "Livello": "SUB", "Tipo": "AP"},
            {"Descrizione": "   Ratei e risconti passivi (RRP)", "Corrente": p_c['rrp'], "Precedente": p_p['rrp'], "Livello": "SUB", "Tipo": "RRP"},
            {"Descrizione": "   Debiti previdenziali (PREV)", "Corrente": p_c['prev'], "Precedente": p_p['prev'], "Livello": "SUB", "Tipo": "PREV"},
            {"Descrizione": "CAPITALE DI TERZI", "Corrente": tot_cons_c + tot_corr_c, "Precedente": tot_cons_p + tot_corr_p, "Livello": "H2", "Tipo": None},
            {"Descrizione": "TOTALE PASSIVO E NETTO", "Corrente": tot_proprio_c + tot_cons_c + tot_corr_c, "Precedente": tot_proprio_p + tot_cons_p + tot_corr_p, "Livello": "TOTAL", "Tipo": None}
        ]

        df_p = pd.DataFrame(str_p)
        df_p["Variazione"] = df_p["Corrente"] - df_p["Precedente"]
        col_order = ["Descrizione", "Corrente", "Precedente", "Variazione", "Livello", "Tipo"]
        df_p = df_p[col_order]

        detail_container = st.empty()
        event = st.dataframe(
            df_p.style.apply(style_rows, axis=1).format({"Corrente": "€ {:,.2f}", "Precedente": "€ {:,.2f}", "Variazione": "€ {:+,.2f}"}).hide(axis='index'),
            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="sp_passivo_select"
        )

        if event.selection.rows:
            idx_sel = event.selection.rows[0]
            row_sel = df_p.iloc[idx_sel]
            tipo_sel = row_sel["Tipo"]
            _render_drill_down_passivo(df_final, detail_container, tipo_sel, row_sel, anno_sel, anno_prec, mese_sel, mesi_nomi)

    with tab_check:
        st.subheader("Verifica di Bilancio")
        tot_att = tot_A_c + tot_B_c
        tot_pass = tot_proprio_c + tot_cons_c + tot_corr_c
        diff = tot_att - tot_pass
        c1, c2, c3 = st.columns(3)
        c1.metric("Totale Attivo", f"€ {tot_att:,.2f}")
        c2.metric("Totale Passivo", f"€ {tot_pass:,.2f}")
        if abs(diff) < 0.1:
            c3.success("BILANCIO QUADRATO")
        else:
            c3.error(f"SQUILIBRIO: € {diff:,.2f}")
            _render_diagnostica(df_final, p_c, tot_att, tot_pass, diff, anno_sel, mese_sel)

    with tab_grafici:
        _render_grafici(tot_A_c, a_c, tot_proprio_c, tot_cons_c, tot_corr_c)


def _render_drill_down_cli_attivo(df_final, anno_sel, mese_sel, mesi_nomi):
    """
    Drill-down specifico per CLI (Clienti):
    - Prima riga: conti con codice 'CLIENTI' aggregati, descrizione 'Crediti vs clienti'
    - Poi: tutti gli altri conti CLI individuali, anche con saldo avere
    """
    st.divider()
    st.subheader("🔍 Dettaglio Clienti")
    st.info("Visualizzazione di tutti i conti mappati con tipo CLI.")

    sub_c = df_final[
        (df_final["Anno"] == anno_sel) &
        (df_final["Mese_Num"] <= mese_sel) &
        (df_final["Tipo"].astype(str).str.strip() == "CLI")
    ].copy()

    if sub_c.empty:
        st.info("Nessun dato disponibile per tipo CLI.")
        if st.button("Chiudi Dettaglio ❌", key="close_att_cli"): st.rerun()
        return

    sub_c["D"] = pd.to_numeric(sub_c["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub_c["A"] = pd.to_numeric(sub_c["Avere"].apply(clean_numeric), errors='coerce').fillna(0)

    # Aggrega per Codice Conto
    det_c = sub_c.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
    det_c["Saldo"] = det_c["D"] - det_c["A"]

    # Separa conti CLIENTI dagli altri
    pattern_clienti = det_c["Codice Conto"].str.upper().str.strip() == "CLIENTI"
    clienti_rows = det_c[pattern_clienti].copy()
    altri_rows = det_c[~pattern_clienti].copy()

    # Crea riga aggregata per CLIENTI
    rows_to_show = []
    if not clienti_rows.empty:
        totale_clienti = clienti_rows["Saldo"].sum()
        rows_to_show.append({
            "Codice Conto": "CLIENTI",
            "Descrizione Conto": "Crediti vs clienti",
            "D": clienti_rows["D"].sum(),
            "A": clienti_rows["A"].sum(),
            "Saldo": totale_clienti,
            "Is_Aggregato": True
        })

    # Aggiungi gli altri conti CLI
    for _, row in altri_rows.iterrows():
        rows_to_show.append({
            "Codice Conto": row["Codice Conto"],
            "Descrizione Conto": row["Descrizione Conto"],
            "D": row["D"],
            "A": row["A"],
            "Saldo": row["Saldo"],
            "Is_Aggregato": False
        })

    if not rows_to_show:
        st.info("Nessun conto CLI con movimenti.")
        if st.button("Chiudi Dettaglio ❌", key="close_att_cli2"): st.rerun()
        return

    df_show = pd.DataFrame(rows_to_show)

    def style_cli(row):
        if row.get("Is_Aggregato"):
            return ['background-color: #fff3cd; font-weight: bold;'] * len(row)
        return [''] * len(row)

    st.markdown(f"**Anno {anno_sel} (fino a {mesi_nomi[mese_sel]})**")
    st.dataframe(
        df_show.style.apply(style_cli, axis=1).format({
            "D": "€ {:,.2f}", "A": "€ {:,.2f}", "Saldo": "€ {:+,.2f}"
        }).map(
            lambda v: 'color: green; font-weight: bold;' if v > 0 else ('color: red; font-weight: bold;' if v < 0 else ''),
            subset=["Saldo"]
        ),
        use_container_width=True, hide_index=True
    )

    # Totale
    totale = df_show["Saldo"].sum()
    st.markdown(f"**TOTALE CLI: € {totale:,.2f}**")

    if st.button("Chiudi Dettaglio ❌", key="close_att_cli3"): st.rerun()


def _render_drill_down_attivo(df_final, container, tipo_sel, row_sel, anno_sel, anno_prec, mese_sel, mesi_nomi):
    if not tipo_sel:
        return
    with container.container():
        st.divider()
        st.subheader(f"🔍 Dettaglio: {row_sel['Descrizione'].strip()}")
        if tipo_sel == "BANCHE":
            st.info("Solo i conti bancari con saldo DARE > AVERE (disponibilità).")
        elif tipo_sel == "ERARIO":
            st.info("Solo i conti con saldo DARE > AVERE (crediti verso l'erario).")
        elif tipo_sel == "AA_RRA":
            st.info("Ratei e risconti attivi sono composti dai tipi AA e RRA.")

        if tipo_sel == "AA_RRA":
            tipi_query = ["AA", "RRA"]
        elif tipo_sel == "CLI":
            # DRILL-DOWN SPECIFICO PER CLIENTI
            _render_drill_down_cli_attivo(df_final, anno_sel, mese_sel, mesi_nomi)
            return
        else:
            tipi_query = [tipo_sel]

        sub_c = df_final[
            (df_final["Anno"] == anno_sel) &
            (df_final["Mese_Num"] <= mese_sel) &
            (df_final["Tipo"].astype(str).str.strip().isin(tipi_query))
        ].copy()

        if not sub_c.empty:
            sub_c["D"] = pd.to_numeric(sub_c["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
            sub_c["A"] = pd.to_numeric(sub_c["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
            if tipo_sel == "FORN_FOCF":
                det_c = sub_c.groupby("Codice Conto").agg({"D": "sum", "A": "sum", "Descrizione Conto": "first"}).reset_index()
            else:
                det_c = sub_c.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
            det_c["Saldo"] = det_c["D"] - det_c["A"]
            if tipo_sel in ["BANCHE", "ERARIO"]:
                det_c = det_c[det_c["Saldo"] > 0]
            else:
                det_c = det_c[det_c["Saldo"] != 0]
            det_c = det_c.sort_values("Saldo", ascending=False)
            if not det_c.empty:
                st.dataframe(det_c.style.format({"D": "€ {:,.2f}", "A": "€ {:,.2f}", "Saldo": "€ {:+,.2f}"})
                    .map(lambda v: 'color: green; font-weight: bold;' if v > 0 else ('color: red; font-weight: bold;' if v < 0 else ''), subset=["Saldo"]),
                    use_container_width=True, hide_index=True)
            else:
                st.info("Nessun conto con saldo corrispondente.")
        else:
            st.info("Nessun dato disponibile.")
        if st.button("Chiudi Dettaglio ❌", key=f"close_att_{tipo_sel}"): st.rerun()


def _render_drill_down_forn_passivo(df_final, anno_sel, mese_sel, mesi_nomi):
    """
    Drill-down specifico per FORN/FOCF (Fornitori):
    - Prima riga: TUTTI i conti con Codice Conto esatto 'FORN' (case-insensitive) aggregati
      in un'unica riga con codice FORN, descrizione 'Debiti vs fornitori'
    - Poi: gli altri conti mappati con tipo FORN/FOCF ma con codice conto diverso da 'FORN',
      indicati individualmente, anche con saldo dare
    """
    st.divider()
    st.subheader("🔍 Dettaglio Fornitori")
    st.info("Visualizzazione di tutti i conti mappati con tipo FORN o FOCF.")

    sub_c = df_final[
        (df_final["Anno"] == anno_sel) &
        (df_final["Mese_Num"] <= mese_sel) &
        (df_final["Tipo"].astype(str).str.strip().isin(["FORN", "FOCF"]))
    ].copy()

    if sub_c.empty:
        st.info("Nessun dato disponibile per tipo FORN/FOCF.")
        if st.button("Chiudi Dettaglio ❌", key="close_pass_forn"): st.rerun()
        return

    sub_c["D"] = pd.to_numeric(sub_c["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub_c["A"] = pd.to_numeric(sub_c["Avere"].apply(clean_numeric), errors='coerce').fillna(0)

    # Aggrega per Codice Conto
    det_c = sub_c.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
    det_c["Saldo"] = det_c["A"] - det_c["D"]

    # Separa conti con Codice Conto ESATTO "FORN" (case-insensitive) dagli altri
    pattern_forn = det_c["Codice Conto"].str.upper().str.strip() == "FORN"
    forn_rows = det_c[pattern_forn].copy()
    altri_rows = det_c[~pattern_forn].copy()

    # Crea riga aggregata per FORN (tutti i conti con codice esatto FORN)
    rows_to_show = []
    if not forn_rows.empty:
        totale_forn = forn_rows["Saldo"].sum()
        rows_to_show.append({
            "Codice Conto": "FORN",
            "Descrizione Conto": "Debiti vs fornitori",
            "D": forn_rows["D"].sum(),
            "A": forn_rows["A"].sum(),
            "Saldo": totale_forn,
            "Is_Aggregato": True
        })

    # Aggiungi gli altri conti FORN/FOCF (codice diverso da FORN)
    for _, row in altri_rows.iterrows():
        rows_to_show.append({
            "Codice Conto": row["Codice Conto"],
            "Descrizione Conto": row["Descrizione Conto"],
            "D": row["D"],
            "A": row["A"],
            "Saldo": row["Saldo"],
            "Is_Aggregato": False
        })

    if not rows_to_show:
        st.info("Nessun conto FORN/FOCF con movimenti.")
        if st.button("Chiudi Dettaglio ❌", key="close_pass_forn2"): st.rerun()
        return

    df_show = pd.DataFrame(rows_to_show)

    def style_forn(row):
        if row.get("Is_Aggregato"):
            return ['background-color: #fff3cd; font-weight: bold;'] * len(row)
        return [''] * len(row)

    st.markdown(f"**Anno {anno_sel} (fino a {mesi_nomi[mese_sel]})**")
    st.dataframe(
        df_show.style.apply(style_forn, axis=1).format({
            "D": "€ {:,.2f}", "A": "€ {:,.2f}", "Saldo": "€ {:+,.2f}"
        }).map(
            lambda v: 'color: green; font-weight: bold;' if v > 0 else ('color: red; font-weight: bold;' if v < 0 else ''),
            subset=["Saldo"]
        ),
        use_container_width=True, hide_index=True
    )

    # Totale
    totale = df_show["Saldo"].sum()
    st.markdown(f"**TOTALE FORN/FOCF: € {totale:,.2f}**")

    if st.button("Chiudi Dettaglio ❌", key="close_pass_forn3"): st.rerun()


def _render_drill_down_passivo(df_final, container, tipo_sel, row_sel, anno_sel, anno_prec, mese_sel, mesi_nomi):
    if not tipo_sel:
        return
    with container.container():
        st.divider()
        st.subheader(f"🔍 Dettaglio: {row_sel['Descrizione'].strip()}")
        if tipo_sel == "UTILE":
            st.info("L'utile/perdita è calcolato dal Conto Economico. Vai alla pagina 📈 Conto Economico per il dettaglio.")
            if st.button("Chiudi ❌", key="close_utile"): st.rerun()
            return

        if tipo_sel == "FORN_FOCF":
            # DRILL-DOWN SPECIFICO PER FORNITORI
            _render_drill_down_forn_passivo(df_final, anno_sel, mese_sel, mesi_nomi)
            return
        else:
            tipi_query = [tipo_sel]

        sub_c = df_final[
            (df_final["Anno"] == anno_sel) &
            (df_final["Mese_Num"] <= mese_sel) &
            (df_final["Tipo"].astype(str).str.strip().isin(tipi_query))
        ].copy()

        if not sub_c.empty:
            sub_c["D"] = pd.to_numeric(sub_c["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
            sub_c["A"] = pd.to_numeric(sub_c["Avere"].apply(clean_numeric), errors='coerce').fillna(0)

            if tipo_sel in ["BANCHE", "ERARIO"]:
                det_c = sub_c.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
                det_c["Saldo"] = det_c["A"] - det_c["D"]
                det_c = det_c[det_c["Saldo"] > 0].sort_values("Saldo", ascending=False)
            else:
                det_c = sub_c.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
                det_c["Saldo"] = det_c["A"] - det_c["D"]
                det_c = det_c[det_c["Saldo"] != 0].sort_values("Saldo", ascending=False)

            if not det_c.empty:
                st.markdown(f"**Anno {anno_sel} (fino a {mesi_nomi[mese_sel]})**")
                st.dataframe(det_c.style.format({"D": "€ {:,.2f}", "A": "€ {:,.2f}", "Saldo": "€ {:+,.2f}"})
                    .map(lambda v: 'color: green; font-weight: bold;' if v > 0 else ('color: red; font-weight: bold;' if v < 0 else ''), subset=["Saldo"]),
                    use_container_width=True, hide_index=True)
            else:
                st.info("Nessun conto con saldo corrispondente.")
        else:
            st.info("Nessun dato disponibile per la selezione.")
        if st.button("Chiudi Dettaglio ❌", key=f"close_pass_{tipo_sel}"): st.rerun()


def _render_diagnostica(df_final, p_c, tot_att, tot_pass, diff, anno_sel, mese_sel):
    st.divider()
    st.subheader("🔍 Diagnostica Squadratura")
    st.info("Il bilancio non quadra. Ecco le possibili cause e i controlli da fare:")

    diagnostic_data = []
    utile_ce = calcola_utile_ce(df_final, anno_sel, mese_sel)
    utile_sp = p_c.get('utile', 0.0)
    diagnostic_data.append({
        "Controllo": "Utile CE vs Utile SP",
        "Valore CE": utile_ce, "Valore SP": utile_sp,
        "Differenza": utile_ce - utile_sp,
        "Stato": "✅ OK" if abs(utile_ce - utile_sp) < 0.1 else "⚠️ DISALLINEATO"
    })

    banche_att = get_saldo_attivo(df_final, "BANCHE", anno_sel, mese_sel)
    banche_pass = get_saldo_passivo(df_final, "BANCHE", anno_sel, mese_sel)
    diagnostic_data.append({
        "Controllo": "Banche Attivo vs Passivo",
        "Valore CE": banche_att, "Valore SP": banche_pass,
        "Differenza": banche_att - banche_pass, "Stato": "ℹ️ INFO"
    })

    causes = [
        "1. **Conti con saldo ZERO**: Se un conto ha D=A esatto, non viene contato né in attivo né in passivo.",
        "2. **Segni invertiti**: Verifica che i tipi 'BANCHE', 'ERARIO', 'CLI' siano classificati correttamente.",
        "3. **Utile d'esercizio**: L'utile nel SP è calcolato da Categoria (RICAVI/COSTI), non da Tipo.",
        "4. **Fondi ammortamento**: I fondi (FMAT, FIMMAT) sono sottratti dalle immobilizzazioni.",
        "5. **Ratei e risconti**: I tipi 'AA', 'RRA' vanno in attivo; 'RRP', 'AP' vanno in passivo.",
    ]
    for cause in causes:
        st.markdown(cause)

    st.markdown("#### 📊 Dettaglio Controlli Automatici")
    df_diag = pd.DataFrame(diagnostic_data)
    st.dataframe(df_diag.style.format({"Valore CE": "€ {:,.2f}", "Valore SP": "€ {:,.2f}", "Differenza": "€ {:+,.2f}"}),
                 use_container_width=True, hide_index=True)

    st.markdown("#### 🧮 Scomposizione dello Squilibrio")
    st.write(f"**Totale Attivo:** € {tot_att:,.2f}")
    st.write(f"**Totale Passivo + PN:** € {tot_pass:,.2f}")
    st.write(f"**Differenza:** € {diff:,.2f}")
    st.write(f"**Utile d'esercizio (SP):** € {p_c.get('utile', 0.0):,.2f}")


def _render_grafici(tot_A_c, a_c, tot_proprio_c, tot_cons_c, tot_corr_c):
    immob = tot_A_c
    rimanenze = a_c['rim'] + a_c['anf']
    liq_diff = a_c['cli_n'] + a_c['af'] + a_c['era'] + a_c['aa']
    liq_imm = a_c['banche'] + a_c['dl']
    p_netto = tot_proprio_c
    pass_cons = tot_cons_c
    pass_corr = tot_corr_c

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.write("**Composizione Attivo**")
        fig_a = go.Figure(data=[go.Pie(
            labels=['Cap. Immobilizzato', 'Rimanenze', 'Liq. Differite', 'Liq. Immediate'],
            values=[immob, rimanenze, liq_diff, liq_imm],
            hole=.4, marker_colors=['#1f4e78', '#2e75b6', '#bdd7ee', '#ffc000']
        )])
        fig_a.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_a, use_container_width=True)

    with col_g2:
        st.write("**Composizione Passivo**")
        fig_p = go.Figure(data=[go.Pie(
            labels=['Patrimonio Netto', 'Pass. Consolidate', 'Pass. Correnti'],
            values=[p_netto, pass_cons, pass_corr],
            hole=.4, marker_colors=['#c00000', '#ed7d31', '#ffcc00']
        )])
        fig_p.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")
    st.write("**Equilibrio tra Impieghi e Fonti (Valori Assoluti)**")
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(name='Immobilizzazioni', x=['ATTIVO'], y=[immob], marker_color='#1f4e78'))
    fig_stack.add_trace(go.Bar(name='Rimanenze', x=['ATTIVO'], y=[rimanenze], marker_color='#2e75b6'))
    fig_stack.add_trace(go.Bar(name='Liq. Differite', x=['ATTIVO'], y=[liq_diff], marker_color='#bdd7ee'))
    fig_stack.add_trace(go.Bar(name='Liq. Immediate', x=['ATTIVO'], y=[liq_imm], marker_color='#ffc000'))
    fig_stack.add_trace(go.Bar(name='Patrimonio Netto', x=['PASSIVO'], y=[p_netto], marker_color='#c00000'))
    fig_stack.add_trace(go.Bar(name='Passivita Consolidate', x=['PASSIVO'], y=[pass_cons], marker_color='#ed7d31'))
    fig_stack.add_trace(go.Bar(name='Passivita Correnti', x=['PASSIVO'], y=[pass_corr], marker_color='#ffcc00'))
    fig_stack.update_layout(barmode='stack', height=500, template="plotly_white",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_stack.update_traces(texttemplate='%{y:,.2s}€', textposition='inside')
    st.plotly_chart(fig_stack, use_container_width=True)
