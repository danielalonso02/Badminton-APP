"""
pages/5_Detalle_rally.py  ·  Detalle de un rally
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (get_df, preprocess, STYLES, PLAYER_COLORS, sidebar_logo,
                   base_court_fig, add_net_label, ZONE_COORDS_OWN, court_shapes)

st.set_page_config(page_title="Detalle rally · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

DARK_BG  = "#0f1117"
GRID_COL = "#1f2937"
FONT_COL = "#9ca3af"
BASE_LAYOUT = dict(
    paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
    font=dict(family="DM Sans, sans-serif", color=FONT_COL),
    margin=dict(l=40, r=20, t=48, b=40),
)

# ── Funciones helper para rotación ──
def swap_xy(x, y):
    return y, x

def rotate_shapes(shapes):
    rotated = []
    for s in shapes:
        s2 = s.copy()
        if all(k in s2 for k in ["x0", "y0", "x1", "y1"]):
            s2["x0"], s2["y0"] = s2["y0"], s2["x0"]
            s2["x1"], s2["y1"] = s2["y1"], s2["x1"]
        rotated.append(s2)
    return rotated

def base_court_fig_horizontal(title=""):
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=14, color="#f9fafb")),
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        # Rango invertido para vista horizontal: X es largo (0-1), Y es ancho (0-3)
        xaxis=dict(range=[-0.05, 1.05], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(range=[-0.05, 3.05], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        shapes=rotate_shapes(court_shapes()),
        showlegend=True,
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=11, color="#f9fafb"))
    )
    return fig

# ── Datos ────────────────────────────────
df = get_df()
strokes, rally_rows, _, player1, player2 = preprocess(df)
jugador_col = "Jugador del golpeo"

# Parseo de coordenadas XY
def parse_xy(nombre):
    try:
        coords = str(nombre).split("(")[0].strip()
        x, y = coords.split(";")
        return float(x), float(y)
    except Exception:
        return None, None

strokes[["coord_x", "coord_y"]] = strokes["Nombre"].apply(lambda n: pd.Series(parse_xy(n)))

def normalize_xy(df_in):
    out = df_in.copy()
    X_HALF, Y_HALF = 22.0, 68.0
    out["nx"] = (out["coord_x"] + X_HALF) / (2 * X_HALF) * 3.0
    out["ny"] = (out["coord_y"] + Y_HALF) / (2 * Y_HALF)
    out["nx"] = out["nx"].clip(0.0, 3.0)
    out["ny"] = out["ny"].clip(0.0, 1.0)
    return out

strokes = normalize_xy(strokes)

# Identificador único Set_Rally
if "rally_id" in strokes.columns:
    rallies_available = sorted(strokes["rally_id"].dropna().unique().tolist(),
                               key=lambda x: (int(x.split("_")[0]), int(float(x.split("_")[1]))))
else:
    rallies_available = []

dur_map = (rally_rows.groupby("rally_id")["Duración"].first() / 1000) \
    if "Duración" in rally_rows.columns and "rally_id" in rally_rows.columns \
    else pd.Series(dtype=float)


# ─────────────────────────────────────────
# SELECTOR DE RALLY
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Buscar rally</div>', unsafe_allow_html=True)

if not rallies_available:
    st.warning("No se encontraron rallies en los datos.")
    st.stop()

if "rally_idx" not in st.session_state:
    st.session_state["rally_idx"] = 0

col_prev, col_sel, col_next, _ = st.columns([1, 4, 1, 4])
with col_prev:
    if st.button("←"):
        st.session_state["rally_idx"] = max(0, st.session_state["rally_idx"] - 1)
with col_next:
    if st.button("→"):
        st.session_state["rally_idx"] = min(len(rallies_available) - 1, st.session_state["rally_idx"] + 1)
with col_sel:
    selected_id = st.selectbox(
        "Rally", options=rallies_available,
        index=st.session_state["rally_idx"],
        format_func=lambda x: f"Set {x.split('_')[0]} · Rally {int(float(x.split('_')[1]))}",
        label_visibility="collapsed",
    )
    st.session_state["rally_idx"] = rallies_available.index(selected_id)

rally_id = selected_id
rally_strokes = strokes[strokes["rally_id"] == rally_id].sort_values("Stroke").reset_index(drop=True)


# ─────────────────────────────────────────
# ESTADÍSTICAS RÁPIDAS
# ─────────────────────────────────────────
n_golpes  = len(rally_strokes)
dur_s     = dur_map.get(rally_id, None)
dur_str   = f"{dur_s:.1f}s" if pd.notna(dur_s) else "—"
set_num   = rally_id.split("_")[0]
rally_num = int(float(rally_id.split("_")[1]))

# Ganador del rally
ganador = "—"
outcome = ""
if "Rally Outcome" in rally_strokes.columns:
    vals = rally_strokes["Rally Outcome"].dropna()
    if not vals.empty:
        outcome = str(vals.iloc[-1])
        if f"Error {player2}" in outcome or player1 in outcome:
            ganador = player1.split()[0]
        elif f"Error {player1}" in outcome or player2 in outcome:
            ganador = player2.split()[0]

ganador_color = PLAYER_COLORS[0] if ganador == player1.split()[0] else PLAYER_COLORS[1]

st.markdown(f"""
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px;">
  <div class="metric-card" style="flex:1;min-width:120px;">
    <div class="metric-label">Rally</div>
    <div class="metric-value">#{rally_num}</div>
    <div class="metric-sub">Set {set_num}</div>
  </div>
  <div class="metric-card" style="flex:1;min-width:120px;">
    <div class="metric-label">Golpes</div>
    <div class="metric-value">{n_golpes}</div>
  </div>
  <div class="metric-card" style="flex:1;min-width:120px;">
    <div class="metric-label">Duración</div>
    <div class="metric-value">{dur_str}</div>
  </div>
  <div class="metric-card" style="flex:1;min-width:160px;">
    <div class="metric-label">Ganador</div>
    <div class="metric-value" style="color:{ganador_color};font-size:20px;">{ganador}</div>
    <div class="metric-sub" style="color:#6b7280;font-size:10px;">{outcome[:60] if outcome else ''}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# TRAYECTORIA EN PISTA + GANTT
