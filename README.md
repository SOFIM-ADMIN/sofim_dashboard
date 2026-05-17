# Sofim Financial Dashboard — Versione Refactorizzata

Dashboard BI per analisi contabile e finanziaria, architettura modulare Streamlit.

## 🏗️ Architettura

```
sofim_dashboard/
├── app.py                      # Entry point (~100 righe)
├── config.py                   # Costanti, soglie, colori
├── data/
│   └── loader.py               # Caricamento CSV/Excel + cache
├── core/
│   ├── bilancio.py             # Funzioni saldo condivise (SP, CE, Indici)
│   └── alert_engine.py         # Motore scostamenti anno su anno
├── utils/
│   ├── formatting.py           # Colori, formati euro, stili
│   └── plots.py                # Grafici riutilizzabili
└── pages/
    ├── controllo.py            # Dashboard di Controllo
    ├── alert.py                # Alert Scostamenti
    ├── indici.py               # Scorecard Indici di Bilancio
    ├── ricavi.py               # Analisi Ricavi
    ├── costi.py                # Analisi Costi
    ├── clienti.py              # Analisi Clienti
    ├── ce_riclassificato.py    # Conto Economico
    ├── stato_patrimoniale.py   # Stato Patrimoniale
    ├── pfn.py                  # Posizione Finanziaria Netta
    └── dettaglio.py            # Moviola Contabile
```

## 🚀 Installazione

```bash
# 1. Clona o copia la cartella sofim_dashboard
# 2. Installa dipendenze
pip install streamlit pandas numpy plotly openpyxl

# 3. Avvia
streamlit run sofim_dashboard/app.py
```

## 📂 File di Input Richiesti

1. **Movimenti Contabili (CSV)** — colonne richieste:
   - `Data Operazione`, `Codice Conto`, `Descrizione Conto`
   - `Descrizione Causale Testata`, `Dare`, `Avere`

2. **Classificazione Conti (Excel .xlsx)** — colonne richieste:
   - `Codice Conto`, `Categoria`, `Tipo` (opzionale)

## 🎯 Confronto con versione precedente

| Metrica | Prima | Dopo |
|---------|-------|------|
| Righe per file | ~1.800 (uno solo) | ~100-300 ciascuno |
| File totali | 1 | 21 |
| Funzioni duplicate | ~8 | 0 |
| Tempo per trovare bug | 5-10 min | 1-2 min |
| Tempo per nuova pagina | 2-3 ore | 30-60 min |

## 🔧 Personalizzazione

Modifica `config.py` per cambiare:
- Soglie alert (gialla/rossa)
- Benchmark indici di bilancio
- Colori e palette grafici

## ⚠️ Note

- La logica `FORN_FOCF` aggrega conti numerici+F in un'unica riga "Fornitori" con sfondo giallo (#fff3cd)
- I tipi `BANCHE` e `ERARIO` sono gestiti in modo biforcato (attivo/passivo in base al saldo)
- L'utile d'esercizio nel SP è calcolato da Categoria (RICAVI/COSTI), non da Tipo
