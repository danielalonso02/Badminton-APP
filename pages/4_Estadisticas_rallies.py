"""
pages/4_Analisis_rallies.py  ·  Análisis de rallies
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_df, preprocess, STYLES, sidebar_logo, PLAYER_COLORS

st.set_page_config(page_title="Estadísticas rallies · Badminton", page_icon="🏸", layout="wide")
sidebar_logo()
st.markdown(STYLES, unsafe_allow_html=True)

# ── Datos ────────────────────────────────
df = get_df()
strokes, rally_rows, _, player1, player2 = preprocess(df)

jugador_col = "Jugador del golpeo"

DARK_BG  = "#0f1117"
GRID_COL = "#1f2937"
FONT_COL = "#9ca3af"
BASE_LAYOUT = dict(
    paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
    font=dict(family="DM Sans, sans-serif", color=FONT_COL),
    margin=dict(l=40, r=20, t=48, b=40),
    legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#f9fafb")),
)

def ax(title=""):
    return dict(title=title, tickfont=dict(size=10, color=FONT_COL),
                gridcolor=GRID_COL, zerolinecolor=GRID_COL)


# ── Sidebar: filtros ─────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### Filtros")
    sets_available = sorted(strokes["Set"].dropna().unique().astype(int)) if "Set" in strokes.columns else []
    set_sel = st.selectbox("Set", ["Todos"] + [f"Set {s}" for s in sets_available])
    top_n = st.slider("Top rallies más largos", min_value=3, max_value=20, value=10)

def apply_set_filter(df_in):
    if set_sel != "Todos" and "Set" in df_in.columns:
        return df_in[df_in["Set"] == int(set_sel.replace("Set ", ""))]
    return df_in

strokes_f = apply_set_filter(strokes)
rally_rows_f = apply_set_filter(rally_rows)


# ── Métricas por rally ───────────────────
rally_stats = (
    strokes_f.groupby("rally_id")
    .agg(n_golpes=("Stroke", "max"), set=("Set", "first"), rally=("Rally", "first"))
    .reset_index()
) if "rally_id" in strokes_f.columns else pd.DataFrame()

rally_dur_s = (rally_rows_f["Duración"] / 1000).dropna() if "Duración" in rally_rows_f.columns else pd.Series(dtype=float)
if not rally_stats.empty and "Duración" in rally_rows_f.columns and "rally_id" in rally_rows_f.columns:
    dur_map = (rally_rows_f.groupby("rally_id")["Duración"].first() / 1000)
    rally_stats["dur_s"] = rally_stats["rally_id"].map(dur_map)


# ─────────────────────────────────────────
# 1 · DURACIÓN DE RALLIES
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Duración de rallies</div>', unsafe_allow_html=True)

if not rally_dur_s.empty:
    col_h, col_b = st.columns(2)

    with col_h:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=rally_dur_s, nbinsx=25,
            marker_color="#60a5fa", marker_line_color="#1d4ed8",
            marker_line_width=0.5, opacity=0.85, name="Duración",
        ))
        mean_dur = rally_dur_s.mean()
        fig_hist.add_vline(x=mean_dur, line=dict(color="#facc15", width=1.5, dash="dot"))
        fig_hist.add_annotation(x=mean_dur, y=1, yref="paper", yanchor="top",
            text=f"media {mean_dur:.1f}s", showarrow=False,
            font=dict(size=9, color="#facc15"), xanchor="left", xshift=4)
        fig_hist.update_layout(**BASE_LAYOUT, height=280, showlegend=False,
            title=dict(text="Histograma de duración (s)", font=dict(size=12, color=FONT_COL), x=0),
            xaxis=ax("Segundos"), yaxis=ax("Nº rallies"))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        # Box por set
        if "Set" in strokes_f.columns and not rally_stats.empty and "dur_s" in rally_stats.columns:
            fig_box = go.Figure()
            set_colors = ["#60a5fa", "#f472b6", "#4ade80"]
            for i, s in enumerate(sorted(rally_stats["set"].dropna().unique().astype(int))):
                data_s = rally_stats[rally_stats["set"] == s]["dur_s"].dropna()
                fig_box.add_trace(go.Box(
                    y=data_s, name=f"Set {s}",
                    marker_color=set_colors[i % len(set_colors)],
                    boxmean=True, line_width=1.5,
                ))
            fig_box.update_layout(**BASE_LAYOUT, height=280, showlegend=False,
                title=dict(text="Duración por set (s)", font=dict(size=12, color=FONT_COL), x=0),
                yaxis=ax("Segundos"), xaxis=ax())
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            fig_box = go.Figure()
            fig_box.add_trace(go.Box(y=rally_dur_s, name="Todos",
                marker_color="#60a5fa", boxmean=True, line_width=1.5))
            fig_box.update_layout(**BASE_LAYOUT, height=280, showlegend=False,
                title=dict(text="Distribución duración (s)", font=dict(size=12, color=FONT_COL), x=0),
                yaxis=ax("Segundos"), xaxis=ax())
            st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Sin datos de duración de rallies.")


# ─────────────────────────────────────────
# 2 · LONGITUD (Nº GOLPES POR RALLY)
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Longitud de rallies · nº de golpes</div>', unsafe_allow_html=True)

if not rally_stats.empty:
    col_l1, col_l2 = st.columns(2)

    with col_l1:
        fig_len = go.Figure()
        fig_len.add_trace(go.Histogram(
            x=rally_stats["n_golpes"], nbinsx=20,
            marker_color="#a78bfa", marker_line_color="#6d28d9",
            marker_line_width=0.5, opacity=0.85,
        ))
        mean_len = rally_stats["n_golpes"].mean()
        fig_len.add_vline(x=mean_len, line=dict(color="#facc15", width=1.5, dash="dot"))
        fig_len.add_annotation(x=mean_len, y=1, yref="paper", yanchor="top",
            text=f"media {mean_len:.1f}", showarrow=False,
            font=dict(size=9, color="#facc15"), xanchor="left", xshift=4)
        fig_len.update_layout(**BASE_LAYOUT, height=280, showlegend=False,
            title=dict(text="Histograma de longitud (golpes)", font=dict(size=12, color=FONT_COL), x=0),
            xaxis=ax("Nº golpes"), yaxis=ax("Nº rallies"))
        st.plotly_chart(fig_len, use_container_width=True)

    with col_l2:
        # Scatter duración vs longitud
        if "dur_s" in rally_stats.columns:
            fig_sc = go.Figure()
            set_colors = ["#60a5fa", "#f472b6", "#4ade80"]
            if "set" in rally_stats.columns:
                for i, s in enumerate(sorted(rally_stats["set"].dropna().unique().astype(int))):
                    sub = rally_stats[rally_stats["set"] == s]
                    fig_sc.add_trace(go.Scatter(
                        x=sub["n_golpes"], y=sub["dur_s"],
                        mode="markers", name=f"Set {s}",
                        marker=dict(size=6, color=set_colors[i % len(set_colors)], opacity=0.7),
                        hovertemplate="Rally %{customdata}<br>Golpes: %{x}<br>Duración: %{y:.1f}s<extra></extra>",
                        customdata=sub["rally_id"].apply(lambda x: f"S{x.split('_')[0]}R{int(float(x.split('_')[1]))}") if "rally_id" in sub.columns else sub.index,
                    ))
            else:
                fig_sc.add_trace(go.Scatter(
                    x=rally_stats["n_golpes"], y=rally_stats["dur_s"],
                    mode="markers", marker=dict(size=6, color="#60a5fa", opacity=0.7),
                ))
            fig_sc.update_layout(**BASE_LAYOUT, height=280,
                title=dict(text="Longitud vs duración", font=dict(size=12, color=FONT_COL), x=0),
                xaxis=ax("Nº golpes"), yaxis=ax("Duración (s)"))
            st.plotly_chart(fig_sc, use_container_width=True)
else:
    st.info("Sin datos de longitud de rallies.")


# ─────────────────────────────────────────
# 3 · TOP N RALLIES MÁS LARGOS
# ─────────────────────────────────────────
st.markdown(f'<div class="section-title" style="font-size:14px;">Top {top_n} rallies más largos</div>', unsafe_allow_html=True)

if not rally_stats.empty:
    top_rallies = rally_stats.nlargest(top_n, "n_golpes").reset_index(drop=True)

    SET_COLORS = ["#facc15", "#60a5fa", "#4ade80", "#f472b6", "#a78bfa"]

    try:
        x_labels = [f"S{str(r).split('_')[0]}R{int(float(str(r).split('_')[1]))}"
                    for r in top_rallies["rally_id"]]
    except Exception:
        x_labels = [str(r) for r in top_rallies["rally_id"]]

    sets_in_top = list(top_rallies["set"].fillna(1).astype(int)) if "set" in top_rallies.columns else [1]*len(top_rallies)
    bar_colors = [SET_COLORS[(s-1) % len(SET_COLORS)] for s in sets_in_top]

    max_golpes = int(top_rallies["n_golpes"].max())

    fig_top = go.Figure()
    fig_top.add_trace(go.Bar(
        x=x_labels,
        y=list(top_rallies["n_golpes"]),
        marker_color=bar_colors,
        text=[int(x) for x in top_rallies["n_golpes"]],
        textposition="outside",
        textfont=dict(size=11, color="#f9fafb"),
        hovertemplate="Rally %{x}<br>%{y:.0f} golpes<extra></extra>",
        showlegend=False,
    ))
    mean_val = float(rally_stats["n_golpes"].mean())
    fig_top.add_hline(y=mean_val, line=dict(color="#6b7280", width=1, dash="dot"))
    fig_top.add_annotation(x=1, y=mean_val, xref="paper", yref="y",
        text=f"media {mean_val:.1f}", showarrow=False,
        font=dict(size=9, color="#6b7280"), xanchor="left", yshift=6)

    sets_shown = sorted(set(sets_in_top))
    for s in sets_shown:
        fig_top.add_trace(go.Bar(
            x=[None], y=[None],
            marker_color=SET_COLORS[(s-1) % len(SET_COLORS)],
            name=f"Set {s}", showlegend=True,
        ))

    fig_top.update_layout(**BASE_LAYOUT, height=340, showlegend=True,
        title=dict(text=f"Top {top_n} rallies por nº de golpes",
                   font=dict(size=14, color=FONT_COL), x=0),
        xaxis=dict(title="Rally", tickfont=dict(size=11, color="#f9fafb")),
        yaxis=dict(**ax("Nº golpes"), range=[0, max_golpes * 1.2]))
    fig_top.update_layout(legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#f9fafb")))
    st.plotly_chart(fig_top, use_container_width=True)

    # Tabla detalle
    with st.expander("Ver detalle de los rallies"):
        top_rallies["Rally"] = top_rallies["rally_id"].apply(
            lambda x: f"S{x.split('_')[0]}R{int(float(x.split('_')[1]))}")
        detail_cols = ["Rally", "n_golpes"]
        if "set" in top_rallies.columns:
            detail_cols.insert(1, "set")
        if "dur_s" in top_rallies.columns:
            detail_cols.append("dur_s")
            top_rallies["dur_s"] = top_rallies["dur_s"].round(1)

        rename = {"n_golpes": "Golpes", "set": "Set", "dur_s": "Duración (s)"}
        st.dataframe(top_rallies[detail_cols].rename(columns=rename).set_index("Rally"),
                     use_container_width=True)
else:
    st.info("Sin datos de rallies.")
    
    def build_transitions(player_strokes, player_name):
        """
        Transiciones del jugador consigo mismo (golpe n → golpe n+1 del mismo jugador)
        y transición final de su última fase → Victoria o Derrota.
        Un resultado por rally garantizado.
        """
        trans = {}
        for rid, group in player_strokes.sort_values("Stroke").groupby("rally_id"):
            phases = group["Game Phase"].dropna().tolist()
            if not phases:
                continue
            # Transiciones consecutivas entre golpes del mismo jugador
            for a, b in zip(phases[:-1], phases[1:]):
                trans[(a, b)] = trans.get((a, b), 0) + 1
            # Transición final: última fase del jugador → Victoria o Derrota
            winner = rally_winners.get(rid)
            if winner is not None:
                result = "Victoria" if winner == player_name else "Derrota"
                trans[(phases[-1], result)] = trans.get((phases[-1], result), 0) + 1
        return trans


# ─────────────────────────────────────────
# 4 · FLUJO DE FASES (MATRICES Y TRANSICIONES)
# ─────────────────────────────────────────
st.markdown('<div class="section-title" style="font-size:14px;">Análisis de Iniciativa y Flujo de Fases</div>', unsafe_allow_html=True)

if "Game Phase" in strokes_f.columns and "Rally" in strokes_f.columns:

    # 1. Configuración de Traducción y Colores
    PHASE_TRANSLATION = {
        "Attack": "Ataque", "Defence": "Defensa",
        "Construccion": "Construcción", "Construcción": "Construcción"
    }
    PHASE_COLORS = {"Construcción": "#3b82f6", "Ataque": "#f87171", "Defensa": "#facc15"}
    OUTCOME_COLORS = {"Victoria": "#4ade80", "Derrota": "#f87171"}

    # Traducir columna en el DataFrame local
    strokes_f = strokes_f.copy()
    strokes_f["Game Phase"] = strokes_f["Game Phase"].map(PHASE_TRANSLATION).fillna(strokes_f["Game Phase"])

    # --- FUNCIONES DE LÓGICA (RECUPERADAS) ---
    def get_rally_winner(outcome, p1, p2):
        o = str(outcome)
        if f"Error {p2}" in o or f"Unforced {p2}" in o: return p1
        if f"Error {p1}" in o or f"Unforced {p1}" in o: return p2
        if p1 in o: return p1
        if p2 in o: return p2
        return None

    def build_transitions(player_strokes, player_name, rally_winners):
        trans = {}
        for rid, group in player_strokes.sort_values("Stroke").groupby("rally_id"):
            phases = group["Game Phase"].dropna().tolist()
            if not phases: continue
            for a, b in zip(phases[:-1], phases[1:]):
                trans[(a, b)] = trans.get((a, b), 0) + 1
            winner = rally_winners.get(rid)
            if winner is not None:
                result = "Victoria" if winner == player_name else "Derrota"
                trans[(phases[-1], result)] = trans.get((phases[-1], result), 0) + 1
        return trans

    def get_matrix_df(trans):
        phase_nodes = sorted(set(n for (a, b) in trans for n in [a, b] if n not in ("Victoria", "Derrota")))
        all_nodes = phase_nodes + [n for n in ["Victoria", "Derrota"] if any(b == n for (a, b) in trans)]
        matrix = pd.DataFrame(0.0, index=phase_nodes, columns=all_nodes)
        for (a, b), v in trans.items():
            if a in matrix.index and b in matrix.columns: 
                matrix.loc[a, b] = v
        return matrix

    # --- FUNCIONES DE DIBUJO ---
    def plot_matrix_total(matrix, player_name, color):
        fig = go.Figure(go.Heatmap(
            z=matrix.values, x=list(matrix.columns), y=list(matrix.index),
            colorscale=[[0.0, "#0f1117"], [0.01, "#1e3a5f"], [0.4, color], [1.0, "#facc15"]],
            text=matrix.values, texttemplate="%{text}", textfont=dict(size=13, color="white"),
            showscale=False, hovertemplate="De: <b>%{y}</b><br>A: <b>%{x}</b><br>Veces: <b>%{z}</b><extra></extra>",
        ))
        fig.update_layout(**{k: v for k, v in BASE_LAYOUT.items() if k != "legend"}, height=280,
                          title=dict(text=f"{player_name.split()[0]} · Matriz Total", font=dict(size=12, color=FONT_COL), x=0))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    def plot_matrix_percent(matrix, player_name, color):
        matrix_pct = matrix.div(matrix.sum(axis=1), axis=0).fillna(0) * 100
        fig = go.Figure(go.Heatmap(
            z=matrix_pct.values, x=list(matrix_pct.columns), y=list(matrix_pct.index),
            colorscale=[[0.0, "#0f1117"], [1.0, color]],
            text=matrix_pct.values, texttemplate="%{text:.1f}%", textfont=dict(size=12, color="white"),
            showscale=False, hovertemplate="Origen: <b>%{y}</b><br>Destino: <b>%{x}</b><br>%: <b>%{z:.1f}%</b><extra></extra>",
        ))
        fig.update_layout(**{k: v for k, v in BASE_LAYOUT.items() if k != "legend"}, height=280,
                          title=dict(text=f"{player_name.split()[0]} · Distribución (El % de destinos por cada origen)", font=dict(size=12, color="#facc15"), x=0))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    def plot_transition_bars(trans, player_name, color):
        trans_rows = [{"Transición": f"{a} → {b}", "Veces": v, "origen": a} for (a, b), v in trans.items()]
        if not trans_rows: return
        trans_df = pd.DataFrame(trans_rows).sort_values("Veces", ascending=True).tail(10)
        bcolors = [OUTCOME_COLORS[r["Transición"].split(" → ")[1]] if r["Transición"].split(" → ")[1] in OUTCOME_COLORS 
                   else PHASE_COLORS.get(r["origen"], color) for _, r in trans_df.iterrows()]
        
        fig = go.Figure(go.Bar(x=trans_df["Veces"], y=trans_df["Transición"], orientation="h", 
                               marker_color=bcolors, text=trans_df["Veces"], textposition="outside"))
        fig.update_layout(**{k: v for k, v in BASE_LAYOUT.items() if k != "legend"}, height=320,
                          title=dict(text=f"{player_name.split()[0]} · Top Transiciones", font=dict(size=12, color=FONT_COL), x=0))
        st.plotly_chart(fig, use_container_width=True)

    # --- PROCESAMIENTO ---
    outcome_col = "Rally Outcome"
    rally_winners = {}
    if outcome_col in strokes_f.columns:
        last_per_rally = strokes_f.sort_values("Stroke").groupby("rally_id").last().reset_index()
        for _, row in last_per_rally.iterrows():
            winner = get_rally_winner(row.get(outcome_col, ""), player1, player2)
            rally_winners[row["rally_id"]] = winner

    p1_strokes = strokes_f[strokes_f[jugador_col] == player1]
    p2_strokes = strokes_f[strokes_f[jugador_col] == player2]
    
    trans_p1 = build_transitions(p1_strokes, player1, rally_winners)
    trans_p2 = build_transitions(p2_strokes, player2, rally_winners)

    mat_p1 = get_matrix_df(trans_p1)
    mat_p2 = get_matrix_df(trans_p2)

    # --- RENDERIZADO POR FILAS ---
    col1, col2 = st.columns(2)

    # FILA 1: Heatmap Total
    with col1: plot_matrix_total(mat_p1, player1, PLAYER_COLORS[0])
    with col2: plot_matrix_total(mat_p2, player2, PLAYER_COLORS[1])

    # FILA 2: Heatmap %
    with col1: plot_matrix_percent(mat_p1, player1, PLAYER_COLORS[0])
    with col2: plot_matrix_percent(mat_p2, player2, PLAYER_COLORS[1])

    # FILA 3: Barras horizontales
    with col1: plot_transition_bars(trans_p1, player1, PLAYER_COLORS[0])
    with col2: plot_transition_bars(trans_p2, player2, PLAYER_COLORS[1])

else:
    st.info("No se encontraron columnas de fase o rally para realizar el análisis.")
