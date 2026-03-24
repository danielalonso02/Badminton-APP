"""
app.py  ·  Portada con login, selector de partido y subida de CSV
Ejecutar con:  streamlit run app.py
"""

import streamlit as st
from pathlib import Path
from auth import init_users, is_logged_in, login_page, logout
from utils import get_csv_files, STYLES

st.set_page_config(
    page_title="Badminton Analytics",
    page_icon="🏸",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #f5f5f0; }

.hero {
    background: #111827;
    border-radius: 20px;
    padding: 52px 56px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-tag {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 54px;
    font-weight: 700;
    color: #f9fafb;
    line-height: 1.15;
    margin-bottom: 16px;
}
.hero-title span { color: #60a5fa; }
.hero-desc {
    font-size: 18px;
    color: #9ca3af;
    max-width: 540px;
    line-height: 1.7;
}
.hero-deco {
    position: absolute;
    right: 56px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 120px;
    opacity: 0.07;
    line-height: 1;
    pointer-events: none;
}
.feature-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 24px;
    height: 100%;
}
.feature-icon {
    font-size: 34px;
    margin-bottom: 12px;
}
.feature-title {
    font-size: 17px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 6px;
}
.feature-desc {
    font-size: 14px;
    color: #6b7280;
    line-height: 1.6;
}
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
}
.match-name {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
}
.match-meta {
    font-size: 13px;
    color: #9ca3af;
    font-family: 'DM Mono', monospace;
    margin-top: 2px;
}
.upload-zone {
    background: #f9fafb;
    border: 2px dashed #d1d5db;
    border-radius: 12px;
    padding: 28px;
    text-align: center;
}
.upload-zone-title {
    font-size: 16px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
}
.upload-zone-sub {
    font-size: 14px;
    color: #9ca3af;
}
.user-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    margin-bottom: 24px;
    font-size: 15px;
    color: #6b7280;
}
.user-name {
    font-weight: 600;
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

init_users()

if not is_logged_in():
    login_page()
    st.stop()

# ── Logo fijo esquina superior izquierda ─
from utils import sidebar_logo
sidebar_logo()

# ── Barra de usuario ─────────────────────
col_user, col_logout = st.columns([8, 1])
with col_user:
    st.markdown(f"""
    <div class="user-bar">
        <span>Conectado como <span class="user-name">{st.session_state['name']}</span></span>
    </div>""", unsafe_allow_html=True)
with col_logout:
    if st.button("Salir", use_container_width=True):
        logout()

# ── Hero ─────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-deco">🏸</div>
    <div class="hero-tag">🏸 Sports Intelligence</div>
    <div class="hero-title">Badminton<br><span>Analytics</span></div>
    <div class="hero-desc">
        Plataforma de análisis táctico para partidos de bádminton.
        Explora el rendimiento de cada jugadora, visualiza trayectorias
        en pista y descubre patrones en cada rally.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Cards de funcionalidades ─────────────
c1, c2, c3, c4, c5 = st.columns(5)
features = [
    ("📊", "Resumen",                "Métricas clave, marcador y momentum del partido.",    "pages/1_Resumen.py"),
    ("🏟️", "Mapa de pista",          "Heatmap de zonas y trayectorias de golpeos.",         "pages/2_Mapa_de_pista.py"),
    ("👤", "Estadísticas jugadoras", "Iniciativa, servicios y errores por jugadora.",       "pages/3_Estadisticas_jugadoras.py"),
    ("⚡", "Estadísticas rallies",   "Duración, longitud y flujo de fases entre rallies.",  "pages/4_Estadisticas_rallies.py"),
    ("🔍", "Detalle rally",          "Análisis golpe a golpe de cualquier rally.",           "pages/5_Detalle_rally.py"),
]
for col, (icon, title, desc, page) in zip([c1, c2, c3, c4, c5], features):
    with col:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)
        st.page_link(page, label=f"Ir a {title} →", use_container_width=True)

st.markdown("<div style='margin-top:36px'></div>", unsafe_allow_html=True)

# ── Selector + subida de CSV ─────────────
col_sel, col_gap, col_up = st.columns([5, 0.4, 4])

with col_sel:
    st.markdown('<div class="section-label">Seleccionar partido</div>', unsafe_allow_html=True)

    DATA_FOLDER = "datos"
    folder = Path(DATA_FOLDER)
    folder.mkdir(parents=True, exist_ok=True)
    csv_files = get_csv_files(folder)

    if not csv_files:
        st.info("No hay partidos disponibles. Sube uno a la derecha.")
    else:
        options = [f.name for f in csv_files]
        # Preseleccionar el partido activo si existe
        current = st.session_state.get("selected_file", "")
        current_name = Path(current).name if current else options[0]
        default_idx = options.index(current_name) if current_name in options else 0

        selected_label = st.selectbox(
            "Partido",
            options=options,
            index=default_idx,
            format_func=lambda x: "🏸  " + x.replace(".csv", "").replace("_", " "),
            label_visibility="collapsed",
        )
        selected_file = str(folder / selected_label)

        if st.button("Cargar partido", use_container_width=True, type="primary"):
            st.session_state["selected_file"] = selected_file
            st.session_state["data_folder"]   = DATA_FOLDER
            st.rerun()

        if "selected_file" in st.session_state:
            selected_name = Path(st.session_state["selected_file"]).stem.replace("_", " ")
            st.success(f"✓ Partido activo: **{selected_name}**")

with col_up:
    st.markdown('<div class="section-label">Subir nuevo partido</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Se usan los archivos con la forma _zonas.csv</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-zone">
        <div class="upload-zone-title">Arrastra tu CSV aquí</div>
        <div class="upload-zone-sub">o haz clic para seleccionar un archivo</div>
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "CSV", type=["csv"], label_visibility="collapsed"
    )
    if uploaded is not None:
        dest = folder / uploaded.name
        do_save = True
        if dest.exists():
            st.warning(f"`{uploaded.name}` ya existe.")
            do_save = st.checkbox("Sobreescribir archivo existente")

        if do_save:
            with open(dest, "wb") as out_f:
                out_f.write(uploaded.getbuffer())
            st.session_state["selected_file"] = str(dest)
            st.session_state["data_folder"]   = DATA_FOLDER
            st.success(f"✓ `{uploaded.name}` subido y cargado.")
            st.rerun()
