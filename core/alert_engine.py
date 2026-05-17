"""
Sofim Financial Dashboard - Motore Alert Scostamenti
"""

import pandas as pd
import numpy as np
from utils.formatting import clean_numeric


def _get_saldo_attivo_anno(df_final, sigle, anno):
    """Calcola saldo attivo al 31/12 dell'anno (cumulato fino a dicembre)."""
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    conti = sub.groupby("Codice Conto").agg({"D": "sum", "A": "sum"})
    conti["S"] = conti["D"] - conti["A"]
    return float(conti[conti["S"] > 0]["S"].sum())


def _get_saldo_passivo_anno(df_final, sigle, anno):
    """Calcola saldo passivo al 31/12 dell'anno (cumulato fino a dicembre)."""
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    conti = sub.groupby("Codice Conto").agg({"D": "sum", "A": "sum"})
    conti["S"] = conti["A"] - conti["D"]
    return float(conti[conti["S"] > 0]["S"].sum())


def _get_saldo_bifurcato_anno(df_final, sigle, anno):
    """Per tipi bifurcati (BANCHE, ERARIO): ritorna (saldo_attivo, saldo_passivo) al 31/12."""
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0, 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    conti = sub.groupby("Codice Conto").agg({"D": "sum", "A": "sum"})
    conti["S"] = conti["A"] - conti["D"]
    attivo = float(conti[conti["S"] < 0]["S"].abs().sum())
    passivo = float(conti[conti["S"] > 0]["S"].sum())
    return attivo, passivo


def _get_saldo_cli_lordo_anno(df_final, anno):
    """Per CLI: saldo lordo = D - A (posizione netta crediti vs clienti) al 31/12."""
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip() == "CLI")
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    return float((sub["D"] - sub["A"]).sum())


def _get_saldo_forn_lordo_anno(df_final, anno):
    """Per FORN/FOCF: saldo lordo = A - D (debito vs fornitori) al 31/12."""
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip().isin(["FORN", "FOCF"]))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    return float((sub["A"] - sub["D"]).sum())


def _get_saldo_fondo_anno(df_final, sigla, anno):
    """Fondo ammortamento al 31/12."""
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12) &
        (df_final["Tipo"].astype(str).str.strip() == sigla)
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    return float(sub["A"].sum() - sub["D"].sum())


def _calcola_utile_anno(df_final, anno):
    """Calcola utile/perdita dell'anno (cumulato fino a dicembre)."""
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= 12)
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    ricavi = sub[sub["Categoria"].astype(str).str.strip().str.upper() == "RICAVI"]
    costi = sub[sub["Categoria"].astype(str).str.strip().str.upper() == "COSTI"]
    tot_ricavi = ricavi["A"].sum() - ricavi["D"].sum()
    tot_costi = costi["D"].sum() - costi["A"].sum()
    return float(tot_ricavi - tot_costi)


