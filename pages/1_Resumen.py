"""
pages/1_Resumen.py  ·  Resumen del partido
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_df, preprocess, STYLES, sidebar_logo, PLAYER_COLORS

st.set_page_config(page_title="Resumen · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

# ── Datos ────────────────────────────────
df = get_df()
strokes, rally_rows, rest_rows, player1, player2 = preprocess(df)

tournament = str(df["Tournament"].dropna().iloc[0]) if "Tournament" in df.columns else ""
wr1 = pd.to_numeric(df["WR Player1"].dropna().iloc[0], errors="coerce") if "WR Player1" in df.columns else None
wr2 = pd.to_numeric(df["WR Player2"].dropna().iloc[0], errors="coerce") if "WR Player2" in df.columns else None

n_rallies = int(strokes["rally_id"].nunique()) if "rally_id" in strokes.columns else int(strokes["Rally"].nunique()) if "Rally" in strokes.columns else 0
n_sets    = int(strokes["Set"].nunique())   if "Set"   in strokes.columns else 1

dur_total_ms  = df["Duración"].dropna().max() if "Duración" in df.columns else None
dur_total_str_short = (
    f"{int(dur_total_ms // 60000)}:{int((dur_total_ms % 60000) // 1000):02d} min"
    if pd.notna(dur_total_ms) else "—"
)

# Duración por set: max(Posición) - min(Posición) de los golpes del set
# Posición es timestamp absoluto en ms desde inicio del partido
def set_duration_str(s):
    # Inicio: Posición del primer golpe del rally 1 de este set
    if "Posición" not in strokes.columns or "Rally" not in strokes.columns:
        return "—"
    s_strokes = strokes[strokes["Set"] == s].copy()
    first_rally = s_strokes[s_strokes["Rally"] == 1]["Posición"]
    first_rally = pd.to_numeric(first_rally, errors="coerce").dropna()
    if first_rally.empty:
        return "—"
    start_ms = first_rally.min()

    # Fin: Posición del último Rest Time de este set
    if "Posición" not in rest_rows.columns or "Set" not in rest_rows.columns:
        return "—"
    s_rest = rest_rows[pd.to_numeric(rest_rows["Set"], errors="coerce") == s]
    s_rest_pos = pd.to_numeric(s_rest["Posición"], errors="coerce").dropna()
    if s_rest_pos.empty:
        return "—"
    end_ms = s_rest_pos.max()

    dur_ms = end_ms - start_ms
    return f"{int(dur_ms // 60000)}:{int((dur_ms % 60000) // 1000):02d} min"

strokes_per_rally = (strokes.groupby("rally_id")["Stroke"].max().reset_index()
                     if "rally_id" in strokes.columns and "Stroke" in strokes.columns
                     else pd.DataFrame())

rally_dur_s = (rally_rows["Duración"] / 1000).dropna() if "Duración" in rally_rows.columns else pd.Series(dtype=float)
rest_dur_s  = (rest_rows["Duración"]  / 1000).dropna() if "Duración" in rest_rows.columns  else pd.Series(dtype=float)

# Marcador: calcular puntos por set de forma independiente
outcome_col = "Rally Outcome"
score_rows = []
set_scores = {}

if outcome_col in strokes.columns:
    last_stroke = (strokes.sort_values("Stroke")
                   .groupby("rally_id").last().reset_index())
    # Ordenar por set y rally
    last_stroke["_set"] = pd.to_numeric(last_stroke.get("Set", 1), errors="coerce").fillna(1).astype(int)
    last_stroke["_rally"] = last_stroke["rally_id"].apply(
        lambda x: int(float(x.split("_")[1])) if "_" in str(x) else 0)
    last_stroke = last_stroke.sort_values(["_set", "_rally"]).reset_index(drop=True)

    # Acumular puntos reseteando por set
    prev_set = None
    sp1, sp2 = 0, 0
    for _, row in last_stroke.iterrows():
        s = int(row["_set"])
        if s != prev_set:
            sp1, sp2 = 0, 0
            prev_set = s
        outcome = str(row.get(outcome_col, ""))
        if f"Error {player2}" in outcome or (player1 in outcome and "Error" not in outcome and "Unforced" not in outcome):
            sp1 += 1
        elif f"Error {player1}" in outcome or (player2 in outcome and "Error" not in outcome and "Unforced" not in outcome):
            sp2 += 1
        elif f"Unforced {player1}" in outcome:
            sp2 += 1
        elif f"Unforced {player2}" in outcome:
            sp1 += 1
        score_rows.append({"rally": row["_rally"], "set": s,
                           "score_p1": sp1, "score_p2": sp2})

score_df = pd.DataFrame(score_rows)
if not score_df.empty:
    for s, g in score_df.groupby("set"):
        set_scores[s] = (int(g["score_p1"].iloc[-1]), int(g["score_p2"].iloc[-1]))

# ── Encabezado ───────────────────────────
import streamlit.components.v1 as components

wr1_str = f"Ranking mundial · #{int(wr1)}" if pd.notna(wr1) else "Ranking no disponible"
wr2_str = f"Ranking mundial · #{int(wr2)}" if pd.notna(wr2) else "Ranking no disponible"

components.html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;700&display=swap');
  .header {{
    background: linear-gradient(135deg, #1a1f2e, #0f1117);
    border: 1px solid #2a2d3a;
    border-radius: 20px;
    padding: 36px 44px;
    font-family: 'DM Sans', sans-serif;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 32px;
    align-items: center;
  }}
  .tag {{
    grid-column: 1 / -1;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 8px;
  }}
  .label {{
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: #4b5563;
    margin-bottom: 8px;
  }}
  .player-name {{
    font-size: 30px;
    font-weight: 700;
    color: #f9fafb;
    line-height: 1.2;
  }}
  .ranking {{
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: #6b7280;
    margin-top: 10px;
  }}
  .vs {{
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: #4b5563;
    text-align: center;
  }}
</style>
<div class="header">
  <div class="tag">🏸 &nbsp;Torneo &nbsp;·&nbsp; {tournament}</div>
  <div>
    <div class="label">Jugadora 1</div>
    <div class="player-name">{player1}</div>
    <div class="ranking">{wr1_str}</div>
  </div>
  <div class="vs">vs</div>
  <div>
    <div class="label">Jugadora 2</div>
    <div class="player-name">{player2}</div>
    <div class="ranking">{wr2_str}</div>
  </div>
</div>
""", height=260)

