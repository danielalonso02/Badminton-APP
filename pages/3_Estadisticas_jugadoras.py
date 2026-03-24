"""
pages/3_Analisis_jugadoras.py  ·  Análisis por jugadora
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_df, preprocess, STYLES, sidebar_logo, PLAYER_COLORS

st.set_page_config(page_title="Estadísticas jugadoras · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

# ── Datos ────────────────────────────────
df = get_df()
strokes, _, _, player1, player2 = preprocess(df)

jugador_col = "Jugador del golpeo"
p1 = strokes[strokes[jugador_col] == player1] if jugador_col in strokes.columns else strokes.iloc[0:0]
p2 = strokes[strokes[jugador_col] == player2] if jugador_col in strokes.columns else strokes.iloc[0:0]

DARK_BG   = "#0f1117"
GRID_COL  = "#1f2937"
FONT_COL  = "#9ca3af"
BASE_LAYOUT = dict(
    paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
    font=dict(family="DM Sans, sans-serif", color=FONT_COL),
    margin=dict(l=40, r=20, t=48, b=40),
    legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#f9fafb")),
)

def ax(title=""):
    return dict(title=title, tickfont=dict(size=10, color=FONT_COL),
                gridcolor=GRID_COL, zerolinecolor=GRID_COL)


# ─────────────────────────────────────────
# 1 · FASE DE JUEGO
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Iniciativa · Construcción · Ataque · Defensa</div>',
            unsafe_allow_html=True)

if "Game Phase" in strokes.columns:
    col_bar, col_pie = st.columns(2)

    # Tonalidades por jugadora: P1=azules, P2=rosas
    # Cada fase usa una tonalidad distinta bien diferenciada
    PLAYER_PHASE_COLORS = {
        player1: ["#93c5fd", "#3b82f6", "#1e40af"],   # azul claro → medio → oscuro
        player2: ["#f9a8d4", "#ec4899", "#9d174d"],   # rosa claro → medio → oscuro
    }

    # Barras agrupadas
    with col_bar:
        p1_counts = p1["Game Phase"].value_counts()
        p2_counts = p2["Game Phase"].value_counts()
        all_phases = sorted(set(p1_counts.index.tolist() + p2_counts.index.tolist()))

        fig = go.Figure()
        for player, pdata_g, counts in [
            (player1, p1, p1_counts),
            (player2, p2, p2_counts),
        ]:
            tones = PLAYER_PHASE_COLORS.get(player, PLAYER_PHASE_COLORS[player1])
            for i, ph in enumerate(all_phases):
                fig.add_trace(go.Bar(
                    name=f"{player.split()[0]} · {ph}",
                    x=[ph], y=[counts.get(ph, 0)],
                    marker_color=tones[i % len(tones)],
                    legendgroup=player.split()[0],
                    showlegend=True,
                ))
        fig.update_layout(**BASE_LAYOUT, barmode="group", height=300,
            title=dict(text="Golpes por iniciativa", font=dict(size=12, color=FONT_COL), x=0),
            xaxis=ax(), yaxis=ax("Nº golpes"))
        st.plotly_chart(fig, use_container_width=True)

    # Donut side by side
    with col_pie:
        fig2 = go.Figure()
        for i, (player, pdata, color) in enumerate([
            (player1.split()[0], p1, PLAYER_COLORS[0]),
            (player2.split()[0], p2, PLAYER_COLORS[1]),
        ]):
            counts = pdata["Game Phase"].value_counts()
            fig2.add_trace(go.Pie(
                labels=counts.index.tolist(),
                values=counts.values.tolist(),
                name=player,
                hole=0.55,
                domain={"x": [0, 0.46] if i == 0 else [0.54, 1]},
                marker=dict(colors=["#60a5fa", "#f472b6", "#4ade80", "#facc15", "#a78bfa"][:len(counts)]),
                textinfo="percent",
                textfont=dict(size=11),
                title=dict(
                    text=f"<b>{player}</b>",
                    font=dict(size=18, color="#f9fafb"),
                    position="bottom center",
                ),
            ))
        fig2.update_layout(**BASE_LAYOUT, height=340, showlegend=True,
            title=dict(text="Distribución por iniciativa", font=dict(size=12, color=FONT_COL), x=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Evolución por set — una columna por jugadora en cada set
    if "Set" in strokes.columns:
        sets = sorted(strokes["Set"].dropna().unique().astype(int))
        all_phases_sorted = sorted(strokes["Game Phase"].dropna().unique())
        fig3 = go.Figure()

        # Eje X: "Set 1 · P1", "Set 1 · P2", "Set 2 · P1", etc.
        x_labels = []
        for s in sets:
            x_labels.append(f"S{s} · {player1.split()[0]}")
            x_labels.append(f"S{s} · {player2.split()[0]}")

        for i, phase in enumerate(all_phases_sorted):
            vals = []
            colors = []
            for s in sets:
                for player, pdata, tones in [
                    (player1, p1, PLAYER_PHASE_COLORS.get(player1, ["#93c5fd","#3b82f6","#1e40af"])),
                    (player2, p2, PLAYER_PHASE_COLORS.get(player2, ["#f9a8d4","#ec4899","#9d174d"])),
                ]:
                    vals.append(pdata[(pdata["Set"] == s) & (pdata["Game Phase"] == phase)].shape[0])
                    colors.append(tones[i % len(tones)])

            fig3.add_trace(go.Bar(
                name=phase,
                x=x_labels, y=vals,
                marker_color=colors,
                legendgroup=phase,
                showlegend=i < len(all_phases_sorted),
            ))

        fig3.update_layout(**BASE_LAYOUT, barmode="stack", height=320,
            title=dict(text="Iniciativa por set y jugadora", font=dict(size=12, color=FONT_COL), x=0),
            xaxis=dict(title="", tickfont=dict(size=11, color="#f9fafb"),
                       gridcolor=GRID_COL, zerolinecolor=GRID_COL),
            yaxis=ax("Nº golpes"))
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No se encontró la columna 'Game Phase'.")


# ─────────────────────────────────────────
# 2 · TIPO DE SERVICIO Y ZONA DE SAQUE
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Tipo de servicio y zona de saque</div>',
            unsafe_allow_html=True)

service_col = "Type of service"
zona_c1_col = "Zona de C1"

if service_col in strokes.columns:
    # Todos los tipos de saque posibles (unión de ambas jugadoras)
    all_service_types = sorted(strokes[service_col].dropna().unique().tolist())
    # Todas las zonas posibles: 1-12
    all_zones = list(range(1, 13))

    col_s1, col_s2 = st.columns(2)

    for col_ui, player, pdata, color in [
        (col_s1, player1.split()[0], p1, PLAYER_COLORS[0]),
        (col_s2, player2.split()[0], p2, PLAYER_COLORS[1]),
    ]:
        with col_ui:
            svc = pdata[service_col].dropna()
            if svc.empty:
                st.info(f"Sin datos de servicio para {player}.")
                continue

            # Contar todos los tipos, rellenando con 0 los que no aparecen
            svc_counts = svc.value_counts()
            svc_values = [int(svc_counts.get(t, 0)) for t in all_service_types]

            fig_svc = go.Figure(go.Bar(
                x=svc_values, y=all_service_types,
                orientation="h", marker_color=color, opacity=0.85,
            ))
            fig_svc.update_layout(**BASE_LAYOUT, height=max(180, len(all_service_types) * 48 + 60),
                title=dict(text=f"{player} · tipo de servicio",
                           font=dict(size=12, color=FONT_COL), x=0),
                xaxis=ax("Nº saques"),
                yaxis=dict(tickfont=dict(size=10, color="#f9fafb"),
                           categoryorder="total ascending"))
            st.plotly_chart(fig_svc, use_container_width=True)

            if zona_c1_col in pdata.columns:
                zona_raw = pd.to_numeric(pdata[zona_c1_col], errors="coerce").dropna()
                zona_counts = zona_raw.value_counts()
                zona_values = [int(zona_counts.get(z, 0)) for z in all_zones]

                fig_zona = go.Figure(go.Bar(
                    x=[str(z) for z in all_zones],
                    y=zona_values,
                    marker_color=color, opacity=0.75,
                ))
                fig_zona.update_layout(**BASE_LAYOUT, height=220,
                    title=dict(text=f"{player} · zona de saque (C1)",
                               font=dict(size=12, color=FONT_COL), x=0),
                    xaxis=dict(title="Zona", tickmode="array",
                               tickvals=[str(z) for z in all_zones],
                               ticktext=[str(z) for z in all_zones],
                               tickfont=dict(size=10, color="#f9fafb"),
                               gridcolor=GRID_COL),
                    yaxis=ax("Nº saques"))
                st.plotly_chart(fig_zona, use_container_width=True)
else:
    st.info("No se encontró la columna 'Type of service'.")


# ─────────────────────────────────────────
# 3 · RALLY OUTCOME · ERRORES
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Rally outcome · errores forzados y no forzados</div>',
            unsafe_allow_html=True)

outcome_col = "Rally Outcome"
if outcome_col in strokes.columns:
    # Quedarse solo con la última fila de cada rally (donde está el resultado)
    last_strokes = strokes.sort_values("Stroke").groupby("Rally").last().reset_index()
    outcomes = last_strokes[outcome_col].dropna()

    def classify_outcome(outcome, p1_name, p2_name):
        o = str(outcome)
        if f"Error {p2_name}" in o:   return p1_name.split()[0], "Error no forzado"
        if f"Error {p1_name}" in o:   return p2_name.split()[0], "Error no forzado"
        if f"Unforced {p1_name}" in o: return p2_name.split()[0], "Error no forzado"
        if f"Unforced {p2_name}" in o: return p1_name.split()[0], "Error no forzado"
        if p1_name in o:               return p1_name.split()[0], "Punto ganado"
        if p2_name in o:               return p2_name.split()[0], "Punto ganado"
        return "Otro", o

    classified = last_strokes[outcome_col].dropna().apply(
        lambda o: pd.Series(classify_outcome(o, player1, player2),
                            index=["ganador", "tipo"])
    )
    last_strokes = last_strokes.join(classified)

    all_tipos = ["Error no forzado", "Punto ganado"]

    total_rallies = len(last_strokes)
    fig_out = go.Figure()
    for player, color in [(player1.split()[0], PLAYER_COLORS[0]),
                          (player2.split()[0], PLAYER_COLORS[1])]:
        pdata_out = last_strokes[last_strokes["ganador"] == player]
        tipo_counts = pdata_out["tipo"].value_counts() if not pdata_out.empty else pd.Series()
        vals = [int(tipo_counts.get(t, 0)) for t in all_tipos]
        pcts = [round(v / total_rallies * 100, 1) if total_rallies > 0 else 0 for v in vals]
        fig_out.add_trace(go.Bar(
            name=player,
            x=all_tipos, y=vals,
            marker_color=color, opacity=0.85,
            text=[f"{p}%" for p in pcts],
            textposition="outside",
            textfont=dict(size=10, color=FONT_COL),
        ))
    max_val_out = max([int(last_strokes[last_strokes["ganador"]==p]["tipo"].value_counts().get(t,0))
                       for p in [player1.split()[0], player2.split()[0]] for t in all_tipos], default=1)
    fig_out.update_layout(**BASE_LAYOUT, barmode="group", height=320,
        title=dict(text="Puntos ganados por tipo · comparativa", font=dict(size=12, color=FONT_COL), x=0),
        xaxis=dict(tickfont=dict(size=12, color="#f9fafb"), gridcolor=GRID_COL),
        yaxis=dict(**ax("Nº puntos"), range=[0, max_val_out * 1.25]))
    fig_out.update_layout(legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#f9fafb")))
    st.plotly_chart(fig_out, use_container_width=True)

    # Tabla resumen
    summary_rows = []
    for player in [player1.split()[0], player2.split()[0]]:
        pdata_out = last_strokes[last_strokes["ganador"] == player]
        total      = len(pdata_out)
        ganados    = len(pdata_out[pdata_out["tipo"] == "Punto ganado"])
        errores    = len(pdata_out[pdata_out["tipo"] == "Error no forzado"])
        summary_rows.append({"Jugadora": player, "Puntos totales": total,
                              "Puntos directos": ganados, "Errores rivales": errores})
    st.dataframe(pd.DataFrame(summary_rows).set_index("Jugadora"),
                 use_container_width=True)
else:
    st.info("No se encontró la columna 'Rally Outcome'.")


# ─────────────────────────────────────────
# 4 · BARRIDO FUERTE Y REVÉS
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Golpes especiales · barrido fuerte y revés</div>',
            unsafe_allow_html=True)

special_cols = {
    "Barrido Fuerte": "Barrido fuerte",
    "Reves":          "Revés",
}

available = {k: v for k, v in special_cols.items() if k in strokes.columns}

if available:
    col_sp1, col_sp2 = st.columns(2)
    for col_ui, player, pdata, color in [
        (col_sp1, player1.split()[0], p1, PLAYER_COLORS[0]),
        (col_sp2, player2.split()[0], p2, PLAYER_COLORS[1]),
    ]:
        with col_ui:
            rows = []
            for col_name, label in available.items():
                total   = len(pdata)
                n       = pdata[col_name].dropna().astype(str).str.strip().ne("").sum()
                pct     = round(n / total * 100, 1) if total > 0 else 0
                rows.append({"Golpe": label, "Nº": n, "%": pct})

            fig_sp = go.Figure()
            df_sp = pd.DataFrame(rows)
            fig_sp.add_trace(go.Bar(
                x=df_sp["Golpe"], y=df_sp["Nº"],
                marker_color=color, opacity=0.85,
                text=df_sp["%"].apply(lambda v: f"{v}%"),
                textposition="outside",
                textfont=dict(size=10, color=FONT_COL),
            ))
            fig_sp.update_layout(**BASE_LAYOUT, height=320,
                title=dict(text=f"{player} · golpes especiales",
                           font=dict(size=12, color=FONT_COL), x=0),
                xaxis=ax(), yaxis=dict(**ax("Nº golpes"),
                                       range=[0, df_sp["Nº"].max() * 1.25 if not df_sp.empty else 10]),
                uniformtext_minsize=8, uniformtext_mode="hide")
            st.plotly_chart(fig_sp, use_container_width=True)

    # Comparativa por iniciativa
    if "Game Phase" in strokes.columns:
        st.markdown("<div style='font-size:12px;color:#6b7280;margin-top:8px;'>Por iniciativa</div>",
                    unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(len(available))
        for col_ui, (col_name, label) in zip([col_f1, col_f2], available.items()):
            with col_ui:
                fig_ph = go.Figure()
                for player, pdata, color in [(player1.split()[0], p1, PLAYER_COLORS[0]),
                                              (player2.split()[0], p2, PLAYER_COLORS[1])]:
                    phases = sorted(pdata["Game Phase"].dropna().unique())
                    vals = [pdata[(pdata["Game Phase"] == ph) &
                                  pdata[col_name].notna() &
                                  pdata[col_name].astype(str).str.strip().ne("")].shape[0]
                            for ph in phases]
                    total_p = len(pdata)
                    pcts = [round(v / total_p * 100, 1) if total_p > 0 else 0 for v in vals]
                    fig_ph.add_trace(go.Bar(
                        name=player, x=phases, y=vals,
                        marker_color=color, opacity=0.85,
                        text=[f"{p}%" for p in pcts],
                        textposition="outside",
                        textfont=dict(size=10, color=FONT_COL),
                    ))
                all_vals_ph = [pdata[(pdata["Game Phase"] == ph) &
                                      pdata[col_name].notna() &
                                      pdata[col_name].astype(str).str.strip().ne("")].shape[0]
                               for pdata in [p1, p2]
                               for ph in sorted(strokes["Game Phase"].dropna().unique())]
                max_val_ph = max(all_vals_ph, default=1)
                fig_ph.update_layout(**BASE_LAYOUT, barmode="group", height=300,
                    title=dict(text=f"{label} por iniciativa", font=dict(size=12, color=FONT_COL), x=0),
                    xaxis=ax(), yaxis=dict(**ax("Nº golpes"), range=[0, max_val_ph * 1.3]),
                    uniformtext_minsize=8, uniformtext_mode="hide")
                st.plotly_chart(fig_ph, use_container_width=True)
else:
    st.info("No se encontraron columnas 'Barrido Fuerte' o 'Reves'.")