# ─────────────────────────────────────────
col_court, col_gantt = st.columns([1, 1])

# ── Trayectoria ──────────────────────────
with col_court:
    st.markdown('<div class="section-title" style="font-size:14px;">Trayectoria en pista</div>', unsafe_allow_html=True)

    fig_court = base_court_fig_horizontal("")
    
    xs_raw, ys_raw, colors_traj, labels = [], [], [], []

    for _, row in rally_strokes.iterrows():
        player = row.get(jugador_col, "")
        nx, ny = row.get("nx"), row.get("ny")
        zone = row.get("Zone")
        
        if pd.isna(nx) or pd.isna(ny):
            if pd.notna(zone) and int(zone) in ZONE_COORDS_OWN:
                nx, ny = ZONE_COORDS_OWN[int(zone)]
        
        if pd.notna(nx) and pd.notna(ny):
            xs_raw.append(float(nx))
            ys_raw.append(float(ny))
            colors_traj.append(PLAYER_COLORS[0] if player == player1 else PLAYER_COLORS[1])
            phase = row.get("Game Phase", "")
            labels.append(f"Golpe {int(row['Stroke']) if pd.notna(row.get('Stroke')) else '?'} · {str(player).split()[0]}<br>Fase: {phase}")

    if len(xs_raw) >= 1:
        # 1. Obtenemos las coordenadas giradas básicas
        xs_swapped, ys_swapped = zip(*[swap_xy(x, y) for x, y in zip(xs_raw, ys_raw)])
        
        # 2. Reflejamos el eje Y (ancho de la pista) para corregir el efecto espejo
        # Como el rango del ancho de la pista es de 0 a 3, reflejamos restando de 3.0
        xs_rot = xs_swapped # El largo (0-1) se mantiene
        ys_rot = [3.0 - y for y in ys_swapped] # Reflejamos el ancho

        # Línea de trayectoria
        fig_court.add_trace(go.Scatter(
            x=xs_rot, y=ys_rot, mode="lines",
            line=dict(color="rgba(255,255,255,0.25)", width=1.5, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))
        
        # Marcadores con número de golpe
        fig_court.add_trace(go.Scatter(
            x=xs_rot, y=ys_rot, mode="markers+text",
            marker=dict(size=13, color=colors_traj, line=dict(width=1.5, color="rgba(0,0,0,0.5)")),
            text=[str(i + 1) for i in range(len(xs_rot))],
            textfont=dict(size=8, color="white"),
            textposition="middle center",
            hovertext=labels,
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        ))
        
        # Flechas
        for i in range(len(xs_rot) - 1):
            fig_court.add_annotation(
                ax=xs_rot[i], ay=ys_rot[i], x=xs_rot[i + 1], y=ys_rot[i + 1],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1,
                arrowwidth=1.2, arrowcolor="rgba(255,255,255,0.45)",
            )
        
        # Leyenda manual para jugadores
        fig_court.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=PLAYER_COLORS[0]), name=player1.split()[0], showlegend=True))
        fig_court.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=PLAYER_COLORS[1]), name=player2.split()[0], showlegend=True))
    else:
        fig_court.add_annotation(x=0.5, y=1.5, text="Sin coordenadas", showarrow=False)

    st.plotly_chart(fig_court, use_container_width=True)