def _build_attivita_rows(df_final, anno_c, anno_p):
    """Costruisce le righe per l'analisi scostamenti ATTIVITA (saldo al 31/12)."""
    rows = []

    # Immobilizzazioni
    imm_n_c = _get_saldo_attivo_anno(df_final, "IMIMM", anno_c) - _get_saldo_fondo_anno(df_final, "FIMMAT", anno_c)
    imm_n_p = _get_saldo_attivo_anno(df_final, "IMIMM", anno_p) - _get_saldo_fondo_anno(df_final, "FIMMAT", anno_p)
    mat_n_c = _get_saldo_attivo_anno(df_final, "IMMAT", anno_c) - _get_saldo_fondo_anno(df_final, "FMAT", anno_c)
    mat_n_p = _get_saldo_attivo_anno(df_final, "IMMAT", anno_p) - _get_saldo_fondo_anno(df_final, "FMAT", anno_p)
    fin_c = _get_saldo_attivo_anno(df_final, "IMMFIN", anno_c)
    fin_p = _get_saldo_attivo_anno(df_final, "IMMFIN", anno_p)

    rows.append({
        "Codice Conto": "IMMOB", "Descrizione Conto": "Immobilizzazioni nette",
        "Cat_Safe": "ATTIVITA", "Importo_C": imm_n_c + mat_n_c + fin_c,
        "Importo_P": imm_n_p + mat_n_p + fin_p
    })

    # Rimanenze
    rim_c = _get_saldo_attivo_anno(df_final, "RIM", anno_c)
    rim_p = _get_saldo_attivo_anno(df_final, "RIM", anno_p)
    anf_c = _get_saldo_attivo_anno(df_final, "ANF", anno_c)
    anf_p = _get_saldo_attivo_anno(df_final, "ANF", anno_p)

    rows.append({
        "Codice Conto": "RIMAN", "Descrizione Conto": "Rimanenze e anticipi",
        "Cat_Safe": "ATTIVITA", "Importo_C": rim_c + anf_c,
        "Importo_P": rim_p + anf_p
    })

    # Clienti (aggregato in un'unica riga)
    cli_c = _get_saldo_cli_lordo_anno(df_final, anno_c)
    cli_p = _get_saldo_cli_lordo_anno(df_final, anno_p)

    rows.append({
        "Codice Conto": "CLI", "Descrizione Conto": "Crediti vs clienti",
        "Cat_Safe": "ATTIVITA", "Importo_C": cli_c,
        "Importo_P": cli_p
    })

    # Altri crediti
    af_c = _get_saldo_attivo_anno(df_final, "AF", anno_c)
    af_p = _get_saldo_attivo_anno(df_final, "AF", anno_p)
    era_att_c, _ = _get_saldo_bifurcato_anno(df_final, "ERARIO", anno_c)
    era_att_p, _ = _get_saldo_bifurcato_anno(df_final, "ERARIO", anno_p)
    aa_c = _get_saldo_attivo_anno(df_final, ["AA", "RRA"], anno_c)
    aa_p = _get_saldo_attivo_anno(df_final, ["AA", "RRA"], anno_p)

    rows.append({
        "Codice Conto": "ALTRI_CR", "Descrizione Conto": "Altri crediti",
        "Cat_Safe": "ATTIVITA", "Importo_C": af_c + era_att_c + aa_c,
        "Importo_P": af_p + era_att_p + aa_p
    })

    # Liquidità
    banche_att_c, _ = _get_saldo_bifurcato_anno(df_final, "BANCHE", anno_c)
    banche_att_p, _ = _get_saldo_bifurcato_anno(df_final, "BANCHE", anno_p)
    dl_c = _get_saldo_attivo_anno(df_final, "DL", anno_c)
    dl_p = _get_saldo_attivo_anno(df_final, "DL", anno_p)

    rows.append({
        "Codice Conto": "LIQUID", "Descrizione Conto": "Liquidità",
        "Cat_Safe": "ATTIVITA", "Importo_C": banche_att_c + dl_c,
        "Importo_P": banche_att_p + dl_p
    })

    return pd.DataFrame(rows)


