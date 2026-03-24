"""
utils.py  ·  Funciones y constantes compartidas entre páginas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ─────────────────────────────────────────
# ESTILOS GLOBALES
# ─────────────────────────────────────────
STYLES = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .section-title {
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6b7280;
    font-family: 'DM Mono', monospace;
    margin: 28px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1f2937;
  }
  .metric-card {
    background: #0f1117;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
  }
  .metric-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 6px;
    font-family: 'DM Mono', monospace;
  }
  .metric-value {
    font-size: 36px;
    font-weight: 600;
    color: #f9fafb;
    line-height: 1;
  }
  .metric-sub {
    font-size: 12px;
    color: #4ade80;
    margin-top: 4px;
    font-family: 'DM Mono', monospace;
  }
</style>
"""

PLAYER_COLORS = ["#60a5fa", "#f472b6"]

# ─────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────
def get_csv_files(folder: Path) -> list[Path]:
    return sorted(Path(folder).glob("*.csv"))


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python", encoding="latin1")
    df.columns = df.columns.str.strip()
    return df


def sidebar_logo():
    """Logo en sidebar usando st.logo() — nativo de Streamlit.
    Aparece en la parte superior del sidebar y en miniatura cuando está cerrado.
    """
    from pathlib import Path
    import sys
    # Buscar logo relativo al directorio del script principal
    candidates = [
        Path("imagenes/logo.png"),
        Path(__file__).parent / "imagenes" / "logo.png",
        Path(sys.argv[0]).parent / "imagenes" / "logo.png",
    ]
    for logo in candidates:
        if logo.exists():
            st.logo(str(logo.resolve()), size="large")
            return


def get_df() -> pd.DataFrame:
    """Carga el DataFrame del partido seleccionado en session_state."""
    path = st.session_state.get("selected_file")
    if not path:
        st.warning("Selecciona un partido en la página principal.")
        st.stop()
    return load_data(path)


def preprocess(df: pd.DataFrame):
    """
    Separa filas de rally/rest de los golpes reales.
    Devuelve (strokes, rally_rows, rest_rows, player1, player2).
    """
    is_rally = df["Nombre"].astype(str).str.startswith("Rally Time")
    is_rest  = df["Nombre"].astype(str).str.startswith("Rest Time")
    is_stroke = ~is_rally & ~is_rest & df["Nombre"].notna() & (df["Nombre"].astype(str).str.strip() != "")

    strokes = df[is_stroke].copy()
    rally_rows = df[is_rally].copy()
    rest_rows  = df[is_rest].copy()

    for col in ["Zone", "Rally", "Stroke", "Set"]:
        if col in strokes.columns:
            strokes[col] = pd.to_numeric(strokes[col], errors="coerce")
    for col in ["Duración", "Rally"]:
        for d in [rally_rows, rest_rows]:
            if col in d.columns:
                d[col] = pd.to_numeric(d[col], errors="coerce")

    # Identificador único de rally: "Set_Rally" para evitar colisiones entre sets
    for d in [strokes, rally_rows, rest_rows]:
        if "Set" in d.columns and "Rally" in d.columns:
            d["rally_id"] = (d["Set"].astype(str).str.strip()
                             + "_"
                             + d["Rally"].astype(str).str.strip())

    player1 = str(df["Player1"].dropna().iloc[0]).strip() if "Player1" in df.columns else "Jugadora 1"
    player2 = str(df["Player2"].dropna().iloc[0]).strip() if "Player2" in df.columns else "Jugadora 2"

    # Matching flexible por si hay diferencias de encoding
    jugador_col = "Jugador del golpeo"
    if jugador_col in strokes.columns:
        strokes[jugador_col] = strokes[jugador_col].astype(str).str.strip()
    unique_players = strokes[jugador_col].dropna().unique().tolist() if jugador_col in strokes.columns else []

    def find_player(target, candidates):
        for c in candidates:
            if target.lower() in c.lower() or c.lower() in target.lower():
                return c
        return target

    player1_col = find_player(player1, unique_players)
    player2_col = find_player(player2, unique_players)

    return strokes, rally_rows, rest_rows, player1_col, player2_col


# ─────────────────────────────────────────
# PISTA DE BÁDMINTON
# ─────────────────────────────────────────
# La pista tiene DOS mitades con zonas 1-12 cada una:
#   - Mitad PROPIA  (y=0..0.5): zonas 1-12 donde está el jugador (Zone)
#   - Mitad RIVAL   (y=0.5..1): zonas 1-12 espejadas donde cae el volante (Field Position)
#
# Layout de zonas en cada mitad (visto desde campo propio, abajo):
#   Fondo:  10 | 11 | 12       (más lejos de la red)
#   Medio:   4 |  5 |  6
#   Corto:   1 |  2 |  3       (más cerca de la red)
#
# En el campo rival las zonas están espejadas verticalmente:
#   Corto:   1 |  2 |  3       (más cerca de la red, en y=0.5..0.65)
#   Medio:   4 |  5 |  6
#   Fondo:  10 | 11 | 12       (más lejos, en y=0.85..1.0)