# ── Métricas globales ────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Métricas del partido</div>', unsafe_allow_html=True)

cols = st.columns(5)
metrics = [
    ("Sets",          str(n_sets),    ""),
    ("Rallies",       str(n_rallies), ""),
    ("Duración",      dur_total_str_short, ""),
    ("Golpes / rally",
     f"{strokes_per_rally['Stroke'].mean():.1f}" if not strokes_per_rally.empty else "—",
     f"máx {int(strokes_per_rally['Stroke'].max())}" if not strokes_per_rally.empty else ""),
    ("T. medio rally",
     f"{rally_dur_s.mean():.1f}s" if not rally_dur_s.empty else "—",
     f"máx {rally_dur_s.max():.1f}s" if not rally_dur_s.empty else ""),
]
for col, (label, value, sub) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          {'<div class="metric-sub">' + sub + '</div>' if sub else ''}
        </div>""", unsafe_allow_html=True)

# ── Métricas por set ─────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Métricas por set</div>', unsafe_allow_html=True)

sets_list = sorted(strokes["Set"].dropna().unique().astype(int)) if "Set" in strokes.columns else []

if sets_list:
    set_cols = st.columns(len(sets_list))
    for col, s in zip(set_cols, sets_list):
        s_strokes = strokes[strokes["Set"] == s]
        s_rallies = s_strokes["rally_id"].nunique() if "rally_id" in s_strokes.columns else 0

        s_rally_rows = rally_rows[rally_rows["Set"] == s] if "Set" in rally_rows.columns else pd.DataFrame()
        s_dur_s = (s_rally_rows["Duración"] / 1000).dropna() if "Duración" in s_rally_rows.columns else pd.Series(dtype=float)

        s_dur_str = set_duration_str(s)

        s_per_rally = s_strokes.groupby("rally_id")["Stroke"].max() if "rally_id" in s_strokes.columns else pd.Series(dtype=float)
        s_golpes_mean = f"{s_per_rally.mean():.1f}" if not s_per_rally.empty else "—"
        s_golpes_max  = f"máx {int(s_per_rally.max())}" if not s_per_rally.empty else ""

        # Tiempo medio de rally del set usando filas Rally Time
        s_rally_rows = rally_rows[pd.to_numeric(rally_rows.get("Set", pd.Series()), errors="coerce") == s] if "Set" in rally_rows.columns else pd.DataFrame()
        s_dur_s = (s_rally_rows["Duración"] / 1000).dropna() if "Duración" in s_rally_rows.columns else pd.Series(dtype=float)
        s_rally_mean = f"{s_dur_s.mean():.1f}s" if not s_dur_s.empty else "—"
        s_rally_max  = f"máx {s_dur_s.max():.1f}s" if not s_dur_s.empty else ""

        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label" style="font-size:13px;color:#60a5fa;margin-bottom:12px;">Set {s}</div>
              <div style="display:flex;flex-direction:column;gap:10px;">
                <div>
                  <div class="metric-label">Rallies</div>
                  <div class="metric-value" style="font-size:24px;">{s_rallies}</div>
                </div>
                <div>
                  <div class="metric-label">Duración</div>
                  <div class="metric-value" style="font-size:24px;">{s_dur_str}</div>
                </div>
                <div>
                  <div class="metric-label">Golpes / rally</div>
                  <div class="metric-value" style="font-size:24px;">{s_golpes_mean}</div>
                  {'<div class="metric-sub">' + s_golpes_max + '</div>' if s_golpes_max else ''}
                </div>
                <div>
                  <div class="metric-label">T. medio rally</div>
                  <div class="metric-value" style="font-size:24px;">{s_rally_mean}</div>
                  {'<div class="metric-sub">' + s_rally_max + '</div>' if s_rally_max else ''}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

# ── Marcador por set ─────────────────────
if set_scores:
    st.markdown('<div class="section-title" style="font-size:14px;">Marcador por set</div>', unsafe_allow_html=True)
    header = st.columns([2, 1, 1])
    header[1].markdown(f"<div style='text-align:center;font-size:12px;color:#9ca3af;font-family:DM Mono,monospace;'>{player1.split()[0]}</div>", unsafe_allow_html=True)
    header[2].markdown(f"<div style='text-align:center;font-size:12px;color:#9ca3af;font-family:DM Mono,monospace;'>{player2.split()[0]}</div>", unsafe_allow_html=True)

    p1_sets_won = sum(1 for s1, s2 in set_scores.values() if s1 > s2)
    p2_sets_won = sum(1 for s1, s2 in set_scores.values() if s2 > s1)

    for set_num, (s1, s2) in sorted(set_scores.items()):
        row = st.columns([2, 1, 1])
        row[0].markdown(f"<div style='font-size:13px;color:#6b7280;font-family:DM Mono,monospace;padding:6px 0;'>Set {set_num}</div>", unsafe_allow_html=True)
        c1 = "#4ade80" if s1 > s2 else "#374151"
        c2 = "#4ade80" if s2 > s1 else "#374151"
        row[1].markdown(f"<div style='text-align:center;font-size:24px;font-weight:600;color:{c1};'>{s1}</div>", unsafe_allow_html=True)
        row[2].markdown(f"<div style='text-align:center;font-size:24px;font-weight:600;color:{c2};'>{s2}</div>", unsafe_allow_html=True)

    row = st.columns([2, 1, 1])
    row[0].markdown("<div style='font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#6b7280;font-family:DM Mono,monospace;padding-top:8px;border-top:1px solid #1f2937;'>Sets ganados</div>", unsafe_allow_html=True)
    row[1].markdown(f"<div style='text-align:center;font-size:20px;font-weight:600;color:#facc15;padding-top:8px;border-top:1px solid #1f2937;'>{p1_sets_won}</div>", unsafe_allow_html=True)
    row[2].markdown(f"<div style='text-align:center;font-size:20px;font-weight:600;color:#facc15;padding-top:8px;border-top:1px solid #1f2937;'>{p2_sets_won}</div>", unsafe_allow_html=True)

# ── Momentum ─────────────────────────────
if not score_df.empty:
    st.markdown('<div class="section-title" style="font-size:14px;">Evolución del marcador (momentum)</div>', unsafe_allow_html=True)
    score_df["diff"] = score_df["score_p1"] - score_df["score_p2"]
    sets_list = sorted(score_df["set"].unique())
    set_colors = ["#60a5fa", "#f472b6", "#4ade80"]
    fig_mom = go.Figure()

    for i, s in enumerate(sets_list):
        sg = score_df[score_df["set"] == s].copy()
        color = set_colors[i % len(set_colors)]
        color_pos = color.replace(")", ", 0.15)").replace("rgb", "rgba") if "rgb" in color else f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)"
        # área positiva
        fig_mom.add_trace(go.Scatter(
            x=sg["rally"], y=sg["diff"].clip(lower=0),
            fill="tozeroy", mode="none",
            fillcolor=color_pos, showlegend=False,
        ))
        # área negativa
        fig_mom.add_trace(go.Scatter(
            x=sg["rally"], y=sg["diff"].clip(upper=0),
            fill="tozeroy", mode="none",
            fillcolor="rgba(248,113,113,0.12)", showlegend=False,
        ))
        # línea
        fig_mom.add_trace(go.Scatter(
            x=sg["rally"], y=sg["diff"],
            mode="lines", line=dict(color=color, width=2),
            name=f"Set {s}",
            hovertemplate=f"Set {s} · Rally %{{x}}<br>Diferencia: %{{y}}<extra></extra>",
        ))

    fig_mom.add_hline(y=0, line=dict(color="#374151", width=1, dash="dot"))
    max_diff = score_df["diff"].abs().max() or 1
    for i, s in enumerate(sets_list[1:], 1):
        fig_mom.add_vline(
            x=score_df[score_df["set"] == s]["rally"].iloc[0] - 0.5,
            line=dict(color="#374151", width=1, dash="dash"))

    # Etiquetas de jugadoras en el eje Y
    fig_mom.add_annotation(
        x=1, xref="paper", y=max_diff * 0.75,
        text=f"▲ {player1.split()[0]}", showarrow=False,
        font=dict(size=11, color="#4ade80"), xanchor="right",
    )
    fig_mom.add_annotation(
        x=1, xref="paper", y=-max_diff * 0.75,
        text=f"▼ {player2.split()[0]}", showarrow=False,
        font=dict(size=11, color="#f87171"), xanchor="right",
    )

    fig_mom.update_layout(
        height=280, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#f9fafb")),
        xaxis=dict(title="Rally (dentro del set)", tickfont=dict(size=10, color="#6b7280"), gridcolor="#1f2937"),
        yaxis=dict(title="Diferencia de puntos", tickfont=dict(size=10, color="#6b7280"),
                   gridcolor="#1f2937", zeroline=False),
        font=dict(family="DM Sans, sans-serif", color="#9ca3af"),
    )
    st.plotly_chart(fig_mom, use_container_width=True)

# ── Tiempos ──────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Tiempos de rally vs descanso</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2)

with col_a:
    if not rally_dur_s.empty:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=rally_dur_s, nbinsx=20,
            marker_color="#60a5fa", marker_line_color="#1d4ed8",
            marker_line_width=0.5, opacity=0.85))
        fig_hist.add_vline(x=rally_dur_s.mean(), line=dict(color="#facc15", width=1.5, dash="dot"))
        fig_hist.add_annotation(x=rally_dur_s.mean(), y=0, yref="paper", yanchor="bottom",
            text=f"media {rally_dur_s.mean():.1f}s", showarrow=False,
            font=dict(size=10, color="#facc15"), xanchor="left", yshift=4)
        fig_hist.update_layout(title=dict(text="Duración de rallies (s)", font=dict(size=13, color="#9ca3af"), x=0),
            height=340, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            margin=dict(l=40, r=20, t=40, b=40), bargap=0.05, showlegend=False,
            xaxis=dict(title="Segundos", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
            yaxis=dict(title="Nº rallies", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
            font=dict(family="DM Sans, sans-serif", color="#9ca3af"))
        st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    if not rally_dur_s.empty or not rest_dur_s.empty:
        fig_box = go.Figure()
        if not rally_dur_s.empty:
            fig_box.add_trace(go.Box(y=rally_dur_s, name="Rally", marker_color="#60a5fa",
                boxmean=True, line_width=1.5))
        if not rest_dur_s.empty:
            fig_box.add_trace(go.Box(y=rest_dur_s, name="Descanso", marker_color="#a78bfa",
                boxmean=True, line_width=1.5))
        fig_box.update_layout(title=dict(text="Rally vs descanso (s)", font=dict(size=13, color="#9ca3af"), x=0),
            height=340, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            margin=dict(l=40, r=20, t=40, b=40), showlegend=False,
            yaxis=dict(title="Segundos", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
            xaxis=dict(tickfont=dict(size=12, color="#9ca3af")),
            font=dict(family="DM Sans, sans-serif", color="#9ca3af"))
        st.plotly_chart(fig_box, use_container_width=True)


# ── Descanso previo vs resultado ─────────
st.markdown('<div class="section-title" style="font-size:14px;">Tiempo de descanso previo vs resultado del punto</div>', unsafe_allow_html=True)

# Construir tabla: para cada rally, descanso previo + quién ganó
if "rally_id" in strokes.columns and "Rally Outcome" in strokes.columns and not rest_rows.empty:
    # Último golpe de cada rally → resultado
    last_per_rally = (strokes.sort_values("Stroke")
                      .groupby("rally_id").last().reset_index())
    last_per_rally["_set"] = pd.to_numeric(last_per_rally.get("Set", 1), errors="coerce").fillna(1).astype(int)
    last_per_rally["_rally"] = last_per_rally["rally_id"].apply(
        lambda x: int(float(x.split("_")[1])) if "_" in str(x) else 0)

    def get_winner(outcome):
        o = str(outcome)
        if f"Error {player2}" in o or (player1 in o and "Error" not in o and "Unforced" not in o):
            return player1.split()[0]
        elif f"Error {player1}" in o or (player2 in o and "Error" not in o and "Unforced" not in o):
            return player2.split()[0]
        elif f"Unforced {player1}" in o:
            return player2.split()[0]
        elif f"Unforced {player2}" in o:
            return player1.split()[0]
        return None

    last_per_rally["ganador"] = last_per_rally["Rally Outcome"].apply(get_winner)

    # Descanso previo: Rest Time del rally anterior (mismo set)
    rest_map = {}
    if "Duración" in rest_rows.columns and "Rally" in rest_rows.columns and "Set" in rest_rows.columns:
        for _, row in rest_rows.iterrows():
            s = pd.to_numeric(row.get("Set"), errors="coerce")
            r = pd.to_numeric(row.get("Rally"), errors="coerce")
            d = pd.to_numeric(row.get("Duración"), errors="coerce")
            if pd.notna(s) and pd.notna(r) and pd.notna(d):
                # El descanso tras el rally r del set s precede al rally r+1
                next_rid = f"{int(s)}_{int(r)+1}"
                rest_map[next_rid] = d / 1000

    last_per_rally["descanso_previo_s"] = last_per_rally["rally_id"].map(rest_map)
    rally_outcome_df = last_per_rally[
        last_per_rally["ganador"].notna() & last_per_rally["descanso_previo_s"].notna()
    ].copy()

    if not rally_outcome_df.empty:
        fig_rest = go.Figure()
        for player, color in [(player1.split()[0], PLAYER_COLORS[0]),
                              (player2.split()[0], PLAYER_COLORS[1])]:
            sub = rally_outcome_df[rally_outcome_df["ganador"] == player]["descanso_previo_s"]
            fig_rest.add_trace(go.Box(
                y=sub, name=f"{player} gana",
                marker_color=color, boxmean=True, line_width=1.5,
                hovertemplate=f"<b>{player} gana</b><br>Descanso: %{{y:.1f}}s<extra></extra>",
            ))
        fig_rest.update_layout(
            title=dict(text="Distribución del descanso previo según quién gana el punto",
                       font=dict(size=13, color="#9ca3af"), x=0),
            height=360, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            margin=dict(l=40, r=20, t=48, b=40), showlegend=True,
            legend=dict(orientation="h", y=-0.12, font=dict(size=11, color="#f9fafb")),
            yaxis=dict(title="Descanso previo (s)", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
            xaxis=dict(tickfont=dict(size=12, color="#9ca3af")),
            font=dict(family="DM Sans, sans-serif", color="#9ca3af"),
        )
        st.plotly_chart(fig_rest, use_container_width=True)
    else:
        st.info("No hay suficientes datos para construir este gráfico.")
else:
    st.info("Faltan columnas necesarias (Rally Outcome o datos de descanso).")


# ── Duración del rally vs tipo de victoria ─
st.markdown('<div class="section-title" style="font-size:14px;">Duración del rally vs tipo de victoria</div>', unsafe_allow_html=True)

if "rally_id" in strokes.columns and "Rally Outcome" in strokes.columns and "Duración" in rally_rows.columns:
    last_per_rally2 = (strokes.sort_values("Stroke")
                       .groupby("rally_id").last().reset_index())
    last_per_rally2["ganador"] = last_per_rally2["Rally Outcome"].apply(get_winner)

    # Duración del rally en segundos
    dur_rally_map = (rally_rows.groupby("rally_id")["Duración"].first() / 1000
                     if "rally_id" in rally_rows.columns else pd.Series())
    last_per_rally2["dur_rally_s"] = last_per_rally2["rally_id"].map(dur_rally_map)

    rally_dur_df = last_per_rally2[
        last_per_rally2["ganador"].notna() & last_per_rally2["dur_rally_s"].notna()
    ].copy()

    if not rally_dur_df.empty:
        col_bp, col_vp = st.columns(2)

        # Box plot
        with col_bp:
            fig_bp = go.Figure()
            for player, color in [(player1.split()[0], PLAYER_COLORS[0]),
                                  (player2.split()[0], PLAYER_COLORS[1])]:
                sub = rally_dur_df[rally_dur_df["ganador"] == player]["dur_rally_s"]
                fig_bp.add_trace(go.Box(
                    y=sub, name=f"{player} gana",
                    marker_color=color, boxmean=True, line_width=1.5,
                    hovertemplate=f"<b>{player} gana</b><br>Rally: %{{y:.1f}}s<extra></extra>",
                ))
            fig_bp.update_layout(
                title=dict(text="Box plot · duración rally por ganador",
                           font=dict(size=13, color="#9ca3af"), x=0),
                height=360, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                margin=dict(l=40, r=20, t=48, b=40), showlegend=True,
                legend=dict(orientation="h", y=-0.12, font=dict(size=11, color="#f9fafb")),
                yaxis=dict(title="Duración rally (s)", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
                xaxis=dict(tickfont=dict(size=12, color="#9ca3af")),
                font=dict(family="DM Sans, sans-serif", color="#9ca3af"),
            )
            st.plotly_chart(fig_bp, use_container_width=True)

        # Violin plot
        with col_vp:
            fig_vp = go.Figure()
            for player, color in [(player1.split()[0], PLAYER_COLORS[0]),
                                  (player2.split()[0], PLAYER_COLORS[1])]:
                sub = rally_dur_df[rally_dur_df["ganador"] == player]["dur_rally_s"]
                fig_vp.add_trace(go.Violin(
                    y=sub, name=f"{player} gana",
                    line_color=color, fillcolor=color.replace(")", ", 0.2)").replace("rgb", "rgba") if "rgb" in color else color,
                    opacity=0.7, meanline_visible=True, box_visible=True,
                    hovertemplate=f"<b>{player} gana</b><br>Rally: %{{y:.1f}}s<extra></extra>",
                ))
            fig_vp.update_layout(
                title=dict(text="Violin plot · duración rally por ganador",
                           font=dict(size=13, color="#9ca3af"), x=0),
                height=360, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                margin=dict(l=40, r=20, t=48, b=40), showlegend=True,
                legend=dict(orientation="h", y=-0.12, font=dict(size=11, color="#f9fafb")),
                yaxis=dict(title="Duración rally (s)", tickfont=dict(size=11, color="#6b7280"), gridcolor="#1f2937"),
                xaxis=dict(tickfont=dict(size=12, color="#9ca3af")),
                font=dict(family="DM Sans, sans-serif", color="#9ca3af"),
            )
            st.plotly_chart(fig_vp, use_container_width=True)
    else:
        st.info("No hay suficientes datos para construir este gráfico.")
else:
    st.info("Faltan columnas necesarias para el gráfico de duración vs victoria.")