def _build_passivita_rows(df_final, anno_c, anno_p):
    """Costruisce le righe per l'analisi scostamenti PASSIVITA (saldo al 31/12)."""
    rows = []

    # Capitale proprio
    cs_c = _get_saldo_passivo_anno(df_final, "CS", anno_c)
    cs_p = _get_saldo_passivo_anno(df_final, "CS", anno_p)
    pn_c = _get_saldo_passivo_anno(df_final, "PN", anno_c)
    pn_p = _get_saldo_passivo_anno(df_final, "PN", anno_p)
    upn_c = _get_saldo_passivo_anno(df_final, "UPN", anno_c)
    upn_p = _get_saldo_passivo_anno(df_final, "UPN", anno_p)
    utile_c = _calcola_utile_anno(df_final, anno_c)
    utile_p = _calcola_utile_anno(df_final, anno_p)

    rows.append({
        "Codice Conto": "CP", "Descrizione Conto": "Capitale proprio",
        "Cat_Safe": "PASSIVITA", "Importo_C": cs_c + pn_c + upn_c + utile_c,
        "Importo_P": cs_p + pn_p + upn_p + utile_p
    })

    # Passività consolidate
    dcon_c = _get_saldo_passivo_anno(df_final, "DCON", anno_c)
    dcon_p = _get_saldo_passivo_anno(df_final, "DCON", anno_p)
    fmlt_c = _get_saldo_passivo_anno(df_final, "FMLT", anno_c)
    fmlt_p = _get_saldo_passivo_anno(df_final, "FMLT", anno_p)
    fin_c = _get_saldo_passivo_anno(df_final, "FIN", anno_c)
    fin_p = _get_saldo_passivo_anno(df_final, "FIN", anno_p)
    soci_c = _get_saldo_passivo_anno(df_final, "SOCI", anno_c)
    soci_p = _get_saldo_passivo_anno(df_final, "SOCI", anno_p)
    tfm_c = _get_saldo_passivo_anno(df_final, "TFM", anno_c)
    tfm_p = _get_saldo_passivo_anno(df_final, "TFM", anno_p)
    tfr_c = _get_saldo_passivo_anno(df_final, "TFR", anno_c)
    tfr_p = _get_saldo_passivo_anno(df_final, "TFR", anno_p)
    fondi_c = _get_saldo_passivo_anno(df_final, "FONDI", anno_c)
    fondi_p = _get_saldo_passivo_anno(df_final, "FONDI", anno_p)

    rows.append({
        "Codice Conto": "PASS_CONS", "Descrizione Conto": "Passività consolidate",
        "Cat_Safe": "PASSIVITA", "Importo_C": dcon_c + fmlt_c + fin_c + soci_c + tfm_c + tfr_c + fondi_c,
        "Importo_P": dcon_p + fmlt_p + fin_p + soci_p + tfm_p + tfr_p + fondi_p
    })

    # Fornitori (aggregato in un'unica riga)
    forn_c = _get_saldo_forn_lordo_anno(df_final, anno_c)
    forn_p = _get_saldo_forn_lordo_anno(df_final, anno_p)

    rows.append({
        "Codice Conto": "FORN", "Descrizione Conto": "Debiti vs fornitori",
        "Cat_Safe": "PASSIVITA", "Importo_C": forn_c,
        "Importo_P": forn_p
    })

    # Altre passività correnti
    _, banche_pass_c = _get_saldo_bifurcato_anno(df_final, "BANCHE", anno_c)
    _, banche_pass_p = _get_saldo_bifurcato_anno(df_final, "BANCHE", anno_p)
    bant_c = _get_saldo_passivo_anno(df_final, "BANT", anno_c)
    bant_p = _get_saldo_passivo_anno(df_final, "BANT", anno_p)
    antcli_c = _get_saldo_passivo_anno(df_final, "ANTCLI", anno_c)
    antcli_p = _get_saldo_passivo_anno(df_final, "ANTCLI", anno_p)
    _, era_pass_c = _get_saldo_bifurcato_anno(df_final, "ERARIO", anno_c)
    _, era_pass_p = _get_saldo_bifurcato_anno(df_final, "ERARIO", anno_p)
    prev_c = _get_saldo_passivo_anno(df_final, "PREV", anno_c)
    prev_p = _get_saldo_passivo_anno(df_final, "PREV", anno_p)
    ap_c = _get_saldo_passivo_anno(df_final, "AP", anno_c)
    ap_p = _get_saldo_passivo_anno(df_final, "AP", anno_p)
    rrp_c = _get_saldo_passivo_anno(df_final, "RRP", anno_c)
    rrp_p = _get_saldo_passivo_anno(df_final, "RRP", anno_p)

    rows.append({
        "Codice Conto": "ALTRE_PASS", "Descrizione Conto": "Altre passività correnti",
        "Cat_Safe": "PASSIVITA", "Importo_C": banche_pass_c + bant_c + antcli_c + era_pass_c + prev_c + ap_c + rrp_c,
        "Importo_P": banche_pass_p + bant_p + antcli_p + era_pass_p + prev_p + ap_p + rrp_p
    })

    return pd.DataFrame(rows)


