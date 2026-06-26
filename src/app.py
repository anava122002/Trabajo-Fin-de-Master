import streamlit as st

# Cosas a cambiar:
# que la ventana no se amplíe, si no que se vaya hacia abajo con una barra
# LA BARRA DE Input debe ocupar todo su div
# más separación entre bloque de chat y bloque de resultados

# ======================================================================================
# CONFIGURACIÓN
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
    .block-container { margin: 0 auto !important; max-width: 100% !important; padding: 0 10% !important;}

    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Header */
    .app-header {
        padding: 1.5rem 3rem;
        border-bottom: 1px solid #1C1C1C;
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 3.5rem;
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

    /* Layout principal */
    .main-layout {
        display: grid;
        grid-template-columns: 1fr 1px 420px;
        height: calc(100vh - 73px);
    }
    .divider-line {
        background-color: #1C1C1C;
        height: 100%;
    }

    /* Panel chat */
    .chat-messages {
        height: 65vh !important;   /* Obliga al contenedor a medir el 65% de la pantalla */
        overflow-y: auto !important;/* Activa el scroll vertical */
        display: flex !important;
        flex-direction: column !important;
        padding-right: 10px;       /* Margen para que la barra de scroll no pise el texto */
    }
    .chat-panel {
        display: flex;
        flex-direction: column;
        height: 100%;
        overflow: hidden;
    }
    .chat-input-area {
        padding: 1.5rem 0 1.5rem 3rem;
        border-top: 1px solid #E3DBCC;
        background: #FAFAF7;
        width: 100% !important;
        max-width: 100% !important;
    }

    /* Mensajes */
    .msg-user {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #1C1C1C;
        background: #FAF8F5;
        padding: 0.75rem 1rem;
        border-radius: 20px;
        margin: 1rem 0 0.5rem 20%;
    }
    .msg-assistant {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #1C1C1C;
        padding: 0.75rem 0;
        margin: 0.5rem 20% 1rem 0;
        line-height: 1.6;
        padding-left: 1rem;
    }
    .msg-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 0.25rem;
    }

    /* Input de chat */
    [data-testid="stVerticalBlock"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        width: 90% !important;        
        max-width: 750px !important;  
        margin: 0 auto !important;
    }
    .stTextInput, 
    .stTextInput > div, 
    .stTextInput > div > div, 
    .stTextInput > div > div > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    .stTextInput input {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        padding: 0rem 0 !important;
        color: #1C1C1C !important;
        box-shadow: none !important;
        background-color: #FAF8F5 !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    .stTextInput input:focus {
        box-shadow: 0 0 0 1px #1C1C1C !important;
        background-color: #FAF8F5 !important;
    }
            
    .stTextInput input::placeholder { color: #AAA !important; }

    /* Panel resultados */
    .results-panel-container {
        max-height: 70vh !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .results-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 1.5rem;
    }

    /* Carrusel */
    .book-cover-responsive {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-bottom: 1vh;
    }
    .book-cover-responsive img {
        max-height: 40vh !important; 
        width: auto !important;       
        object-fit: contain;
    }

    .book-cover-container-responsive {
        width: 50%;
        margin: 0 auto 1vh auto;
        max-height: 40vh !important;
        aspect-ratio: 2/3;
        background: #FAF8F5;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Info del libro */
    .book-title-responsive {
        font-family: 'Playfair Display', serif;
        font-size: calc(1.5rem + 0.5vh) !important; 
        font-weight: 600;
        color: #1C1C1C;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }
    
    .book-author-responsive {
        font-family: 'Inter', sans-serif;
        font-size: calc(0.8rem + 0.1vh) !important;
        font-weight: 300;
        color: #555;
        margin-bottom: 1vh;
    }

    .book-detail-responsive {
        font-family: 'Inter', sans-serif;
        font-size: calc(0.75rem + 0.1vh) !important;
        color: #888;
        display: flex;
        justify-content: space-between;
        padding: 0.3vh 0; 
        border-bottom: 1px solid #E8E8E3;
    }
    .book-detail-label { font-weight: 500; color: #555; }

    /* Navegación carrusel */
    .carousel-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 1.5rem;
    }
    .carousel-counter {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #888;
        letter-spacing: 0.05em;
    }

    /* Botones de navegación */
    .stButton button {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 400 !important;
        background: transparent !important;
        color: #1C1C1C !important;
        border: 1px solid #1C1C1C !important;
        border-radius: 36000 !important;
        padding: 0.4rem 1rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton button:hover {
        background: #1C1C1C !important;
        color: #FAFAF7 !important;
    }
    .stButton button:disabled {
        opacity: 0.3 !important;
        cursor: not-allowed !important;
    }

    /* Estado vacío */
    .empty-state {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        text-align: center;
    }
    .empty-state-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.3;
    }
    .empty-state-text {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 300;
        color: #AAA;
        line-height: 1.6;
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
    st.session_state.resultados = []      # lista de dicts con info de cada libro

if "indice_carrusel" not in st.session_state:
    st.session_state.indice_carrusel = 0


# ======================================================================================
# DATOS DE EJEMPLO (reemplazar con lógica real)
# ======================================================================================

LIBROS_EJEMPLO = [
    {
        "titulo": "La Ilíada",
        "autor": "Homero",
        "editorial": "Cátedra",
        "traductor": "Emilio Crespo Güemes",
        "año": "2013",
        "formato": "Rústica",
        "peso": "520 g",
        "portada": None,
    },
    {
        "titulo": "La Ilíada",
        "autor": "Homero",
        "editorial": "Gredos",
        "traductor": "Antonio López Eire",
        "año": "2010",
        "formato": "Cartoné",
        "peso": "780 g",
        "portada": None,
    },
    {
        "titulo": "La Ilíada",
        "autor": "Homero",
        "editorial": "Alianza",
        "traductor": "Oscar Martínez García",
        "año": "2019",
        "formato": "Rústica",
        "peso": "410 g",
        "portada": None,
    },
]


# ======================================================================================
# LÓGICA DEL CHATBOT (esqueleto — reemplazar con IA real)
# ======================================================================================

def responder(mensaje_usuario: str) -> str:
    """Placeholder. Aquí irá la llamada al agente con LangGraph."""
    return "Entendido. ¿Tienes alguna preferencia sobre el formato o el peso del libro?"


def buscar_libros(mensajes: list) -> list:
    """Placeholder. Aquí irá el filtrado del dataset y el reranking."""
    return LIBROS_EJEMPLO


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

col_chat, col_divider, col_resultados = st.columns([1, 0.15, 0.5])


# ── PANEL IZQUIERDO: CHAT ──────────────────────────────────────────────────────────────

with col_chat:
    chat_container = st.container() 
    
    with chat_container:
        # 1. Iniciamos la cadena de texto HTML con el contenedor del scroll
        html_chat = '<div class="chat-messages">'
        
        if not st.session_state.mensajes:
            html_chat += """
            <div style="opacity: 0.5; padding: 1rem;">
                <p style="font-family: 'Playfair Display', serif; font-size: 1.5rem; 
                           color: #1C1C1C; line-height: 1.4; margin: 0;">
                    ¿Qué libro estás buscando?
                </p>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.8rem; 
                           color: #888; font-weight: 300; margin-top: 0.5rem;">
                    Descríbeme la obra, el autor, o lo que necesitas de la edición.
                </p>
            </div>
            """
        else:
            # 2. Acumulamos todos los mensajes reales dentro del mismo string
            for msg in st.session_state.mensajes:
                if msg["rol"] == "usuario":
                    html_chat += f'<div class="msg-user">{msg["contenido"]}</div>'
                else:
                    html_chat += f'<div class="msg-assistant">{msg["contenido"]}</div>'
                    
        # 3. Cerramos el contenedor div
        html_chat += '</div>'
        
        # 4. Renderizamos TODO el bloque junto para que Streamlit no rompa el CSS
        st.markdown(html_chat, unsafe_allow_html=True)

    # El input se queda abajo fijo, fuera del contenedor de scroll
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([9, 1])
        with col_input:
            texto = st.text_input(
                label="mensaje",
                placeholder="Escribe aquí...",
                label_visibility="collapsed"
            )
        with col_btn:
            enviado = st.form_submit_button("→")

    if enviado and texto.strip():
        st.session_state.mensajes.append({"rol": "usuario", "contenido": texto})
        respuesta = responder(texto)
        st.session_state.mensajes.append({"rol": "asistente", "contenido": respuesta})
        st.session_state.resultados = buscar_libros(st.session_state.mensajes)
        st.session_state.indice_carrusel = 0
        st.rerun()


# ── DIVISOR ────────────────────────────────────────────────────────────────────────────

with col_divider:
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)


# ── PANEL DERECHO: RESULTADOS ──────────────────────────────────────────────────────────

with col_resultados:
    st.markdown("<div class='results-panel-container'>", unsafe_allow_html=True)

    if not st.session_state.resultados:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">◻</div>
            <div class="empty-state-text">
                Las ediciones recomendadas<br>aparecerán aquí.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        total = len(st.session_state.resultados)
        idx = st.session_state.indice_carrusel
        libro = st.session_state.resultados[idx]

        st.markdown(f'<div class="results-label">Edición {idx + 1} de {total}</div>',
                    unsafe_allow_html=True)

        # Portada (Le inyectamos una clase específica para controlarla por CSS)
        if libro.get("portada"):
            st.markdown(f'<div class="book-cover-responsive"><img src="{libro["portada"]}" /></div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="book-cover-container-responsive">
                <span class="book-cover-placeholder">sin portada</span>
            </div>
            """, unsafe_allow_html=True)

        # Título y autor
        st.markdown(f"""
        <div class="book-title-responsive">{libro['titulo']}</div>
        <div class="book-author-responsive">{libro['autor']}</div>
        """, unsafe_allow_html=True)

        # Detalles
        detalles = [
            ("Editorial", libro.get("editorial", "—")),
            ("Año", libro.get("año", "—")),
            ("Formato", libro.get("formato", "—"))
        ]

        for label, valor in detalles:
            st.markdown(f"""
            <div class="book-detail-responsive">
                <span class="book-detail-label">{label}</span>
                <span>{valor}</span>
            </div>
            """, unsafe_allow_html=True)

        # Navegación fija abajo
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        with nav_col1:
            if st.button("←", disabled=(idx == 0)):
                st.session_state.indice_carrusel -= 1
                st.rerun()
        with nav_col3:
            if st.button("→", disabled=(idx == total - 1)):
                st.session_state.indice_carrusel += 1
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)