COURT_COLOR = "#1a6b3a"
LINE_COLOR  = "rgba(255,255,255,0.9)"

# Layout de zonas (visto desde campo propio, abajo):
#
# Campo RIVAL (arriba):   12 | 11 | 10 | 9
#                          8 |  7 |  6 | 5
#                          4 |  3 |  2 | 1
#                         ----  RED  ----
# Campo PROPIO (abajo):    1 |  2 |  3 | 4
#                          5 |  6 |  7 | 8
#                          9 | 10 | 11 | 12
#
# x: 0=izq, 3=dcha → 4 columnas de ancho 0.75 cada una
# y: 0=abajo(fondo propio), 1=arriba(fondo rival)
# Cada mitad ocupa y=0..0.5 (propio) y y=0.5..1 (rival)
# Cada mitad tiene 3 filas de y=0.167 cada una

# Campo PROPIO (abajo, y=0..0.5) — Zone
# Fila cerca de red (y=0.33..0.50): zonas 1,2,3,4  (izq→dcha)
# Fila media       (y=0.17..0.33): zonas 5,6,7,8
# Fila fondo       (y=0.00..0.17): zonas 9,10,11,12
ZONE_COORDS_OWN = {
     1: (0.375, 0.42),  2: (1.125, 0.42),  3: (1.875, 0.42),  4: (2.625, 0.42),
     5: (0.375, 0.25),  6: (1.125, 0.25),  7: (1.875, 0.25),  8: (2.625, 0.25),
     9: (0.375, 0.08), 10: (1.125, 0.08), 11: (1.875, 0.08), 12: (2.625, 0.08),
}

# Campo RIVAL (arriba, y=0.5..1) — Field Position (espejado)
# Fila cerca de red (y=0.50..0.67): zonas 1,2,3,4  (izq→dcha)
# Fila media        (y=0.67..0.83): zonas 5,6,7,8
# Fila fondo        (y=0.83..1.00): zonas 9,10,11,12 → espejadas: 12,11,10,9 (dcha→izq)
ZONE_COORDS_OPP = {
     1: (0.375, 0.58),  2: (1.125, 0.58),  3: (1.875, 0.58),  4: (2.625, 0.58),
     5: (0.375, 0.75),  6: (1.125, 0.75),  7: (1.875, 0.75),  8: (2.625, 0.75),
     9: (0.375, 0.92), 10: (1.125, 0.92), 11: (1.875, 0.92), 12: (2.625, 0.92),
}

# Bounds (x0,x1,y0,y1) — campo propio
ZONE_BOUNDS_OWN = {
     1: (0,   0.75, 0.33, 0.50),  2: (0.75, 1.50, 0.33, 0.50),
     3: (1.50,2.25, 0.33, 0.50),  4: (2.25, 3.00, 0.33, 0.50),
     5: (0,   0.75, 0.17, 0.33),  6: (0.75, 1.50, 0.17, 0.33),
     7: (1.50,2.25, 0.17, 0.33),  8: (2.25, 3.00, 0.17, 0.33),
     9: (0,   0.75, 0.00, 0.17), 10: (0.75, 1.50, 0.00, 0.17),
    11: (1.50,2.25, 0.00, 0.17), 12: (2.25, 3.00, 0.00, 0.17),
}

# Bounds — campo rival
ZONE_BOUNDS_OPP = {
     1: (0,   0.75, 0.50, 0.67),  2: (0.75, 1.50, 0.50, 0.67),
     3: (1.50,2.25, 0.50, 0.67),  4: (2.25, 3.00, 0.50, 0.67),
     5: (0,   0.75, 0.67, 0.83),  6: (0.75, 1.50, 0.67, 0.83),
     7: (1.50,2.25, 0.67, 0.83),  8: (2.25, 3.00, 0.67, 0.83),
     9: (0,   0.75, 0.83, 1.00), 10: (0.75, 1.50, 0.83, 1.00),
    11: (1.50,2.25, 0.83, 1.00), 12: (2.25, 3.00, 0.83, 1.00),
}

# Alias para compatibilidad con código anterior (usa campo propio por defecto)
ZONE_COORDS = ZONE_COORDS_OWN
ZONE_BOUNDS  = ZONE_BOUNDS_OWN