def _build_ricavi_costi_rows(df_final, anno_c, anno_p):
    """Costruisce le righe per RICAVI e COSTI (movimenti annuali, come prima)."""
    sub = df_final[
        (df_final["Anno"].isin([anno_c, anno_p])) &
        (df_final["Mese_Num"] <= 12)
    ].copy()

    if sub.empty:
        return pd.DataFrame()

    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["Importo_Netto"] = sub["A"] - sub["D"]

    mask_ricavi = sub["Cat_Safe"].str.contains(r"RICAV|VENDIT|ENTRAT", na=False)
    mask_costi = sub["Cat_Safe"].str.contains(r"COST|ACQUIST|USCIT|PERSONALE", na=False)

    ricavi = sub[mask_ricavi].groupby(["Codice Conto", "Descrizione Conto", "Cat_Safe", "Anno"])["Importo_Netto"].sum().reset_index()
    costi = sub[mask_costi].groupby(["Codice Conto", "Descrizione Conto", "Cat_Safe", "Anno"])["Importo_Netto"].sum().reset_index()

    df_all = pd.concat([ricavi, costi], ignore_index=True)

    # Pivot per trasformare Anno in Importo_C e Importo_P
    pivot = df_all.pivot_table(
        index=["Codice Conto", "Descrizione Conto", "Cat_Safe"],
        columns="Anno",
        values="Importo_Netto",
        aggfunc="sum"
    ).fillna(0).reset_index()

    # Rinomina colonne anno in Importo_C e Importo_P
    if anno_c in pivot.columns:
        pivot = pivot.rename(columns={anno_c: "Importo_C"})
    else:
        pivot["Importo_C"] = 0.0
    if anno_p in pivot.columns:
        pivot = pivot.rename(columns={anno_p: "Importo_P"})
    else:
        pivot["Importo_P"] = 0.0

    return pivot[["Codice Conto", "Descrizione Conto", "Cat_Safe", "Importo_C", "Importo_P"]]


