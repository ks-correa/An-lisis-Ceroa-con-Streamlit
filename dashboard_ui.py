"""Estilos y formato compartido de los gráficos del proyecto."""

import streamlit as st


def aplicar_estilo():
    st.markdown("""
    <style>
    .block-container {max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem;}
    h1 {font-size: 2rem !important; letter-spacing: -.04em;}
    h2, h3 {letter-spacing: -.025em;}
    [data-testid="stMetric"] {border: 1px solid #dbe3ed; border-radius: 12px;
        padding: 18px 16px; min-height: 150px;}
    [data-testid="stMetricValue"] {font-size: clamp(1.1rem, 1.7vw, 1.8rem);}
    [data-testid="stMetricLabel"] {font-weight: 600;}
    [data-testid="stMetricDelta"] {font-size: .8rem;}
    [data-testid="stPlotlyChart"] {border: 1px solid #dbe3ed; border-radius: 12px;
        padding: 8px; margin-bottom: 20px; overflow: hidden;}
    [data-testid="stSidebar"] {border-right: 1px solid #dbe3ed;}
    </style>
    """, unsafe_allow_html=True)


def mostrar_grafica(fig, moneda="COP", tipo="dinero", leyenda_anillo=False):
    """Aplica el formato común y muestra valores con sus unidades al pasar el cursor."""
    fig.update_layout(
        template="plotly_white", height=440,
        font=dict(family="Arial, sans-serif", size=12, color="#334155"),
        title=dict(font=dict(size=17, color="#0f172a"), x=0, xanchor="left"),
        margin=dict(l=20, r=20, t=65, b=100),
        hovermode="closest", hoverdistance=30,
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#cbd5e1",
                        font=dict(size=13, color="#0f172a"), namelength=-1),
        legend=dict(title_text="", orientation="h", y=-.22, x=0,
                    font=dict(size=11), itemclick="toggle", itemdoubleclick="toggleothers"),
        separators=",.", dragmode=False,
    )
    for trace in fig.data:
        if trace.type == "pie":
            trace.update(textinfo="percent", textposition="inside",
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f} " + moneda +
                              "<br>Participación: %{percent}<extra></extra>")
            fig.update_layout(showlegend=leyenda_anillo)
        elif trace.type in ("scatter", "bar"):
            valor = "%{y:,.0f} usuarios" if tipo == "usuarios" else "$%{y:,.0f} " + moneda
            nombre = trace.name.replace("<", "&lt;").replace(">", "&gt;")
            encabezado = nombre + "<br>" if nombre and tipo != "usuarios" else ""
            trace.update(hovertemplate="<b>%{x}</b><br>" + encabezado + valor + "<extra></extra>")
            if trace.type == "bar":
                trace.update(textposition="none")
    if not any(trace.type == "pie" for trace in fig.data):
        fig.update_xaxes(title_text=None, showgrid=False, automargin=True, nticks=7)
        fig.update_yaxes(title_text="Usuarios" if tipo == "usuarios" else moneda,
                         gridcolor="#edf2f7", zeroline=False, automargin=True,
                         tickformat=",.0f" if tipo == "usuarios" else "~s")
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": False, "scrollZoom": False,
                            "displaylogo": False})