def court_shapes() -> list:
    def line(x0, y0, x1, y1, dash="solid", width=1.5):
        return dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color=LINE_COLOR, width=width, dash=dash),
                    xref="x", yref="y", layer="below")

    def rect(x0, y0, x1, y1, fill=COURT_COLOR, lw=0):
        return dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                    fillcolor=fill, line=dict(color=LINE_COLOR, width=lw),
                    xref="x", yref="y", layer="below")

    net = dict(type="line", x0=0, y0=0.5, x1=3, y1=0.5,
               line=dict(color="rgba(250,204,21,0.9)", width=3),
               xref="x", yref="y", layer="below")

    return [
        rect(0, 0, 3, 1),
        # Borde exterior
        line(0, 0, 3, 0), line(0, 1, 3, 1),
        line(0, 0, 0, 1), line(3, 0, 3, 1),
        # Campo PROPIO (abajo): 3 filas x 4 columnas
        line(0, 0.17, 3, 0.17, width=0.8),   # fondo / medio
        line(0, 0.33, 3, 0.33, width=0.8),   # medio / saque
        line(0.75, 0, 0.75, 0.5, width=0.8),
        line(1.50, 0, 1.50, 0.5, width=0.8),
        line(2.25, 0, 2.25, 0.5, width=0.8),
        # Campo RIVAL (arriba): 3 filas x 4 columnas (espejado)
        line(0, 0.67, 3, 0.67, width=0.8),   # saque / medio
        line(0, 0.83, 3, 0.83, width=0.8),   # medio / fondo
        line(0.75, 0.5, 0.75, 1, width=0.8),
        line(1.50, 0.5, 1.50, 1, width=0.8),
        line(2.25, 0.5, 2.25, 1, width=0.8),
        # RED — al final para quedar encima de las líneas
        net,
    ]


def zone_number_annotations() -> list:
    anns = []
    for z, (cx, cy) in ZONE_COORDS_OWN.items():
        anns.append(dict(x=cx, y=cy, xref="x", yref="y", text=str(z), showarrow=False,
                         font=dict(size=9, color="rgba(255,255,255,0.35)", family="DM Mono")))
    for z, (cx, cy) in ZONE_COORDS_OPP.items():
        anns.append(dict(x=cx, y=cy, xref="x", yref="y", text=str(z), showarrow=False,
                         font=dict(size=9, color="rgba(255,255,255,0.35)", family="DM Mono")))
    return anns


def base_court_fig(title: str = "", height: int = 400) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#9ca3af", family="DM Mono"), x=0),
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        margin=dict(l=10, r=10, t=36, b=10),
        height=height,
        xaxis=dict(range=[-0.05, 3.05], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True),
        yaxis=dict(range=[-0.05, 1.05], showgrid=False, zeroline=False,
                   showticklabels=False, fixedrange=True,
                   scaleanchor="x", scaleratio=6.59),
        shapes=court_shapes(),
        annotations=zone_number_annotations(),
        showlegend=False,
    )
    return fig


def add_net_label(fig: go.Figure):
    fig.add_annotation(x=1.5, y=0.5, xref="x", yref="y", text="RED",
                       showarrow=False,
                       font=dict(size=10, color="rgba(250,204,21,0.9)", family="DM Mono"))


def zone_heatmap_fig(strokes_df: pd.DataFrame, player_name: str, color_scale: str) -> go.Figure:
    # Heatmap solo del campo propio (Zone = posición del jugador que golpea)
    zone_counts = {}
    if "Zone" in strokes_df.columns:
        z_valid = pd.to_numeric(strokes_df["Zone"], errors="coerce").dropna()
        zone_counts = z_valid.value_counts().to_dict()

    max_count = max(zone_counts.values(), default=1)
    r, g, b = (96, 165, 250) if color_scale == "blue" else (244, 114, 182)

    # Pista solo con la mitad propia (y=0..0.5)
    fig = base_court_fig(player_name.split()[0] + " · posición de golpeo (Zone)", height=280)
    fig.update_layout(yaxis=dict(range=[-0.03, 0.53], showgrid=False,
                                  zeroline=False, showticklabels=False, fixedrange=True))

    for zone, (x0, x1, y0, y1) in ZONE_BOUNDS_OWN.items():
        count = int(zone_counts.get(zone, zone_counts.get(float(zone), 0)))
        alpha = 0.08 + 0.72 * (count / max_count) if count > 0 else 0.0
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=f"rgba({r},{g},{b},{alpha:.2f})",
                      line=dict(width=0), xref="x", yref="y", layer="above")
        if count > 0:
            fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, xref="x", yref="y",
                               text=str(count), showarrow=False,
                               font=dict(size=11, color="white", family="DM Mono"))

    # Zona de números
    for zone, (cx, cy) in ZONE_COORDS_OWN.items():
        fig.add_annotation(x=cx, y=cy, xref="x", yref="y", text=str(zone),
                           showarrow=False,
                           font=dict(size=8, color="rgba(255,255,255,0.25)", family="DM Mono"))

    fig.add_annotation(x=1.5, y=0.50, xref="x", yref="y", text="RED",
                       showarrow=False,
                       font=dict(size=10, color="rgba(250,204,21,0.9)", family="DM Mono"))
    return fig
