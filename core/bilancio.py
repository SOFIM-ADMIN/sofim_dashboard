"""
Sofim Financial Dashboard - Core Logica Bilancio
Funzioni di calcolo saldi condivise tra Stato Patrimoniale, Conto Economico e Indici.
"""

import pandas as pd
from utils.formatting import clean_numeric


def get_saldo(df_final, tipi_sigle, anno, campo="Tipo", mese_limite=12):
    """Estrae saldo netto (Avere - Dare) per tipo/i conto."""
    if isinstance(tipi_sigle, str):
        tipi_sigle = [tipi_sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final[campo].astype(str).str.strip().isin(tipi_sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = sub["Dare"].apply(clean_numeric)
    sub["A"] = sub["Avere"].apply(clean_numeric)
    return float(sub["A"].sum() - sub["D"].sum())


def get_saldo_attivo(df_final, sigle, anno, mese_limite=12):
    """Per immobilizzazioni/attivita: saldo attivo (Dare > Avere)."""
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    conti = sub.groupby("Codice Conto").agg({"D": "sum", "A": "sum"})
    conti["S"] = conti["D"] - conti["A"]
    return float(conti[conti["S"] > 0]["S"].sum())


def get_saldo_passivo(df_final, sigle, anno, mese_limite=12):
    """Per passivita: saldo passivo (Avere > Dare)."""
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    return float(sub["A"].sum() - sub["D"].sum())


def get_saldo_passivo_multi(df_final, sigle, anno, mese_limite=12):
    """
    Calcola il saldo passivo aggregando PIU tipi insieme prima di applicare il filtro.
    Utile quando tipi diversi si compensano (es. FORN + FOCF).
    Per i conti FOCF, il saldo viene sempre incluso anche se negativo.
    """
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)

    conti = sub.groupby(["Codice Conto", "Descrizione Conto"]).agg({"D": "sum", "A": "sum"}).reset_index()
    conti["S"] = conti["A"] - conti["D"]

    pattern_focf = (
        conti["Descrizione Conto"].str.contains(r"OSCILLAZ.*CAMBI|CAMBI.*OSCILLAZ|FONDO.*CAMBI.*FORN|FORN.*CAMBI", case=False, na=False) |
        conti["Codice Conto"].str.contains(r"FOCF|F\.OCF|OSC\.CAMB", case=False, na=False)
    )

    saldo_focf = conti.loc[pattern_focf, "S"].sum() if pattern_focf.any() else 0.0
    saldo_altri = conti.loc[~pattern_focf & (conti["S"] > 0), "S"].sum()

    return float(saldo_altri + saldo_focf)


def get_saldo_bifurcato(df_final, sigle, anno, mese_limite=12):
    """
    Per tipi come ERARIO e BANCHE dove i singoli conti possono chiudere in dare O in avere.
    Ritorna una tupla: (saldo_attivo, saldo_passivo).
    """
    if isinstance(sigle, str):
        sigle = [sigle]
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip().isin(sigle))
    ].copy()
    if sub.empty:
        return 0.0, 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    conti = sub.groupby("Codice Conto").agg({"D": "sum", "A": "sum"})
    conti["S"] = conti["A"] - conti["D"]

    saldo_attivo = float(conti[conti["S"] < 0]["S"].abs().sum())
    saldo_passivo = float(conti[conti["S"] > 0]["S"].sum())

    return saldo_attivo, saldo_passivo


def get_fondo(df_final, sigla, anno, mese_limite=12):
    """Fondo ammortamento/svalutazione: valore negativo da sottrarre."""
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip() == sigla)
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    return float(sub["A"].sum() - sub["D"].sum())




def get_saldo_cli_lordo(df_final, anno, mese_limite=12):
    """
    Per CLI (Clienti): somma di TUTTI i conti mappati con tipo CLI,
    indipendentemente dal segno (dare o avere).
    Ritorna il saldo lordo = somma assoluta dei movimenti.
    """
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip() == "CLI")
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    # Saldo lordo: somma di tutti i movimenti in valore assoluto
    # In contabilità: Dare = credito (positivo per noi), Avere = incasso/anticipo (negativo)
    # Per l'attivo patrimoniale vogliamo la posizione netta = D - A
    return float((sub["D"] - sub["A"]).sum())



def get_saldo_forn_lordo(df_final, anno, mese_limite=12):
    """
    Per FORN/FOCF (Fornitori): somma di TUTTI i conti mappati con tipo FORN o FOCF,
    indipendentemente dal segno (dare o avere).
    Saldo = A - D (debito verso fornitori, passivo)
    """
    sub = df_final[
        (df_final["Anno"] == anno) &
        (df_final["Mese_Num"] <= mese_limite) &
        (df_final["Tipo"].astype(str).str.strip().isin(["FORN", "FOCF"]))
    ].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    # Per fornitori: debito = Avere - Dare (passivo)
    return float((sub["A"] - sub["D"]).sum())

def calcola_utile_ce(df_final, anno, mese_limite):
    """Calcola utile/perdita dal Conto Economico."""
    mask = (df_final["Anno"] == anno) & (df_final["Mese_Num"] <= mese_limite)
    sub = df_final[mask].copy()
    if sub.empty:
        return 0.0
    sub["D"] = pd.to_numeric(sub["Dare"].apply(clean_numeric), errors='coerce').fillna(0)
    sub["A"] = pd.to_numeric(sub["Avere"].apply(clean_numeric), errors='coerce').fillna(0)
    ricavi = sub[sub["Categoria"].astype(str).str.strip().str.upper() == "RICAVI"]
    costi = sub[sub["Categoria"].astype(str).str.strip().str.upper() == "COSTI"]
    tot_ricavi = ricavi["A"].sum() - ricavi["D"].sum()
    tot_costi = costi["D"].sum() - costi["A"].sum()
    return float(tot_ricavi - tot_costi)
