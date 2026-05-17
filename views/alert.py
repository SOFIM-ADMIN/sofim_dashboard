"""
Sofim Financial Dashboard - Pagina Alert Scostamenti
"""

import streamlit as st
import pandas as pd
from core.alert_engine import calcola_alert
from utils.formatting import color_stato, color_variazione_importo, color_variazione_pct
from utils.plots import create_alert_histogram


def render(df_final: pd.DataFrame) -> None:
    st.title("🚨 Centro Alert & Scostamenti")
    st.info("Configura le soglie, le categorie e l'anno di riferimento, poi esamina gli scostamenti.")

    st.subheader("⚙️ Configurazione Analisi")

    # Selettore anno di riferimento
    anni_disponibili = sorted(df_final["Anno"].unique(), reverse=True)
    if len(anni_disponibili) < 2:
        st.warning("Servono almeno 2 anni di dati per l'analisi degli scostamenti.")
        return

    col_anno, col_c1, col_c2 = st.columns([1, 1, 1])

    with col_anno:
        anno_rif = st.selectbox(
            "📅 Anno di riferimento",
            options=anni_disponibili[:-1],  # Esclude l'ultimo (più recente) perché confrontiamo con precedente
            index=0,
            help="Seleziona l'anno da confrontare con il precedente"
        )

    with col_c1:
        soglia_gialla = st.slider(
            "Soglia ATTENZIONE (%)",
            min_value=5, max_value=50, value=15, step=5,
            help="Variazione dannosa superiore a questa % → alert giallo"
        )

    with col_c2:
        soglia_rossa = st.slider(
            "Soglia CRITICO (%)",
            min_value=soglia_gialla + 5, max_value=100, value=30, step=5,
            help="Variazione dannosa superiore a questa % → alert rosso"
        )

    st.markdown("**Categorie da monitorare:**")
    col_cat1, col_cat2, col_cat3, col_cat4 = st.columns(4)

    with col_cat1:
        alert_ricavi = st.checkbox("📈 Ricavi", value=True, help="Aumento = positivo, Diminuzione = negativo")
    with col_cat2:
        alert_costi = st.checkbox("📉 Costi", value=True, help="Diminuzione = positivo, Aumento = negativo")
    with col_cat3:
        alert_attivita = st.checkbox("💰 Attività", value=False, help="Variazioni attività patrimoniali")
    with col_cat4:
        alert_passivita = st.checkbox("🏦 Passività", value=False, help="Variazioni passività patrimoniali")

    st.divider()

    tipi = []
    if alert_ricavi: tipi.append("RICAVI")
    if alert_costi: tipi.append("COSTI")
    if alert_attivita: tipi.append("ATTIVITA")
    if alert_passivita: tipi.append("PASSIVITA")

    if not tipi:
        st.warning("Seleziona almeno una categoria da monitorare.")
        return

    with st.spinner("Analisi scostamenti in corso..."):
        df_alert = calcola_alert(df_final, soglia_gialla, soglia_rossa, tipi, anno_rif)

    if df_alert.empty:
        st.info("Dati insufficienti per il confronto anno su anno.")
        return

    n_critici = len(df_alert[df_alert["Stato"] == "🔴 CRITICO"])
    n_attenzione = len(df_alert[df_alert["Stato"] == "🟡 ATTENZIONE"])
    n_opportunita = len(df_alert[df_alert["Stato"] == "🟢 OPPORTUNITA"])
    n_ok = len(df_alert[df_alert["Stato"] == "⚪ OK"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Conti Monitorati", len(df_alert))
    col2.metric("🔴 Critici", n_critici, delta_color="off")
    col3.metric("🟡 Attenzione", n_attenzione, delta_color="off")
    col4.metric("🟢 Opportunità", n_opportunita, delta_color="off")
    col5.metric("⚪ OK", n_ok, delta_color="off")

    st.markdown("""
    <style>
    .alert-legend {font-size: 12px; color: #666; margin-bottom: 10px;}
    </style>
    <div class="alert-legend">
    <b>Legenda:</b> 🔴 Critico = variazione dannosa forte | 🟡 Attenzione = variazione dannosa moderata | 
    🟢 Opportunità = variazione favorevole | ⚪ OK = entro soglie
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Critici", "🟡 Attenzione", "🟢 Opportunità", "📊 Tutti"])

    for tab, stato_filter in [(tab1, "🔴 CRITICO"), (tab2, "🟡 ATTENZIONE"), (tab3, "🟢 OPPORTUNITA"), (tab4, None)]:
        with tab:
            if stato_filter:
                df_view = df_alert[df_alert["Stato"] == stato_filter].copy()
                if df_view.empty:
                    st.success(f"Nessun conto in stato {stato_filter} — ottimo!")
                    continue
            else:
                df_view = df_alert.copy()

            # NUOVO: Aggiungi riga TOTALE in fondo
            totale = {
                "Codice Conto": "",
                "Descrizione Conto": "TOTALE",
                "Cat_Safe": "",
                "Anno_Cor": df_view["Anno_Cor"].iloc[0] if not df_view.empty else anno_rif,
                "Importo_C": df_view["Importo_C"].sum(),
                "Anno_Prec": df_view["Anno_Prec"].iloc[0] if not df_view.empty else anno_rif - 1,
                "Importo_P": df_view["Importo_P"].sum(),
                "Variazione_€": df_view["Variazione_€"].sum(),
                "Variazione_%": 0.0,
                "Impatt_o": "NEUTRO",
                "Stato": "⚪ OK"
            }

            # Calcola variazione % del totale
            base_tot = abs(totale["Importo_P"]) if totale["Importo_P"] != 0 else abs(totale["Importo_C"])
            if base_tot != 0:
                totale["Variazione_%"] = (totale["Variazione_€"] / base_tot) * 100

            # Crea DataFrame con il totale e concatena in fondo
            df_totale = pd.DataFrame([totale])
            df_view = pd.concat([df_view, df_totale], ignore_index=True)

            # NUOVO: Aggiungi colonna per evidenziare la riga totale
            df_view["_is_totale"] = df_view["Descrizione Conto"] == "TOTALE"

            # FIX: Usa .apply() con funzioni helper
            def _apply_color_stato(col):
                return [color_stato(v) for v in col]

            def _apply_color_importo(col):
                return [color_variazione_importo(v) for v in col]

            def _apply_color_pct(col):
                return [color_variazione_pct(v) for v in col]

            # NUOVO: Funzione per evidenziare riga totale con sfondo grigio
            def _highlight_totale(row):
                if row["_is_totale"]:
                    return ['background-color: #e9ecef; font-weight: bold;'] * len(row)
                return [''] * len(row)

            styler = df_view.style.format({
                "Importo_C": "€ {:,.2f}",
                "Importo_P": "€ {:,.2f}",
                "Variazione_€": "€ {:+,.2f}",
                "Variazione_%": "{:+.1f}%"
            }).apply(_apply_color_stato, subset=["Stato"])              .apply(_apply_color_importo, subset=["Variazione_€"])              .apply(_apply_color_pct, subset=["Variazione_%"])              .apply(_highlight_totale, axis=1)

            # Rimuovi colonna ausiliaria dalla visualizzazione
            styler = styler.hide(subset=["_is_totale"], axis="columns")

            st.dataframe(styler, use_container_width=True, hide_index=True)

            csv = df_view.drop(columns=["_is_totale"]).to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Scarica {stato_filter or 'Tutti'}",
                data=csv,
                file_name=f"alert_{stato_filter or 'completo'}.csv".replace(" ", "_").replace("🔴", "critico").replace("🟡", "attenzione").replace("🟢", "opportunita"),
                mime="text/csv",
                key=f"dl_{stato_filter or 'all'}"
            )

    st.divider()
    st.subheader("📈 Distribuzione degli Scostamenti")
    fig_hist = create_alert_histogram(df_alert, soglia_gialla, soglia_rossa)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("🏆 Top 10 Scostamenti per Impatto")

    top_critici = df_alert[df_alert["Stato"] == "🔴 CRITICO"].copy()
    if not top_critici.empty:
        top_critici["_abs_var"] = top_critici["Variazione_%"].abs()
        top_critici = top_critici.nlargest(5, "_abs_var")
        st.markdown("#### 🔴 Top Critici (da monitorare urgentemente)")
        import plotly.express as px
        fig_crit = px.bar(
            top_critici, y="Descrizione Conto", x="Variazione_%", color="Impatt_o",
            color_discrete_map={"NEGATIVO": "#dc3545", "POSITIVO": "#28a745", "NEUTRO": "#ffc107"},
            orientation="h", title="Top 5 variazioni critiche", text="Variazione_%"
        )
        fig_crit.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_crit, use_container_width=True)

    top_opp = df_alert[df_alert["Stato"] == "🟢 OPPORTUNITA"].copy()
    if not top_opp.empty:
        top_opp["_abs_var"] = top_opp["Variazione_%"].abs()
        top_opp = top_opp.nlargest(5, "_abs_var")
        st.markdown("#### 🟢 Top Opportunità (variazioni favorevoli)")
        import plotly.express as px
        fig_opp = px.bar(
            top_opp, y="Descrizione Conto", x="Variazione_%", color="Impatt_o",
            color_discrete_map={"POSITIVO": "#28a745", "NEGATIVO": "#dc3545", "NEUTRO": "#ffc107"},
            orientation="h", title="Top 5 opportunità", text="Variazione_%"
        )
        fig_opp.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_opp, use_container_width=True)
