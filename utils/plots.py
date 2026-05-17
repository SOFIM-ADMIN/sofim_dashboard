"""
Sofim Financial Dashboard - Utilities Grafiche
"""

import plotly.express as px
import plotly.graph_objects as go


def create_clean_pie(df_pie, title):
    """Grafico a torta (donut) pulito per il mix ricavi."""
    df_pie = (
        df_pie
        .dropna(subset=["Importo_Netto"])
        .pipe(lambda d: d[d["Importo_Netto"] > 0])
        .sort_values("Importo_Netto", ascending=False)
    )
    fig = px.pie(
        df_pie,
        values="Importo_Netto",
        names="Descrizione Conto",
        title=title,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        textinfo="percent",
        textposition="auto",
        textfont_size=12,
        marker=dict(line=dict(color="#FFFFFF", width=1)),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
        margin=dict(t=50, b=100, l=10, r=10),
        height=550,
    )
    return fig


def create_pareto_chart(df_display, anno_sel, mese_limite):
    """Diagramma di Pareto per analisi costi."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_display["Descrizione Conto"],
        y=df_display[anno_sel],
        name="Costo per Voce",
        marker_color="#3498db"
    ))

    fig.add_trace(go.Scatter(
        x=df_display["Descrizione Conto"],
        y=df_display["% Cumulata"],
        name="% Cumulata",
        yaxis="y2",
        line=dict(color="#e74c3c", width=3),
        mode="lines+markers"
    ))

    fig.update_layout(
        title=f"Diagramma di Pareto - {anno_sel} (Fino al mese {mese_limite})",
        yaxis=dict(title="Importo (€)"),
        yaxis2=dict(title="Percentuale Cumulata (%)", overlaying="y", side="right", range=[0, 105]),
        showlegend=True,
        height=500,
        xaxis=dict(tickangle=-45)
    )
    return fig


def create_radar_chart(categories, values_c, values_p, anno_sel, anno_prec):
    """Grafico radar per confronto indici."""
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_c + [values_c[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name=f'{anno_sel}',
        line_color='#2ecc71',
        fillcolor='rgba(46, 204, 113, 0.3)'
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_p + [values_p[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name=f'{anno_prec}',
        line_color='#3498db',
        fillcolor='rgba(52, 152, 219, 0.3)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Profilo Indici di Bilancio (scala normalizzata 0-100)",
        height=600
    )
    return fig


def create_alert_histogram(df_alert, soglia_gialla, soglia_rossa):
    """Istogramma distribuzione scostamenti."""
    # Crea colonna temporanea con valore assoluto per filtro
    df_plot = df_alert.copy()
    df_plot["_var_pct_abs"] = df_plot["Variazione_%"].abs()

    fig = px.histogram(
        df_plot[df_plot["_var_pct_abs"] < 200],
        x="Variazione_%",
        color="Stato",
        color_discrete_map={
            "🔴 CRITICO": "#dc3545",
            "🟡 ATTENZIONE": "#ffc107",
            "🟢 OPPORTUNITA": "#28a745",
            "⚪ OK": "#6c757d"
        },
        nbins=30,
        title="Distribuzione variazioni % anno su anno",
        labels={"Variazione_%": "Variazione %", "count": "N. Conti"}
    )
    fig.add_vline(x=soglia_gialla, line_dash="dash", line_color="orange", 
                  annotation_text=f"Soglia gialla ({soglia_gialla}%)")
    fig.add_vline(x=-soglia_gialla, line_dash="dash", line_color="orange")
    fig.add_vline(x=soglia_rossa, line_dash="dash", line_color="red", 
                  annotation_text=f"Soglia rossa ({soglia_rossa}%)")
    fig.add_vline(x=-soglia_rossa, line_dash="dash", line_color="red")
    return fig
