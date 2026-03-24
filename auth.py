"""
auth.py  ·  Sistema de login simple con JSON
"""

import json
import hashlib
import streamlit as st
from pathlib import Path

USERS_FILE = Path("users.json")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def init_users():
    """Crea users.json con un usuario admin por defecto si no existe."""
    if not USERS_FILE.exists():
        _save_users({
            "admin": {
                "name":     "Administrador",
                "password": _hash("admin123"),   # ← cámbiala tras el primer login
            }
        })


def add_user(username: str, name: str, password: str) -> bool:
    """Añade un usuario nuevo. Devuelve False si ya existe."""
    users = _load_users()
    if username in users:
        return False
    users[username] = {"name": name, "password": _hash(password)}
    _save_users(users)
    return True


def check_credentials(username: str, password: str) -> str | None:
    """Devuelve el nombre del usuario si las credenciales son correctas, si no None."""
    users = _load_users()
    user = users.get(username)
    if user and user["password"] == _hash(password):
        return user["name"]
    return None


def is_logged_in() -> bool:
    return st.session_state.get("authenticated", False)


def login_page():
    """Muestra la pantalla de login y gestiona el estado de sesión."""
    # Centrar el formulario
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
        from pathlib import Path
        logo_path = Path("imagenes/logo.png")
        if logo_path.exists():
            st.image(str(logo_path), width=450)
        else:
            st.markdown('<div style="text-align:center;font-size:32px;">🏸</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
          <div style="font-size:32px; font-weight:600; color:grey; margin-top:8px;">
            Badminton Analytics
          </div>
          <div style="font-size:13px; color:#6b7280; margin-top:4px; font-family:'DM Mono',monospace;">
            Inicia sesión para continuar
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="usuario")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)

        if submitted:
            name = check_credentials(username.strip(), password)
            if name:
                st.session_state["authenticated"] = True
                st.session_state["username"]      = username.strip()
                st.session_state["name"]          = name
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")


def logout():
    """Cierra la sesión limpiando el estado."""
    for key in ["authenticated", "username", "name"]:
        st.session_state.pop(key, None)
    st.rerun()
