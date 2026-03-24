import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Configuración de rutas (manteniendo tu estructura)
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (get_df, preprocess, STYLES, PLAYER_COLORS, sidebar_logo,
                   base_court_fig, zone_heatmap_fig, add_net_label,
                   court_shapes, ZONE_COORDS_OWN, ZONE_COORDS_OPP)

# ── Configuración de la página ─────────
st.set_page_config(page_title="Mapa de pista · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

# ── Datos ───────────────────────────────
df = get_df()
strokes, _, _, player1, player2 = preprocess(df)

# ── Parseo y Normalización ───────────
def parse_xy(nombre):
    try:
        coords = str(nombre).split("(")[0].strip()
        x, y = coords.split(";")
        return float(x), float(y)
    except Exception:
        return None, None

def normalize_xy(df_in):
    out = df_in.copy()
    X_HALF, Y_HALF = 22.0, 68.0
    out["nx"] = (out["coord_x"] + X_HALF) / (2 * X_HALF) * 3.0
    out["ny"] = (out["coord_y"] + Y_HALF) / (2 * Y_HALF)
    out["nx"] = out["nx"].clip(0.0, 3.0)
    out["ny"] = out["ny"].clip(0.0, 1.0)
    return out

# Procesamiento de coordenadas
strokes[["coord_x", "coord_y"]] = strokes["Nombre"].apply(lambda n: pd.Series(parse_xy(n)))
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

# NUEVA LÓGICA DE ESTABILIZACIÓN DE LADO PARA LOS DATAFRAMES FILTRADOS:
# Determinamos el lado "propio" deseado: Fitriani (p1) -> Izquierda (ny < 0.5) and Mutiara (p2) -> Derecha (ny > 0.5)

def stabilizar_lado_jugador(df_in, side_desired):
    out = df_in.copy()
    if side_desired == "left": # Queremos ny < 0.5 (lado cercano/izquierdo de la red)
        # Para los puntos que estén en ny > 0.5 (lado lejano/derecho), los volteamos
        mask_voltear = out["ny"] > 0.5
        out.loc[mask_voltear, "nx"] = 3.0 - out.loc[mask_voltear, "nx"]
        out.loc[mask_voltear, "ny"] = 1.0 - out.loc[mask_voltear, "ny"]
    elif side_desired == "right": # Queremos ny > 0.5 (lado lejano/derecho de la red)
        # Para los puntos que estén en ny < 0.5 (lado cercano/izquierdo), los volteamos
        mask_voltear = out["ny"] < 0.5
        out.loc[mask_voltear, "nx"] = 3.0 - out.loc[mask_voltear, "nx"]
        out.loc[mask_voltear, "ny"] = 1.0 - out.loc[mask_voltear, "ny"]
    return out

jugador_col = "Jugador del golpeo"
# Creamos los dataframes filtrados
p1_f = apply_filters(strokes[strokes[jugador_col] == player1]) if jugador_col in strokes.columns else strokes.iloc[0:0]
p2_f = apply_filters(strokes[strokes[jugador_col] == player2]) if jugador_col in strokes.columns else strokes.iloc[0:0]

# Estabilizamos los dataframes de jugador: p1 -> izquierda and p2 -> derecha
if not p1_f.empty:
    p1_f = stabilizar_lado_jugador(p1_f, "left")
if not p2_f.empty:
    p2_f = stabilizar_lado_jugador(p2_f, "right")

# ── Funciones helper de dibujo ─────────────
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
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        xaxis=dict(range=[-0.05, 1.05], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(range=[-0.05, 3.05], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        height=520,
        margin=dict(l=10, r=60, t=40, b=10),
        shapes=rotate_shapes(court_shapes()),
        showlegend=True,
        legend=dict(orientation="h", y=-0.04, font=dict(size=11, color="#f9fafb"))
    )
    return fig

# ── 1 · Heatmap ──────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Heatmap de zonas · posición de golpeo (campo propio)</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(zone_heatmap_fig(p1_f, player1, "blue"), use_container_width=True)
with col2:
    st.plotly_chart(zone_heatmap_fig(p2_f, player2, "pink"), use_container_width=True)

# ── 1b · Scatter horizontal ──────────────
st.markdown('<div class="section-title" style="font-size:14px;">Posición de golpeos sobre la pista (horizontal)</div>', unsafe_allow_html=True)

def full_court_scatter(p1_df, p2_df):
    fig = base_court_fig_horizontal("Scatter de golpes")

    for df_in, pname, color in [
        (p1_df, player1.split()[0], PLAYER_COLORS[0]),
        (p2_df, player2.split()[0], PLAYER_COLORS[1]),
    ]:
        if "nx" not in df_in.columns or df_in["nx"].notna().sum() == 0:
            continue
            
        valid = df_in[df_in["nx"].notna() & df_in["ny"].notna()].copy()
        
        raw_xs = valid["nx"].tolist()
        raw_ys = valid["ny"].tolist()
        phases = valid["Game Phase"].fillna("—").tolist() if "Game Phase" in valid.columns else ["—"]*len(raw_xs)

        # Invertimos X e Y para la vista horizontal (de ahí el swap_xy)
        xs_rot, ys_rot = zip(*[swap_xy(x, y) for x, y in zip(raw_xs, raw_ys)])

        fig.add_trace(go.Scatter(
            x=xs_rot, y=ys_rot, mode="markers",
            marker=dict(size=6, color=color, opacity=0.7,
                        line=dict(width=0.5, color="white")),
            name=pname,
            text=phases,
            hovertemplate=f"<b>{pname}</b><br>Fase: %{{text}}<extra></extra>"
        ))
    return fig

st.plotly_chart(full_court_scatter(p1_f, p2_f), use_container_width=True)

# ── 2 · Trayectorias horizontal ─────────
st.markdown('<div class="section-title" style="font-size:14px;">Trayectoria · secuencia de golpeos por rally (horizontal)</div>', unsafe_allow_html=True)

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
    
    rally_strokes = strokes[strokes["rally_id"] == rally_id].sort_values("Stroke")

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
        fig = base_court_fig_horizontal(f"Rally {rally_id}")
        xs, ys, colors_traj, labels = [], [], [], []

        for _, row in rally_df.iterrows():
            player = row.get(jugador_col, "")
            nx, ny = row.get("nx", None), row.get("ny", None)
            
            if pd.notna(nx) and pd.notna(ny):
                # NUEVA LÓGICA DE ESTABILIZACIÓN DE TRAYECTORIA:
                # Determinamos el lado "propio" deseado: p1 -> izquierda and p2 -> derecha
                if player == player1: # Es Fitriani
                    # Queremos ny < 0.5. Para los puntos en ny > 0.5, los volteamos.
                    if ny > 0.5:
                        nx = 3.0 - nx
                        ny = 1.0 - ny
                elif player == player2: # Es Mutiara
                    # Queremos ny > 0.5. Para los puntos en ny < 0.5, los volteamos.
                    if ny < 0.5:
                        nx = 3.0 - nx
                        ny = 1.0 - ny
                
                xs.append(nx)
                ys.append(ny)
                colors_traj.append(PLAYER_COLORS[0] if player == player1 else PLAYER_COLORS[1])
                stroke_n = row.get("Stroke", "?")
                phase = row.get("Game Phase", "")
                labels.append(f"Golpe {int(stroke_n) if pd.notna(stroke_n) else '?'} · {str(player).split()[0]}<br>Fase: {phase}")

        if len(xs) < 1:
            fig.add_annotation(x=0.5, y=1.5, text="Sin coordenadas", showarrow=False)
            add_net_label(fig)
            return fig

        
        xs_swapped, ys_swapped = zip(*[swap_xy(x, y) for x, y in zip(xs, ys)])
        
        # 2. Reflejamos el eje Y (ancho de la pista) para corregir el efecto espejo
        # Como el rango del ancho de la pista es de 0 a 3, reflejamos restando de 3.0
        xs_rot = xs_swapped # El largo (0-1) se mantiene
        ys_rot = [3.0 - y for y in ys_swapped] # Reflejamos el ancho

        # Líneas
        fig.add_trace(go.Scatter(x=xs_rot, y=ys_rot, mode="lines",
                                 line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dot"),
                                 showlegend=False, hoverinfo="skip"))

        # Puntos
        fig.add_trace(go.Scatter(x=xs_rot, y=ys_rot, mode="markers+text",
                                 marker=dict(size=14, color=colors_traj, line=dict(width=1.5, color="black")),
                                 text=[str(i+1) for i in range(len(xs_rot))],
                                 textfont=dict(size=9, color="white"),
                                 hovertext=labels, hovertemplate="%{hovertext}<extra></extra>",
                                 showlegend=False))

        # Flechas de dirección
        for i in range(len(xs_rot)-1):
            fig.add_annotation(ax=xs_rot[i], ay=ys_rot[i], x=xs_rot[i+1], y=ys_rot[i+1],
                               xref="x", yref="y", axref="x", ayref="y",
                               showarrow=True, arrowhead=2, arrowsize=1, arrowcolor="rgba(255,255,255,0.4)")

        add_net_label(fig)
        return fig

    st.plotly_chart(trajectory_fig(rally_strokes), use_container_width=True)

    with st.expander("Ver tabla de golpes"):
        st.dataframe(rally_strokes.reset_index(drop=True), use_container_width=True)