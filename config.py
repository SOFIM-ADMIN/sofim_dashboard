"""
Sofim Financial Dashboard - Configurazione Centralizzata
"""

# ---------------------------------------------------------------------------
# COSTANTI GLOBALI
# ---------------------------------------------------------------------------

MESI_NOMI = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
             "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

COLONNE_RICHIESTE = [
    "Data Operazione", "Codice Conto", "Descrizione Conto",
    "Descrizione Causale Testata", "Dare", "Avere",
]

# ---------------------------------------------------------------------------
# SOGLIE ALERT
# ---------------------------------------------------------------------------

class SoglieAlert:
    GIALLA_DEFAULT = 15
    ROSSA_DEFAULT = 30

class SoglieIndici:
    """Benchmark per colorazione semaforo scorecard."""
    ROE_BUONO = 0.10
    ROE_SUFFICIENTE = 0.05

    ROI_BUONO = 0.08
    ROI_SUFFICIENTE = 0.04

    ROS_BUONO = 0.05
    ROS_SUFFICIENTE = 0.02

    MARGINE_LORDO_BUONO = 0.40
    MARGINE_LORDO_SUFFICIENTE = 0.25

    LEVERAGE_BUONO = 1.5
    LEVERAGE_SUFFICIENTE = 2.5

    LIQUIDITA_BUONA = 1.0
    LIQUIDITA_SUFFICIENTE = 0.5

    SOLVIBILITA_BUONA = 1.5
    SOLVIBILITA_SUFFICIENTE = 1.0

    MARG_STRUTTURA_BUONO = 1.0
    MARG_STRUTTURA_SUFFICIENTE = 0.5

# ---------------------------------------------------------------------------
# COLORI
# ---------------------------------------------------------------------------

class Colori:
    VERDE = "#d4edda"
    VERDE_TESTO = "#155724"
    GIALLO = "#fff3cd"
    GIALLO_TESTO = "#856404"
    ROSSO = "#f8d7da"
    ROSSO_TESTO = "#721c24"
    NEUTRO = "#f8f9fa"
    NEUTRO_TESTO = "#6c757d"

    # Per grafici
    BLU_SCURO = "#1f4e78"
    BLU_MEDIO = "#2e75b6"
    BLU_CHIARO = "#bdd7ee"
    GIALLO_GRAFICO = "#ffc000"
    ROSSO_GRAFICO = "#c00000"
    ARANCIO = "#ed7d31"

# ---------------------------------------------------------------------------
# ORDINE MENU
# ---------------------------------------------------------------------------

MENU_ORDINE = [
    "🏠 Dashboard di Controllo",
    "🚨 Alert Scostamenti",
    "📊 Scorecard Indici",
    "💰 Analisi Ricavi",
    "💸 Analisi Costi",
    "👥 Analisi Clienti",
    "📈 Conto Economico",
    "📊 Stato Patrimoniale",
    "🏦 Posizione Finanziaria Netta",
    "🔍 Analisi Dettaglio",
]
