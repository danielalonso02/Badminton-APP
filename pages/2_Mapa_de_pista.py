"""
pages/2_Mapa_de_pista.py  ·  Heatmap de zonas y trayectorias
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (get_df, preprocess, STYLES, PLAYER_COLORS, sidebar_logo,
                   base_court_fig, zone_heatmap_fig, add_net_label,
                   court_shapes, ZONE_COORDS_OWN, ZONE_COORDS_OPP)

st.set_page_config(page_title="Mapa de pista · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

# ── Datos ────────────────────────────────
df = get_df()
strokes, _, _, player1, player2 = preprocess(df)

# ── Parseo de coordenadas XY ─────────────
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

# ── Filtros sidebar ──────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### Filtros")
    sets_available = sorted(strokes["Set"].dropna().unique().astype(int)) if "Set" in strokes.columns else []
    set_sel = st.selectbox("Set", ["Todos"] + [f"Set {s}" for s in sets_available])
    phase_options = ["Todas"] + (sorted(strokes["Game Phase"].dropna().unique().tolist()) if "Game Phase" in strokes.columns else [])
    phase_sel = st.selectbox("Fase de juego", phase_options)

def apply_filters(df_in):
    out = df_in.copy()
    if set_sel != "Todos" and "Set" in out.columns:
        out = out[out["Set"] == int(set_sel.replace("Set ", ""))]
    if phase_sel != "Todas" and "Game Phase" in out.columns:
        out = out[out["Game Phase"] == phase_sel]
    return out

jugador_col = "Jugador del golpeo"
p1_f = apply_filters(strokes[strokes[jugador_col] == player1]) if jugador_col in strokes.columns else strokes.iloc[0:0]
p2_f = apply_filters(strokes[strokes[jugador_col] == player2]) if jugador_col in strokes.columns else strokes.iloc[0:0]

# ── 1 · Heatmap ──────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Heatmap de zonas · posición de golpeo (campo propio)</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(zone_heatmap_fig(p1_f, player1, "blue"), use_container_width=True)
with col2:
    st.plotly_chart(zone_heatmap_fig(p2_f, player2, "pink"), use_container_width=True)


# ── 1b · Scatter posición de golpeos ─────
st.markdown('<div class="section-title" style="font-size:14px;">Posición de golpeos sobre la pista</div>', unsafe_allow_html=True)

def full_court_scatter(p1_df, p2_df):
    import random, numpy as np
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        height=520,
        margin=dict(l=10, r=60, t=36, b=10),
        xaxis=dict(range=[-0.05, 3.05], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True),
        yaxis=dict(range=[-0.05, 1.05], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True,
                   scaleanchor="x", scaleratio=6.59),
        shapes=court_shapes(),
        showlegend=True,
        legend=dict(orientation="h", y=-0.04, font=dict(size=11, color="#f9fafb")),
        title=dict(text="Cada círculo = un golpe",
                   font=dict(size=12, color="#9ca3af"), x=0),
    )

    rng = np.random.default_rng(42)

    # P1 siempre en mitad inferior (y=0..0.5), P2 siempre en superior (y=0.5..1)
    # Si las coordenadas reales están en la mitad equivocada, las reflejamos
    for df_in, pname, color, own_half in [
        (p1_df, player1.split()[0], PLAYER_COLORS[0], "bottom"),
        (p2_df, player2.split()[0], PLAYER_COLORS[1], "top"),
    ]:
        has_xy = "nx" in df_in.columns and df_in["nx"].notna().any()

        if has_xy:
            valid = df_in[df_in["nx"].notna() & df_in["ny"].notna()].copy()
            raw_xs = valid["nx"].tolist()
            raw_ys = valid["ny"].tolist()
            phases = valid["Game Phase"].fillna("—").tolist() if "Game Phase" in valid.columns else ["—"] * len(raw_xs)
            # Normalizar: P1 → mitad inferior (ny < 0.5), P2 → mitad superior (ny > 0.5)
            xs, ys = [], []
            for x, y in zip(raw_xs, raw_ys):
                if own_half == "bottom":
                    # Aseguramos que el punto esté en y < 0.5
                    ny = y if y < 0.5 else 1.0 - y
                else:
                    # Aseguramos que el punto esté en y > 0.5
                    ny = y if y >= 0.5 else 1.0 - y
                xs.append(x)
                ys.append(ny)
        elif "Zone" in df_in.columns:
            xs, ys, phases = [], [], []
            for _, row in df_in.iterrows():
                z = pd.to_numeric(row.get("Zone"), errors="coerce")
                if pd.notna(z) and int(z) in ZONE_COORDS_OWN:
                    cx, cy = ZONE_COORDS_OWN[int(z)]
                    base_y = float(cy)
                    if own_half == "top":
                        base_y = 1.0 - base_y
                    xs.append(float(cx) + rng.uniform(-0.08, 0.08))
                    ys.append(base_y + rng.uniform(-0.02, 0.02))
                    phases.append(str(row.get("Game Phase", "—")))
        else:
            continue

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(size=5, color=color, opacity=0.65,
                        line=dict(width=0.5, color="rgba(0,0,0,0.3)")),
            name=pname,
            text=phases,
            hovertemplate=f"<b>{pname}</b><br>Fase: %{{text}}<extra></extra>",
        ))

    fig.add_annotation(x=3.04, y=0.25, xref="x", yref="y", text="Propio",
                       showarrow=False, font=dict(size=9, color="rgba(255,255,255,0.45)", family="DM Mono"), xanchor="left")
    fig.add_annotation(x=3.04, y=0.75, xref="x", yref="y", text="Rival",
                       showarrow=False, font=dict(size=9, color="rgba(255,255,255,0.45)", family="DM Mono"), xanchor="left")
    fig.add_annotation(x=1.5, y=0.5, xref="x", yref="y", text="RED",
                       showarrow=False, font=dict(size=10, color="rgba(250,204,21,0.9)", family="DM Mono"))
    return fig

st.plotly_chart(full_court_scatter(p1_f, p2_f), use_container_width=True)

# ── 2 · Trayectorias ─────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Trayectoria · secuencia de golpeos por rally</div>', unsafe_allow_html=True)

if "rally_id" in strokes.columns:
    rallies_available = sorted(strokes["rally_id"].dropna().unique().tolist(),
                               key=lambda x: (int(x.split("_")[0]), int(float(x.split("_")[1]))))
else:
    rallies_available = []

if not rallies_available:
    st.info("No se encontró la columna 'Rally' en los datos.")
else:
    col_sel, col_info = st.columns([2, 3])
    with col_sel:
        rally_id = st.selectbox("Selecciona un rally", options=rallies_available,
                                format_func=lambda x: f"Set {x.split('_')[0]} · Rally {int(float(x.split('_')[1]))}")

    rally_strokes = apply_filters(strokes[strokes["rally_id"] == rally_id]).sort_values("Stroke")

    with col_info:
        n_strokes = len(rally_strokes)
        outcome = ""
        if "Rally Outcome" in rally_strokes.columns:
            vals = rally_strokes["Rally Outcome"].dropna()
            outcome = str(vals.iloc[-1]) if not vals.empty else ""
        st.markdown(f"""
        <div style="padding:10px 0;font-family:'DM Mono',monospace;font-size:12px;color:#9ca3af;">
          <span style="color:#f9fafb;font-size:18px;font-weight:600;">{n_strokes}</span> golpes
          {"&nbsp;·&nbsp;<span style='color:#facc15;'>" + outcome + "</span>" if outcome else ""}
        </div>""", unsafe_allow_html=True)

    def trajectory_fig(rally_df):
        fig = base_court_fig(f"Set {rally_id.split('_')[0]} · Rally {int(float(rally_id.split('_')[1]))} · trayectoria")
        fig.update_layout(showlegend=True,
                          legend=dict(orientation="h", y=-0.04, x=0,
                                      font=dict(size=11, color="#9ca3af")))
        xs, ys, colors_traj, labels = [], [], [], []

        for _, row in rally_df.iterrows():
            player  = row.get(jugador_col, "")
            nx = row.get("nx", None)
            ny = row.get("ny", None)
            zone = row.get("Zone", None)
            if pd.isna(nx) or pd.isna(ny):
                if pd.notna(zone) and int(zone) in ZONE_COORDS_OWN:
                    nx, ny = ZONE_COORDS_OWN[int(zone)]
            if pd.notna(nx) and pd.notna(ny):
                xs.append(float(nx))
                ys.append(float(ny))
                colors_traj.append(PLAYER_COLORS[0] if player == player1 else PLAYER_COLORS[1])
                stroke_n = row.get("Stroke", "?")
                phase    = row.get("Game Phase", "")
                labels.append(f"Golpe {int(stroke_n) if pd.notna(stroke_n) else '?'} · {str(player).split()[0]}<br>Fase: {phase}")

        if len(xs) < 2:
            fig.add_annotation(x=1.5, y=0.5, text="Sin coordenadas para este rally",
                               font=dict(color="white", size=12), showarrow=False)
            add_net_label(fig)
            return fig

        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines",
            line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dot"),
            showlegend=False, hoverinfo="skip"))

        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text",
            marker=dict(size=12, color=colors_traj, line=dict(width=1.5, color="rgba(0,0,0,0.5)")),
            text=[str(i+1) for i in range(len(xs))],
            textfont=dict(size=8, color="white"), textposition="middle center",
            hovertext=labels, hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False))

        for i in range(len(xs) - 1):
            fig.add_annotation(ax=xs[i], ay=ys[i], x=xs[i+1], y=ys[i+1],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.2,
                arrowcolor="rgba(255,255,255,0.5)")

        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=PLAYER_COLORS[0]), name=player1.split()[0], showlegend=True))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=PLAYER_COLORS[1]), name=player2.split()[0], showlegend=True))

        add_net_label(fig)
        return fig

    st.plotly_chart(trajectory_fig(rally_strokes), use_container_width=True)

    with st.expander("Ver golpes del rally"):
        cols_show = [c for c in ["Stroke", jugador_col, "Zone", "Game Phase",
                                  "Type of service", "Rally Outcome", "Barrido Fuerte", "Reves"]
                     if c in rally_strokes.columns]
        st.dataframe(rally_strokes[cols_show].reset_index(drop=True),
                     use_container_width=True, height=200)
