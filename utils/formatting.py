"""
Sofim Financial Dashboard - Utilities di Formattazione e Styling
"""

import pandas as pd
import numpy as np


def clean_numeric(x) -> float:
    """Converte stringhe numeriche italiane (punti migliaia, virgola decimale)."""
    if isinstance(x, str):
        try:
            return float(x.strip().replace(".", "").replace(",", "."))
        except ValueError:
            return 0.0
    if pd.isna(x):
        return 0.0
    return float(x)


def style_delta(val):
    """Colora di verde/rosso valori numerici positivi/negativi."""
    if not isinstance(val, (int, float)):
        return ""
    if val > 0:
        return "color: green; font-weight: bold"
    if val < 0:
        return "color: red; font-weight: bold"
    return "color: grey"


def fmt_eur(x):
    """Formatta come Euro solo se numerico, altrimenti restituisce la stringa."""
    if isinstance(x, (int, float)) and not pd.isna(x):
        return f"€ {x:,.2f}"
    return str(x)


def color_stato(val):
    """Colora lo stato alert."""
    if val == "🔴 CRITICO":
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
    elif val == "🟡 ATTENZIONE":
        return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
    elif val == "🟢 OPPORTUNITA":
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    return 'background-color: #f8f9fa; color: #6c757d;'


def color_variazione_importo(val):
    """Colora l'importo della variazione in base al segno e all'entità."""
    if not isinstance(val, (int, float)):
        return ""
    abs_val = abs(val)
    if val > 0:
        if abs_val > 50000:
            return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold;'
        elif abs_val > 10000:
            return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold;'
        return 'color: #4caf50;'
    elif val < 0:
        if abs_val > 50000:
            return 'background-color: #ffcdd2; color: #b71c1c; font-weight: bold;'
        elif abs_val > 10000:
            return 'background-color: #ffebee; color: #c62828; font-weight: bold;'
        return 'color: #f44336;'
    return ""


def color_variazione_pct(val):
    """Colora la percentuale in base al segno."""
    if not isinstance(val, (int, float)):
        return ""
    if val > 0:
        return 'color: #2e7d32; font-weight: bold;'
    elif val < 0:
        return 'color: #c62828; font-weight: bold;'
    return ""


def color_pfn_val(val):
    """Colora valori PFN (verde se >=0, rosso se <0)."""
    color = '#d4edda' if val >= 0 else '#f8d7da'
    text_color = '#155724' if val >= 0 else '#721c24'
    return f'background-color: {color}; color: {text_color}; font-weight: bold;'


def get_color_indice(indice, valore):
    """Restituisce colore semaforo per indice di bilancio."""
    from config import SoglieIndici as S

    if indice == "ROE":
        return "#d4edda" if valore > S.ROE_BUONO else "#fff3cd" if valore > S.ROE_SUFFICIENTE else "#f8d7da"
    elif indice == "ROI":
        return "#d4edda" if valore > S.ROI_BUONO else "#fff3cd" if valore > S.ROI_SUFFICIENTE else "#f8d7da"
    elif indice == "ROS":
        return "#d4edda" if valore > S.ROS_BUONO else "#fff3cd" if valore > S.ROS_SUFFICIENTE else "#f8d7da"
    elif indice == "Margine Lordo":
        return "#d4edda" if valore > S.MARGINE_LORDO_BUONO else "#fff3cd" if valore > S.MARGINE_LORDO_SUFFICIENTE else "#f8d7da"
    elif indice == "Leverage":
        return "#d4edda" if valore < S.LEVERAGE_BUONO else "#fff3cd" if valore < S.LEVERAGE_SUFFICIENTE else "#f8d7da"
    elif indice == "Ind. Liquidita":
        return "#d4edda" if valore > S.LIQUIDITA_BUONA else "#fff3cd" if valore > S.LIQUIDITA_SUFFICIENTE else "#f8d7da"
    elif indice == "Ind. Solvibilita":
        return "#d4edda" if valore > S.SOLVIBILITA_BUONA else "#fff3cd" if valore > S.SOLVIBILITA_SUFFICIENTE else "#f8d7da"
    elif indice == "Marg. Struttura":
        return "#d4edda" if valore > S.MARG_STRUTTURA_BUONO else "#fff3cd" if valore > S.MARG_STRUTTURA_SUFFICIENTE else "#f8d7da"
    return ""
