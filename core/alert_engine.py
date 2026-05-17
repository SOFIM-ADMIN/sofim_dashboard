"""
Sofim Financial Dashboard - Motore Alert Scostamenti
"""

import pandas as pd
import numpy as np


def calcola_alert(df_final, soglia_gialla, soglia_rossa, tipi_monitorati):
    """
    Calcola scostamenti anno corrente vs precedente con logica contestuale.
    Ricavi: aumento = positivo | Costi: diminuzione = positivo
    """
    anni = sorted(df_final["Anno"].unique())
    if len(anni) < 2:
        return pd.DataFrame()

    anno_c = anni[-1]
    anno_p = anni[-2]

    mask_tipo = pd.Series(False, index=df_final.index)
    for tipo in tipi_monitorati:
        if tipo == "RICAVI":
            mask_tipo |= df_final["Cat_Safe"].str.contains(r"RICAV|VENDIT|ENTRAT", na=False)
        elif tipo == "COSTI":
            mask_tipo |= df_final["Cat_Safe"].str.contains(r"COST|ACQUIST|USCIT|PERSONALE", na=False)
        elif tipo == "PATRIMONIO":
            mask_tipo |= df_final["Cat_Safe"].str.contains(r"ATTIV|PASSIV", na=False)

    df_work = df_final[mask_tipo].copy()

    pivot = df_work.pivot_table(
        index=["Codice Conto", "Descrizione Conto", "Cat_Safe"],
        columns="Anno",
        values="Importo_Netto",
        aggfunc="sum"
    ).fillna(0).reset_index()

    for a in [anno_c, anno_p]:
        if a not in pivot.columns:
            pivot[a] = 0.0

    pivot["Importo_C"] = pivot[anno_c]
    pivot["Importo_P"] = pivot[anno_p]
    pivot["Variazione_€"] = pivot["Importo_C"] - pivot["Importo_P"]

    def calc_pct(row):
        base = abs(row["Importo_P"]) if row["Importo_P"] != 0 else abs(row["Importo_C"])
        if base == 0:
            return 0.0 if row["Variazione_€"] == 0 else 999.0
        return (row["Variazione_€"] / base) * 100

    pivot["Variazione_%"] = pivot.apply(calc_pct, axis=1)
    pivot["Variazione_%_abs"] = pivot["Variazione_%"].abs()

    def determina_impatto(row):
        cat = str(row["Cat_Safe"]).upper()
        var = row["Variazione_%"]

        is_ricavo = any(k in cat for k in ["RICAV", "VENDIT", "ENTRAT"])
        is_costo = any(k in cat for k in ["COST", "ACQUIST", "USCIT", "PERSONALE"])

        if is_ricavo:
            if var > 0:
                return "POSITIVO"
            elif var < 0:
                return "NEGATIVO"
            return "NEUTRO"
        elif is_costo:
            if var > 0:
                return "POSITIVO"
            elif var < 0:
                return "NEGATIVO"
            return "NEUTRO"
        else:
            return "NEUTRO"

    pivot["Impatt_o"] = pivot.apply(determina_impatto, axis=1)

    def classifica(row):
        abs_var = abs(row["Variazione_%"])
        impatto = row["Impatt_o"]

        if abs_var >= soglia_rossa:
            if impatto == "POSITIVO":
                return "🟢 OPPORTUNITA"
            elif impatto == "NEGATIVO":
                return "🔴 CRITICO"
            else:
                return "🟡 ATTENZIONE"
        elif abs_var >= soglia_gialla:
            if impatto == "POSITIVO":
                return "🟢 OPPORTUNITA"
            elif impatto == "NEGATIVO":
                return "🟡 ATTENZIONE"
            else:
                return "⚪ OK"
        return "⚪ OK"

    pivot["Stato"] = pivot.apply(classifica, axis=1)
    pivot["Anno_Cor"] = anno_c
    pivot["Anno_Prec"] = anno_p

    ordine = {"🔴 CRITICO": 0, "🟡 ATTENZIONE": 1, "🟢 OPPORTUNITA": 2, "⚪ OK": 3}
    pivot["Ordine"] = pivot["Stato"].map(ordine)
    pivot = pivot.sort_values(["Ordine", "Variazione_%_abs"], ascending=[True, False])

    return pivot[[
        "Codice Conto", "Descrizione Conto", "Cat_Safe",
        "Anno_Cor", "Importo_C", "Anno_Prec", "Importo_P",
        "Variazione_€", "Variazione_%", "Variazione_%_abs", "Impatt_o", "Stato"
    ]]
