import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agente import agente_app

st.set_page_config(page_title="Ediciones - Recomendador", page_icon="📖", layout="wide")

# CSS Ajustado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Inter:wght@300;400;500&display=swap');
    .stApp { background-color: #FFFFFF; }
    .app-header { padding: 1rem 0; border-bottom: 1px solid #1C1C1C; margin-bottom: 1.5rem; }
    .app-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 600; color: #101010; }
    .book-card {
        border: 1px solid #E3DBCC;
        border-radius: 8px;
        padding: 1rem;
        background-color: #FAF8F5;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .book-score { font-size: 0.75rem; color: #888; font-weight: 600; text-transform: uppercase; }
    .book-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 600; color: #1C1C1C; margin: 0.3rem 0; }
    .book-author { font-size: 0.85rem; color: #555; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "resultados" not in st.session_state: st.session_state.resultados = []
if "edicion_seleccionada" not in st.session_state: st.session_state.edicion_seleccionada = None

def responder(texto_usuario: str) -> dict:
    historial = [
        HumanMessage(content=msg["contenido"]) if msg["rol"] == "usuario" else AIMessage(content=msg["contenido"])
        for msg in st.session_state.mensajes
    ]
    return agente_app.invoke({"preguntas": historial})

def procesar_mensaje_usuario(texto_usuario: str):
    if not texto_usuario.strip(): return
    st.session_state.mensajes.append({"rol": "usuario", "contenido": texto_usuario})
    
    estado_final = responder(texto_usuario)
    texto_agente = estado_final.get("respuesta_final") or estado_final["preguntas"][-1].content
    
    st.session_state.mensajes.append({"rol": "asistente", "contenido": texto_agente})
    
    if "top_libros" in estado_final:
        st.session_state.resultados = estado_final["top_libros"]
    st.rerun()

# Layout
st.markdown('<div class="app-header"><span class="app-title">Ediciones</span></div>', unsafe_allow_html=True)
col_chat, col_resultados = st.columns([0.4, 0.6])

with col_chat:
    st.subheader("Conversación")
    for msg in st.session_state.mensajes:
        role_label = "👤 Usuario" if msg["rol"] == "usuario" else "📖 Asistente"
        st.chat_message(msg["rol"]).write(msg["contenido"])
        
    texto = st.chat_input("Escribe tu consulta o título...")
    if texto:
        procesar_mensaje_usuario(texto)

with col_resultados:
    st.subheader("Ediciones Recomendadas")
    
    # 1. Estado explícito: Sin resultados
    if "resultados" in st.session_state and isinstance(st.session_state.resultados, list):
        if len(st.session_state.resultados) == 0 and len(st.session_state.mensajes) > 0:
            st.warning("⚠️ No se ha encontrado ninguna edición con los criterios indicados.")
        elif len(st.session_state.resultados) > 0:
            # 2. Comparativa simultánea de hasta 3 alternativas
            libros = st.session_state.resultados[:3]
            cols_cards = st.columns(len(libros))
            
            for idx, (col, libro) in enumerate(zip(cols_cards, libros)):
                with col:
                    st.markdown(f"""
                    <div class="book-card">
                        <div>
                            <div class="book-score">Top {idx+1} • Score TOPSIS: {libro.get('score_topsis', 0):.2f}</div>
                            <div class="book-title">{libro.get('titulo', 'Sin Título')}</div>
                            <div class="book-author">{libro.get('autor', 'Desconocido')}</div>
                            <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #E3DBCC;">
                            <small>
                                <b>Editorial:</b> {libro.get('editorial', 'N/A')}<br>
                                <b>Encuadernación:</b> {libro.get('encuadernacion', 'N/A')}<br>
                                <b>Precio:</b> {libro.get('precio', 'N/A')} €
                            </small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    # Acciones finales asociadas a cada edición
                    if st.button(f"Seleccionar Opción {idx+1}", key=f"btn_{idx}"):
                        st.session_state.edicion_seleccionada = libro
                        st.success(f"Seleccionada edición de {libro.get('editorial')}")

            # Mostrar ficha seleccionada o enlace directo
            if st.session_state.edicion_seleccionada:
                st.divider()
                st.markdown("### Acción Final")
                ed = st.session_state.edicion_seleccionada
                st.info(f"Has elegido **{ed.get('titulo')}** ({ed.get('editorial')}).")
                if ed.get('url'):
                    st.link_button("Ir a la edición elegida", ed['url'])