def calcola_alert(df_final, soglia_gialla, soglia_rossa, tipi_monitorati, anno_rif=None):
    """
    Calcola scostamenti anno corrente vs precedente.

    Per RICAVI/COSTI: confronto movimenti annuali (come prima).
    Per ATTIVITA/PASSIVITA: confronto saldi al 31/12 (come Stato Patrimoniale).

    Args:
        anno_rif: Anno di riferimento selezionato dall'utente. Se None, usa l'ultimo anno disponibile.
    """
    anni = sorted(df_final["Anno"].unique())
    if len(anni) < 2:
        return pd.DataFrame()

    # Se anno_rif è specificato, usa quello come anno corrente
    if anno_rif is not None and anno_rif in anni:
        anno_c = anno_rif
        idx = anni.index(anno_rif)
        if idx > 0:
            anno_p = anni[idx - 1]
        else:
            return pd.DataFrame()  # Non c'è anno precedente
    else:
        anno_c = anni[-1]
        anno_p = anni[-2]

    all_rows = []

    # RICAVI e COSTI: movimenti annuali
    if any(t in tipi_monitorati for t in ["RICAVI", "COSTI"]):
        df_rc = _build_ricavi_costi_rows(df_final, anno_c, anno_p)
        if not df_rc.empty:
            # Filtra solo le categorie selezionate
            mask = pd.Series(False, index=df_rc.index)
            if "RICAVI" in tipi_monitorati:
                mask |= df_rc["Cat_Safe"].str.contains(r"RICAV|VENDIT|ENTRAT", na=False)
            if "COSTI" in tipi_monitorati:
                mask |= df_rc["Cat_Safe"].str.contains(r"COST|ACQUIST|USCIT|PERSONALE", na=False)
            df_rc = df_rc[mask]
            if not df_rc.empty:
                all_rows.append(df_rc)

    # ATTIVITA: saldi al 31/12
    if "ATTIVITA" in tipi_monitorati:
        df_att = _build_attivita_rows(df_final, anno_c, anno_p)
        if not df_att.empty:
            all_rows.append(df_att)

    # PASSIVITA: saldi al 31/12
    if "PASSIVITA" in tipi_monitorati:
        df_pass = _build_passivita_rows(df_final, anno_c, anno_p)
        if not df_pass.empty:
            all_rows.append(df_pass)

    if not all_rows:
        return pd.DataFrame()

    # Concatena tutti i DataFrame (tutti hanno le stesse colonne)
    pivot = pd.concat(all_rows, ignore_index=True)

    # Assicura che tutte le colonne esistano
    for col in ["Importo_C", "Importo_P"]:
        if col not in pivot.columns:
            pivot[col] = 0.0

    pivot["Variazione_€"] = pivot["Importo_C"] - pivot["Importo_P"]

    def calc_pct(row):
        base = abs(row["Importo_P"]) if row["Importo_P"] != 0 else abs(row["Importo_C"])
        if base == 0:
            return 0.0 if row["Variazione_€"] == 0 else 999.0
        return (row["Variazione_€"] / base) * 100

    pivot["Variazione_%"] = pivot.apply(calc_pct, axis=1)
    # Colonna ausiliaria per ordinamento (non visibile in output)
    pivot["_var_pct_abs"] = pivot["Variazione_%"].abs()

    def determina_impatto(row):
        cat = str(row["Cat_Safe"]).upper()
        var = row["Variazione_%"]

        is_ricavo = any(k in cat for k in ["RICAV", "VENDIT", "ENTRAT"])
        is_costo = any(k in cat for k in ["COST", "ACQUIST", "USCIT", "PERSONALE"])
        is_attivita = "ATTIVITA" in cat
        is_passivita = "PASSIVITA" in cat

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
        elif is_attivita:
            # Per attivita: aumento = positivo (piu attivita = bene)
            if var > 0:
                return "POSITIVO"
            elif var < 0:
                return "NEGATIVO"
            return "NEUTRO"
        elif is_passivita:
            # Per passivita: diminuzione = positivo (meno debiti = bene)
            if var < 0:
                return "POSITIVO"
            elif var > 0:
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

    # NUOVO: Crea riga TOTALE prima di ordinare
    totale = {
        "Codice Conto": "",
        "Descrizione Conto": "TOTALE",
        "Cat_Safe": "",
        "Anno_Cor": anno_c,
        "Importo_C": pivot["Importo_C"].sum(),
        "Anno_Prec": anno_p,
        "Importo_P": pivot["Importo_P"].sum(),
        "Variazione_€": pivot["Variazione_€"].sum(),
        "Variazione_%": 0.0,
        "Impatt_o": "NEUTRO",
        "Stato": "⚪ OK",
        "Ordine": 99,
        "_var_pct_abs": 0.0
    }

    # Calcola variazione % del totale
    base_tot = abs(totale["Importo_P"]) if totale["Importo_P"] != 0 else abs(totale["Importo_C"])
    if base_tot != 0:
        totale["Variazione_%"] = (totale["Variazione_€"] / base_tot) * 100

    # Crea DataFrame con il totale e concatena
    df_totale = pd.DataFrame([totale])
    pivot = pd.concat([pivot, df_totale], ignore_index=True)

    # ORDINA dopo aver aggiunto il totale (così il totale rimane in fondo)
    pivot = pivot.sort_values(["Ordine", "_var_pct_abs"], ascending=[True, False], kind='mergesort')

    # Rimuovi colonne ausiliarie dall'output finale
    return pivot[[
        "Codice Conto", "Descrizione Conto", "Cat_Safe",
        "Anno_Cor", "Importo_C", "Anno_Prec", "Importo_P",
        "Variazione_€", "Variazione_%", "Impatt_o", "Stato"
    ]]
