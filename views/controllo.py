"""
Sofim Financial Dashboard - Pagina Dashboard di Controllo
"""

import streamlit as st
import pandas as pd
from utils.formatting import clean_numeric, fmt_eur


def render(df_final: pd.DataFrame) -> None:
    st.title("📊 Stato della Quadratura")

    st.subheader("📌 Riepilogo Caricamento")
    tab_riepilogo = (
        df_final.groupby("Anno")
        .agg(ultima_reg=("Data Operazione", "max"), n_reg=("Codice Conto", "count"))
        .reset_index()
    )
    tab_riepilogo.columns = ["Anno", "Ultima Registrazione", "N. Registrazioni"]
    tab_riepilogo["Ultima Registrazione"] = tab_riepilogo["Ultima Registrazione"].dt.strftime("%d/%m/%Y")
    st.table(tab_riepilogo)

    st.subheader("⚖️ Verifica Bilanci (segno: Avere − Dare)")
    anni_disp = sorted(df_final["Anno"].unique())

    def get_saldo(keywords: list[str]) -> pd.Series:
        match = [c for c in df_final["Cat_Safe"].unique() if any(k in c for k in keywords)]
        return (
            df_final[df_final["Cat_Safe"].isin(match)]
            .groupby("Anno")["Importo_Netto"]
            .sum()
            .reindex(anni_disp, fill_value=0)
        )

    righe = {
        "[+] Ricavi":               get_saldo(["RICAV", "VENDIT", "ENTRAT"]),
        "[-] Costi":                get_saldo(["COST", "ACQUIST", "USCIT"]),
        "(=) Risultato Economico":  None,
        " ":                        None,
        "[+] Passivita/Patrimonio": get_saldo(["PASSIV"]),
        "[-] Attivita":             get_saldo(["ATTIV"]),
        "(=) Saldo Patrimoniale":   None,
        "  ":                       None,
        "SQUADRATURA TOTALE":       None,
    }

    prospetto = pd.DataFrame(index=list(righe.keys()), columns=anni_disp, dtype=object)
    for k, v in righe.items():
        if v is not None:
            prospetto.loc[k] = v.values

    prospetto.loc["(=) Risultato Economico"] = (
        prospetto.loc["[+] Ricavi"].astype(float) + prospetto.loc["[-] Costi"].astype(float)
    ).values
    prospetto.loc["(=) Saldo Patrimoniale"] = (
        prospetto.loc["[+] Passivita/Patrimonio"].astype(float) + prospetto.loc["[-] Attivita"].astype(float)
    ).values
    prospetto.loc["SQUADRATURA TOTALE"] = (
        prospetto.loc["(=) Risultato Economico"].astype(float)
        + prospetto.loc["(=) Saldo Patrimoniale"].astype(float)
    ).round(2).values

    def style_and_text_squadratura(row):
        if row.name == "SQUADRATURA TOTALE":
            styles = []
            for val in row:
                if abs(val) > 0.1:
                    styles.append('background-color: #f8d7da; color: #721c24; font-weight: bold')
                else:
                    styles.append('background-color: #d4edda; color: #155724; font-weight: bold')
            return styles
        return [''] * len(row)

    def format_ok(val):
        if abs(val) < 0.1:
            return "0.00 € - OK"
        return f"{val:,.2f} €"

    prospetto_formattato = (
        prospetto.style
        .apply(style_and_text_squadratura, axis=1)
        .format(format_ok, subset=(["SQUADRATURA TOTALE"], prospetto.columns))
        .format(fmt_eur, subset=(prospetto.index[:-1], prospetto.columns))
    )

    st.dataframe(prospetto_formattato, use_container_width=True)

    st.divider()
    st.subheader("🔍 Verifica Integrita Anagrafica Conti")

    conti_non_mappati = df_final[df_final["Cat_Safe"] == "NON MAPPATO"]

    if not conti_non_mappati.empty:
        check_mapping = (
            conti_non_mappati.groupby(["Codice Conto", "Descrizione Conto"])
            .agg(
                Movimenti=("Codice Conto", "count"),
                Saldo_Totale=("Importo_Netto", "sum")
            )
            .reset_index()
            .sort_values(by="Movimenti", ascending=False)
        )

        st.error(f"⚠️ Attenzione: Trovati {len(check_mapping)} codici conto nel CSV non presenti nella mappatura Excel.")

        st.dataframe(
            check_mapping.style.format({"Saldo_Totale": "€ {:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )

        csv = check_mapping.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Scarica Elenco Conti da Mappare",
            data=csv,
            file_name="conti_da_mappare.csv",
            mime="text/csv",
        )
    else:
        st.success("✅ Coerenza Dati OK: Tutti i codici movimentati sono presenti nel Piano dei Conti.")
