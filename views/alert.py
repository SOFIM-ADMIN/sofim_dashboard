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
    st.info("Configura le soglie e le categorie da monitorare, poi esamina gli scostamenti anno su anno.")

    st.subheader("⚙️ Configurazione Analisi")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])

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

    with col_c3:
        st.markdown("**Categorie da monitorare:**")
        alert_ricavi = st.checkbox("📈 Ricavi", value=True, help="Aumento = positivo, Diminuzione = negativo")
        alert_costi = st.checkbox("📉 Costi", value=True, help="Diminuzione = positivo, Aumento = negativo")
        alert_patrimonio = st.checkbox("🏦 Patrimonio", value=False, help="Variazioni sempre segnalate")

    st.divider()

    tipi = []
    if alert_ricavi: tipi.append("RICAVI")
    if alert_costi: tipi.append("COSTI")
    if alert_patrimonio: tipi.append("PATRIMONIO")

    if not tipi:
        st.warning("Seleziona almeno una categoria da monitorare.")
        return

    with st.spinner("Analisi scostamenti in corso..."):
        df_alert = calcola_alert(df_final, soglia_gialla, soglia_rossa, tipi)

    if df_alert.empty:
        st.info("Dati insufficienti per il confronto anno su anno (servono almeno 2 anni).")
        return

    n_critici = len(df_alert[df_alert["Stato"] == "🔴 CRITICO"])
    n_attenzione = len(df_alert[df_alert["Stato"] == "🟡 ATTENZIONE"])
    n_opportunita = len(df_alert[df_alert["Stato"] == "🟢 OPPORTUNITA"])
    n_ok = len(df_alert[df_alert["Stato"] == "⚪ OK"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Conti Monitorati", len(df_alert))
    col2.metric("🔴 Critici", n_critici, delta_color="off")
    col3.metric("🟡 Attenzione", n_attenzione, delta_color="off")
    col4.metric("🟢 Opportunita", n_opportunita, delta_color="off")
    col5.metric("⚪ OK", n_ok, delta_color="off")

    st.markdown("""
    <style>
    .alert-legend {font-size: 12px; color: #666; margin-bottom: 10px;}
    </style>
    <div class="alert-legend">
    <b>Legenda:</b> 🔴 Critico = variazione dannosa forte | 🟡 Attenzione = variazione dannosa moderata | 
    🟢 Opportunita = variazione favorevole | ⚪ OK = entro soglie
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Critici", "🟡 Attenzione", "🟢 Opportunita", "📊 Tutti"])

    for tab, stato_filter in [(tab1, "🔴 CRITICO"), (tab2, "🟡 ATTENZIONE"), (tab3, "🟢 OPPORTUNITA"), (tab4, None)]:
        with tab:
            if stato_filter:
                df_view = df_alert[df_alert["Stato"] == stato_filter].copy()
                if df_view.empty:
                    st.success(f"Nessun conto in stato {stato_filter} — ottimo!")
                    continue
            else:
                df_view = df_alert.copy()

            styler = df_view.style.format({
                "Importo_C": "€ {:,.2f}",
                "Importo_P": "€ {:,.2f}",
                "Variazione_€": "€ {:+,.2f}",
                "Variazione_%": "{:+.1f}%"
            }).map(color_stato, subset=["Stato"])                .map(color_variazione_importo, subset=["Variazione_€"])                .map(color_variazione_pct, subset=["Variazione_%"])

            st.dataframe(styler, use_container_width=True, hide_index=True)

            csv = df_view.to_csv(index=False).encode('utf-8')
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

    top_critici = df_alert[df_alert["Stato"] == "🔴 CRITICO"].nlargest(5, "Variazione_%_abs")
    if not top_critici.empty:
        st.markdown("#### 🔴 Top Critici (da monitorare urgentemente)")
        import plotly.express as px
        fig_crit = px.bar(
            top_critici, y="Descrizione Conto", x="Variazione_%", color="Impatt_o",
            color_discrete_map={"NEGATIVO": "#dc3545", "POSITIVO": "#28a745", "NEUTRO": "#ffc107"},
            orientation="h", title="Top 5 variazioni critiche", text="Variazione_%"
        )
        fig_crit.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_crit, use_container_width=True)

    top_opp = df_alert[df_alert["Stato"] == "🟢 OPPORTUNITA"].nlargest(5, "Variazione_%_abs")
    if not top_opp.empty:
        st.markdown("#### 🟢 Top Opportunita (variazioni favorevoli)")
        import plotly.express as px
        fig_opp = px.bar(
            top_opp, y="Descrizione Conto", x="Variazione_%", color="Impatt_o",
            color_discrete_map={"POSITIVO": "#28a745", "NEGATIVO": "#dc3545", "NEUTRO": "#ffc107"},
            orientation="h", title="Top 5 opportunita", text="Variazione_%"
        )
        fig_opp.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_opp, use_container_width=True)
