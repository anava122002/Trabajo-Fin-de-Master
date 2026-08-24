import streamlit as st

# ======================================================================================
# CONFIGURACIÓN Y CSS
# ======================================================================================

st.set_page_config(
    page_title="Ediciones",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500&display=swap');

    /* Reset y base */
    .stApp { background-color: #FFFFFF; }
    .block-container { 
        margin: 0 auto !important; 
        max-width: 100% !important; 
        padding: 1rem 5% !important;
    }

    /* Ocultar elementos secundarios sin romper el input */
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Header */
    .app-header {
        padding: 1rem 0;
        border-bottom: 1px solid #1C1C1C;
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .app-title {
        font-family: 'Playfair Display', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #101010;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 300;
        color: #888;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* Divisor vertical */
    .divider-line {
        background-color: #FFFFFF;
        height: 100%;
        min-height: 70vh;
    }

    /* Mensajes del chat */
    .chat-messages {
        max-height: 55vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        padding-right: 10px;
        margin-bottom: 1rem;
    }
    .msg-user {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #1C1C1C;
        background: #FAF8F5;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0 0.5rem 20%;
    }
    .msg-assistant {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #1C1C1C;
        padding: 0.75rem 1rem 0.75rem 0;
        margin: 0.5rem 20% 0.5rem 0;
        line-height: 1.6;
    }

    /* Estilo para st.chat_input */
    /* Eliminar contenedor exterior y sombras */
    [data-testid="stChatInput"] {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Caja principal del texto (unifica el fondo y quita bordes rígidos/rojos) */
    [data-testid="stChatInput"] > div {
        background-color: #FAF8F5 !important;
        border: 1px solid #E3DBCC !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    /* Quitar el borde rojo/azul al hacer clic o escribir */
    [data-testid="stChatInput"] > div:focus-within {
        border-color: #1C1C1C !important; /* O pon #E3DBCC si no quieres que cambie nada */
        box-shadow: none !important;
        outline: none !important;
    }

    /* El área de texto interna sin bordes ni fondos propios */
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #1C1C1C !important;
        font-family: 'Inter', sans-serif !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Panel de resultados */
    .results-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 1rem;
    }
    .book-title-responsive {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: #1C1C1C;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }
    .book-author-responsive {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 300;
        color: #555;
        margin-bottom: 1rem;
    }
    .book-detail-responsive {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #888;
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #E8E8E3;
    }
    .book-detail-label { font-weight: 500; color: #555; }

    /* Estado vacío */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 1rem;
        text-align: center;
    }
    .empty-state-icon { font-size: 2rem; margin-bottom: 1rem; opacity: 0.3; }
    .empty-state-text {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 300;
        color: #AAA;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================================================
# ESTADO DE LA SESIÓN
# ======================================================================================

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "resultados" not in st.session_state:
    st.session_state.resultados = []

if "indice_carrusel" not in st.session_state:
    st.session_state.indice_carrusel = 0


# ======================================================================================
# DATOS Y FUNCIONES PLACEHOLDER
# ======================================================================================

LIBROS_EJEMPLO = [
    {"titulo": "La Ilíada", "autor": "Homero", "editorial": "Cátedra", "año": "2013", "formato": "Rústica"},
    {"titulo": "La Ilíada", "autor": "Homero", "editorial": "Gredos", "año": "2010", "formato": "Cartoné"},
    {"titulo": "La Ilíada", "autor": "Homero", "editorial": "Alianza", "año": "2019", "formato": "Rústica"},
]

def responder(mensaje_usuario: str) -> str:
    return f"Procesando tu solicitud sobre: '{mensaje_usuario}'. ¿Alguna preferencia de formato?"


# ======================================================================================
# HEADER
# ======================================================================================

st.markdown("""
<div class="app-header">
    <span class="app-title">Ediciones</span>
    <span class="app-subtitle">Recomendador de ediciones de libros</span>
</div>
""", unsafe_allow_html=True)


# ======================================================================================
# LAYOUT PRINCIPAL
# ======================================================================================

col_chat, col_divider, col_resultados = st.columns([1, 0.05, 0.45])


# ── PANEL IZQUIERDO: CHAT ──────────────────────────────────────────────────────────────

with col_chat:
    # 1. Contenedor del historial
    html_chat = '<div class="chat-messages">'
    if not st.session_state.mensajes:
        html_chat += """
        <div style="opacity: 0.5; padding: 1rem;">
            <p style="font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1C1C1C; margin: 0;">
                ¿Qué libro estás buscando?
            </p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
                Descríbeme la obra, el autor, o lo que necesitas de la edición.
            </p>
        </div>
        """
    else:
        for msg in st.session_state.mensajes:
            if msg["rol"] == "usuario":
                html_chat += f'<div class="msg-user">{msg["contenido"]}</div>'
            else:
                html_chat += f'<div class="msg-assistant">{msg["contenido"]}</div>'
    html_chat += '</div>'
    
    st.markdown(html_chat, unsafe_allow_html=True)

    # 2. Input nativo de Streamlit (funciona siempre)
    texto = st.chat_input("Respuesta...")
    if texto:
        st.session_state.mensajes.append({"rol": "usuario", "contenido": texto})
        respuesta = responder(texto)
        st.session_state.mensajes.append({"rol": "asistente", "contenido": respuesta})
        st.session_state.resultados = LIBROS_EJEMPLO
        st.session_state.indice_carrusel = 0
        st.rerun()


# ── DIVISOR ────────────────────────────────────────────────────────────────────────────

with col_divider:
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)


# ── PANEL DERECHO: RESULTADOS ──────────────────────────────────────────────────────────

with col_resultados:
    if not st.session_state.resultados:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📖</div>
            <div class="empty-state-text">
                Las ediciones recomendadas aparecerán aquí.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = len(st.session_state.resultados)
        idx = st.session_state.indice_carrusel
        libro = st.session_state.resultados[idx]

        st.markdown(f'<div class="results-label">Edición {idx + 1} de {total}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="book-title-responsive">{libro["titulo"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="book-author-responsive">{libro["autor"]}</div>', unsafe_allow_html=True)

        for label, valor in [("Editorial", libro.get("editorial")), ("Año", libro.get("año")), ("Formato", libro.get("formato"))]:
            st.markdown(f"""
            <div class="book-detail-responsive">
                <span class="book-detail-label">{label}</span>
                <span>{valor}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        with nav_col1:
            if st.button("←", disabled=(idx == 0)):
                st.session_state.indice_carrusel -= 1
                st.rerun()
        with nav_col3:
            if st.button("→", disabled=(idx == total - 1)):
                st.session_state.indice_carrusel += 1
                st.rerun()