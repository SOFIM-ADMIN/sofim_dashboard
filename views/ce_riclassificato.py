"""
Sofim Financial Dashboard - Pagina Conto Economico Riclassificato
"""

import streamlit as st
import pandas as pd
from utils.formatting import clean_numeric


def render(df_final: pd.DataFrame) -> None:
    st.title("📈 Conto Economico Analitico")

    anni = sorted(df_final["Anno"].unique())
    if not anni:
        st.warning("Nessun dato disponibile.")
        return

    anno_sel = st.selectbox("Seleziona Anno di Analisi", anni, index=len(anni)-1)
    anno_prec = anno_sel - 1

    df_curr = df_final[df_final["Anno"] == anno_sel]
    df_prev = df_final[df_final["Anno"] == anno_prec]

    def get_v(codice):
        return df_curr[df_curr["Tipo"] == codice]["Importo_Netto"].sum(), df_prev[df_prev["Tipo"] == codice]["Importo_Netto"].sum()

    def get_v_list(lista):
        return df_curr[df_curr["Tipo"].isin(lista)]["Importo_Netto"].sum(), df_prev[df_prev["Tipo"].isin(lista)]["Importo_Netto"].sum()

    f_c, f_p = get_v_list(["VE", "VE1", "VE2", "RIA"])
    f_c, f_p = abs(f_c), abs(f_p)

    cv_c, cv_p = get_v_list(["RI", "ME", "ME1", "ME2", "LA", "CP", "RF"])
    mc_c, mc_p = f_c + cv_c, f_p + cv_p

    ap_c, ap_p = get_v("AR")
    cvar_c, cvar_p = get_v_list(["CC", "UTE", "MANUT", "AUTOM"])
    mcont_c, mcont_p = mc_c + abs(ap_c) + cvar_c, mc_p + abs(ap_p) + cvar_p

    serv_c, serv_p = get_v_list(["AMMRE", "AUTO", "UT", "CC1", "CA", "CG", "IMP", "OD", "GOD"])
    va_c, va_p = mcont_c + serv_c, mcont_p + serv_p

    pe_c, pe_p = get_v("PE")
    ebitda_c, ebitda_p = va_c + pe_c, va_p + pe_p

    amm_c, amm_p = get_v_list(["AMMMAT", "AMIMMAT", "PEC", "ACFR"])
    ebit_c, ebit_p = ebitda_c + amm_c, ebitda_p + amm_p

    fin_c, fin_p = get_v_list(["PF", "OF"])
    rord_c, rord_p = ebit_c + fin_c, ebit_p + fin_p

    stra_c, stra_p = get_v_list(["PS", "OS"])
    ebt_c, ebt_p = rord_c + stra_c, rord_p + stra_p

    imp_c, imp_p = get_v_list(["IR", "IRD"])
    utile_c, utile_p = ebt_c + imp_c, ebt_p + imp_p

    def r(voce, tipo, vals, stile=""):
        return {"Voce": voce, "Tipo": tipo, "Val_C": vals[0], "Val_P": vals[1], "Stile": stile}

    struttura = [
        r("FATTURATO", "VE", (f_c, f_p), "M"),
        r("   Vendite bene 1", "VE", (abs(get_v("VE")[0]), abs(get_v("VE")[1]))),
        r("   Vendite bene 2", "VE1", (abs(get_v("VE1")[0]), abs(get_v("VE1")[1]))),
        r("   Vendite bene 3", "VE2", (abs(get_v("VE2")[0]), abs(get_v("VE2")[1]))),
        r("   Riaddebiti", "RIA", (abs(get_v("RIA")[0]), abs(get_v("RIA")[1]))),

        r("Costo del venduto", "", (cv_c, cv_p), "S"),
        r("   (Rimanenze iniziali)", "RI", get_v("RI")),
        r("   (Acquisti bene 1)", "ME", get_v("ME")),
        r("   (Acquisti bene 2)", "ME1", get_v("ME1")),
        r("   (Acquisti bene 3)", "ME2", get_v("ME2")),
        r("   (Lavorazioni esterne)", "LA", get_v("LA")),
        r("   (Altri costi di produzione)", "CP", get_v("CP")),
        r("   (Rimanenze finali)", "RF", get_v("RF")),

        r("MARGINE COMMERCIALE", "", (mc_c, mc_p), "M"),
        r("Altri proventi ordinari", "AR", (abs(ap_c), abs(ap_p))),

        r("Costi variabili di produzione", "", (cvar_c, cvar_p), "S"),
        r("   (Trasporti - costi commerciali)", "CC", get_v("CC")),
        r("   (Energia elettrica)", "UTE", get_v("UTE")),
        r("   (Manutenzioni e riparazioni)", "MANUT", get_v("MANUT")),
        r("   (Costo automezzi)", "AUTOM", get_v("AUTOM")),

        r("MARGINE DI CONTRIBUZIONE", "", (mcont_c, mcont_p), "M"),

        r("Servizi e spese operative", "", (serv_c, serv_p), "S"),
        r("   (Costo amministratori)", "AMMRE", get_v("AMMRE")),
        r("   (Costo autovetture)", "AUTO", get_v("AUTO")),
        r("   (Utenze)", "UT", get_v("UT")),
        r("   (Servizi commerciali)", "CC1", get_v("CC1")),
        r("   (Servizi amministrativi)", "CA", get_v("CA")),
        r("   (Servizi generali)", "CG", get_v("CG")),
        r("   (Imposte e tasse)", "IMP", get_v("IMP")),
        r("   (Oneri diversi di gestione)", "OD", get_v("OD")),
        r("   (Godimento beni di terzi)", "GOD", get_v("GOD")),

        r("VALORE AGGIUNTO", "", (va_c, va_p), "M"),
        r("   (Costo del lavoro)", "PE", (pe_c, pe_p)),

        r("MARGINE OPERATIVO LORDO", "", (ebitda_c, ebitda_p), "M"),
        r("   (Ammortamenti materiali)", "AMMMAT", get_v("AMMMAT")),
        r("   (Ammortamenti immateriali)", "AMIMMAT", get_v("AMIMMAT")),
        r("   (Svalutazione crediti)", "PEC", get_v("PEC")),
        r("   (Accantonamento fondo rischi)", "ACFR", get_v("ACFR")),

        r("UTILE OPERATIVO NETTO", "", (ebit_c, ebit_p), "M"),
        r("Proventi finanziari", "PF", (abs(get_v("PF")[0]), abs(get_v("PF")[1]))),
        r("   (Oneri finanziari)", "OF", get_v("OF")),

        r("RISULTATO ORDINARIO", "", (rord_c, rord_p), "M"),
        r("Proventi straordinari netti", "PS", get_v("PS")),
        r("   Oneri straordinari netti", "OS", get_v("OS")),

        r("UTILE PRIMA DELLE IMPOSTE", "", (ebt_c, ebt_p), "M"),
        r("   (Imposte sul reddito)", "IR", get_v_list(["IR", "IRD"])),

        r("UTILE NETTO", "", (utile_c, utile_p), "R")
    ]
    df_base = pd.DataFrame(struttura)

    def style_rows(row):
        if row["Stile"] == "M": s = 'color: #d32f2f; font-weight: bold; background-color: #f8f9fa;'
        elif row["Stile"] == "S": s = 'color: #1976d2; font-weight: bold; background-color: #e3f2fd;'
        elif row["Stile"] == "R": s = 'background-color: #0d47a1; color: white; font-weight: bold;'
        else: s = ''
        return [s] * len(row)

    container_drill = st.empty()
    tab1, tab2 = st.tabs(["💶 Valori Assoluti", "📊 Incidenze %"])
    tipo_selezionato = None

    with tab1:
        df1 = df_base.copy()
        df1["Var. Abs"] = df1["Val_C"] - df1["Val_P"]
        df1["Var. %"] = df1.apply(lambda x: (x["Var. Abs"]/abs(x["Val_P"])*100) if x["Val_P"] != 0 else 0, axis=1)

        styler1 = df1.style.apply(style_rows, axis=1).format({
            "Val_C": "€ {:,.2f}", "Val_P": "€ {:,.2f}", "Var. Abs": "€ {:,.2f}", "Var. %": "{:.1f}%"
        })

        sel1 = st.dataframe(
            styler1, use_container_width=True, hide_index=True, on_select="rerun",
            selection_mode="single-row", key="tab_euro",
            column_order=["Voce", "Tipo", "Val_C", "Val_P", "Var. Abs", "Var. %"]
        )
        if sel1.selection.rows:
            tipo_selezionato = df_base.iloc[sel1.selection.rows[0]]["Tipo"]

    with tab2:
        df2 = df_base.copy()
        df2["Val_C"] = df2["Val_C"].apply(lambda x: (x / f_c * 100) if f_c != 0 else 0)
        df2["Val_P"] = df2["Val_P"].apply(lambda x: (x / f_p * 100) if f_p != 0 else 0)
        df2["Scost. PT"] = df2["Val_C"] - df2["Val_P"]

        styler2 = df2.style.apply(style_rows, axis=1).format({
            "Val_C": "{:.2f}%", "Val_P": "{:.2f}%", "Scost. PT": "{:+.2f}%"
        })

        sel2 = st.dataframe(
            styler2, use_container_width=True, hide_index=True, on_select="rerun",
            selection_mode="single-row", key="tab_perc",
            column_order=["Voce", "Tipo", "Val_C", "Val_P", "Scost. PT"]
        )
        if sel2.selection.rows:
            tipo_selezionato = df_base.iloc[sel2.selection.rows[0]]["Tipo"]

    if tipo_selezionato:
        t_clean = str(tipo_selezionato).strip()
        if t_clean:
            with container_drill.container():
                st.subheader(f"🔍 Dettaglio Conti: {t_clean}")
                d_c = df_curr[df_curr["Tipo"] == t_clean].groupby(["Codice Conto", "Descrizione Conto"])["Importo_Netto"].sum().reset_index()
                d_p = df_prev[df_prev["Tipo"] == t_clean].groupby(["Codice Conto", "Descrizione Conto"])["Importo_Netto"].sum().reset_index()

                merged = pd.merge(d_c, d_p, on=["Codice Conto", "Descrizione Conto"], how="outer", suffixes=('_c', '_p')).fillna(0)
                merged["Diff"] = merged["Importo_Netto_c"] - merged["Importo_Netto_p"]

                tot_row = pd.DataFrame([{
                    "Codice Conto": "TOTALE", "Descrizione Conto": "",
                    "Importo_Netto_c": merged["Importo_Netto_c"].sum(),
                    "Importo_Netto_p": merged["Importo_Netto_p"].sum(),
                    "Diff": merged["Diff"].sum(), "Is_T": True
                }])
                merged["Is_T"] = False
                final_d = pd.concat([merged, tot_row], ignore_index=True)

                st.dataframe(
                    final_d.style.apply(lambda x: ['background: #34495e; color: white; font-weight: bold;']*len(x) if x.get('Is_T') else ['']*len(x), axis=1)
                    .format({"Importo_Netto_c": "€ {:,.2f}", "Importo_Netto_p": "€ {:,.2f}", "Diff": "€ {:,.2f}"}),
                    use_container_width=True, hide_index=True,
                    column_order=("Codice Conto", "Descrizione Conto", "Importo_Netto_c", "Importo_Netto_p", "Diff")
                )
                st.divider()