# ── Gantt de golpeos ─────────────────────
with col_gantt:
    st.markdown('<div class="section-title" style="font-size:14px;">Línea de tiempo de golpeos</div>', unsafe_allow_html=True)

    pos_col = "Posición"
    has_pos = pos_col in rally_strokes.columns and rally_strokes[pos_col].notna().any()

    if has_pos:
        rally_strokes[pos_col] = pd.to_numeric(rally_strokes[pos_col], errors="coerce")

    PHASE_COLORS = {
        "Construccion": "#3b82f6", "Construcción": "#3b82f6",
        "Attack": "#f87171", "Defence": "#facc15",
    }

    # Origen de tiempo: primer golpe del rally
    rally_start_ms = 0.0
    if has_pos:
        first_pos = pd.to_numeric(rally_strokes[pos_col], errors="coerce").dropna()
        rally_start_ms = float(first_pos.min()) if not first_pos.empty else 0.0

    fig_gantt = go.Figure()
    for i, row in rally_strokes.iterrows():
        player  = str(row.get(jugador_col, ""))
        stroke  = int(row["Stroke"]) if pd.notna(row.get("Stroke")) else i + 1
        phase   = str(row.get("Game Phase", ""))
        zone    = row.get("Zone", "")
        pos_abs = float(row[pos_col]) if has_pos and pd.notna(row.get(pos_col)) else None
        if pos_abs is not None:
            t_start = (pos_abs - rally_start_ms) / 1000
        else:
            t_start = stroke - 1
        t_end = t_start + 0.25

        color = PHASE_COLORS.get(phase, "#888780")
        is_p1 = player == player1
        label = f"G{stroke} · {player.split()[0]}<br>Fase: {phase} · Zona: {zone}"

        fig_gantt.add_trace(go.Scatter(
            x=[t_start, t_end, t_end, t_start, t_start],
            y=[stroke - 0.35, stroke - 0.35, stroke + 0.35, stroke + 0.35, stroke - 0.35],
            fill="toself",
            fillcolor=color,
            line=dict(width=0),
            mode="lines",
            opacity=0.9 if is_p1 else 0.55,
            name=phase,
            hovertext=label,
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        ))
        fig_gantt.add_annotation(
            x=(t_start + t_end) / 2, y=stroke,
            text=f"{stroke}",
            showarrow=False,
            font=dict(size=8, color="white"),
            xanchor="center", yanchor="middle",
        )

    # Leyenda manual de fases
    for phase, color in PHASE_COLORS.items():
        if phase in ["Construcción", "Construccion"]:
            label = "Construcción"
        else:
            label = phase
        if phase == "Construccion":
            continue
        fig_gantt.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color, symbol="square"),
            name=label, showlegend=True,
        ))

    # Separador P1 / P2
    p1_strokes_idx = rally_strokes[rally_strokes[jugador_col] == player1]["Stroke"].tolist()
    p2_strokes_idx = rally_strokes[rally_strokes[jugador_col] == player2]["Stroke"].tolist()

    x_label = rally_strokes[pos_col].max() / 1000 if has_pos else n_golpes
    for s in p1_strokes_idx:
        fig_gantt.add_annotation(x=0, y=s, text="●", showarrow=False,
            font=dict(size=6, color=PLAYER_COLORS[0]), xanchor="right", xshift=-4)
    for s in p2_strokes_idx:
        fig_gantt.add_annotation(x=0, y=s, text="●", showarrow=False,
            font=dict(size=6, color=PLAYER_COLORS[1]), xanchor="right", xshift=-4)

    x_title = "Tiempo (s)" if has_pos else "Secuencia"
    fig_gantt.update_layout(
        **BASE_LAYOUT,
        height=max(400, n_golpes * 22 + 60),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=1,
                    font=dict(size=10, color="#f9fafb")),
        title=dict(text="Golpes por orden" + (" y tiempo" if has_pos else ""),
                   font=dict(size=12, color=FONT_COL), x=0),
        xaxis=dict(title=x_title, tickfont=dict(size=10, color=FONT_COL),
                   gridcolor=GRID_COL),
        yaxis=dict(title="Nº golpe", tickfont=dict(size=10, color=FONT_COL),
                   autorange="reversed", dtick=1, gridcolor=GRID_COL),
    )
    st.plotly_chart(fig_gantt, use_container_width=True)


# ─────────────────────────────────────────
# TABLA DE GOLPES
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Tabla de golpes</div>', unsafe_allow_html=True)

cols_show = [c for c in [
    "Stroke", jugador_col, "Zone", "Game Phase",
    "Type of service", "Zona de C1", "Field Position",
    "Rally Outcome", "Barrido Fuerte", "Reves", "Tipo de recepcion",
] if c in rally_strokes.columns]

rename = {
    "Stroke": "Golpe", jugador_col: "Jugadora", "Zone": "Zona",
    "Game Phase": "Fase", "Type of service": "Servicio",
    "Zona de C1": "Zona saque", "Field Position": "Posición",
    "Rally Outcome": "Resultado", "Barrido Fuerte": "Barrido",
    "Reves": "Revés", "Tipo de recepcion": "Recepción",
}

table_df = rally_strokes[cols_show].rename(columns=rename).reset_index(drop=True)

def color_row(row):
    jugadora = row.get("Jugadora", "")
    if player1.split()[0] in str(jugadora):
        return [f"background-color: rgba(96,165,250,0.08)"] * len(row)
    return [f"background-color: rgba(244,114,182,0.08)"] * len(row)

st.dataframe(
    table_df.style.apply(color_row, axis=1),
    use_container_width=True,
    height=min(600, n_golpes * 36 + 40),
)
