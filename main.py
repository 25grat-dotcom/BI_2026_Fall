import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

warnings.filterwarnings('ignore')

# Configuración inicial de la interfaz
st.set_page_config(
    page_title="Visualizador de Pases - StatsBomb",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Análisis de Pases con StatsBomb y Streamlit")
st.markdown("Visualización interactiva de eventos y mapas de pases en partidos de fútbol.")

# Carga de datos con caché para mejorar la velocidad
@st.cache_data
def load_match_data(match_id):
    events = sb.events(match_id=match_id)

    variables = [
        'location',
        'minute',
        'period',
        'player',
        'second',
        'team',
        'type',
        'pass_end_location',
        'pass_recipient',
    ]
    
    available_vars = [col for col in variables if col in events.columns]
    passes = events[available_vars]

    # Filtrar únicamente los eventos de pase
    final = passes[passes['type'] == 'Pass'].copy()
    final.reset_index(drop=True, inplace=True)

    # Separar coordenadas de origen (x0, y0) y destino (x1, y1)
    final['x0'] = final.location.apply(lambda x: x[0] if isinstance(x, list) and len(x) >= 2 else np.nan)
    final['y0'] = final.location.apply(lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else np.nan)
    
    if 'pass_end_location' in final.columns:
        final['x1'] = final.pass_end_location.apply(lambda x: x[0] if isinstance(x, list) and len(x) >= 2 else np.nan)
        final['y1'] = final.pass_end_location.apply(lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else np.nan)
        final.drop(columns=['pass_end_location'], inplace=True, errors='ignore')

    final.drop(columns=['location'], inplace=True, errors='ignore')
    return events, final


# Carga de eventos del partido (Japón vs España - Mundial 2022)
MATCH_ID = 3857255

try:
    with st.spinner('Cargando datos del partido desde StatsBomb...'):
        events, final_passes = load_match_data(MATCH_ID)
except Exception as e:
    st.error(f"Error al conectar con la API de StatsBomb: {e}")
    st.stop()

# -------------------------------------------------------------
# BARRA DE CONTROL DE TIEMPO (MINUTO A MINUTO) EN LA PANTALLA PRINCIPAL
# -------------------------------------------------------------
min_minute = int(final_passes['minute'].min())
max_minute = int(final_passes['minute'].max())

if 'selected_minute' not in st.session_state:
    st.session_state.selected_minute = min_minute

st.subheader("⏱️ Control Minuto a Minuto")

col_btn_prev, col_slider, col_btn_next = st.columns([1, 6, 1])

with col_btn_prev:
    st.write("") # Espaciador para alinear con el slider
    if st.button("⏮️ -1 Min", use_container_width=True):
        if st.session_state.selected_minute > min_minute:
            st.session_state.selected_minute -= 1

with col_slider:
    selected_minute = st.slider(
        "Desliza para cambiar de minuto:",
        min_value=min_minute,
        max_value=max_minute,
        key="selected_minute"
    )

with col_btn_next:
    st.write("") # Espaciador
    if st.button("1 Min ⏭️", use_container_width=True):
        if st.session_state.selected_minute < max_minute:
            st.session_state.selected_minute += 1

st.divider()

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["🌱 Campo de Juego", "📊 Resumen del Minuto", "🔍 Diagnóstico de Eventos"])

with tab1:
    st.subheader(f"Mapa de Pases en el Minuto {selected_minute}")
    
    # Filtrar pases del minuto seleccionado y limpiar coordenadas nulas
    passes_min = final_passes[final_passes.minute == selected_minute].dropna(subset=['x0', 'y0'])

    if passes_min.empty:
        st.info(f"No se registraron pases en el minuto {selected_minute}.")
    else:
        # Métricas rápidas
        col_m1, col_m2 = st.columns(2)
        teams = passes_min['team'].unique()
        for idx, team in enumerate(teams):
            count = len(passes_min[passes_min.team == team])
            if idx == 0:
                col_m1.metric(f"Pases {team}", count)
            else:
                col_m2.metric(f"Pases {team}", count)

        # Creación del campo con mplsoccer
        pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
        fig, ax = pitch.draw(figsize=(11, 7))

        # Dibujar puntos de origen del pase
        sns.scatterplot(
            data=passes_min,
            x='x0',
            y='y0',
            ax=ax,
            hue='team',
            s=120,
            zorder=3
        )

        # Dibujar vectores/flechas del pase si existen coordenadas de destino
        if 'x1' in passes_min.columns and 'y1' in passes_min.columns:
            valid_vectors = passes_min.dropna(subset=['x1', 'y1'])
            if not valid_vectors.empty:
                pitch.arrows(
                    valid_vectors.x0, valid_vectors.y0,
                    valid_vectors.x1, valid_vectors.y1,
                    ax=ax, color='yellow', alpha=0.6, width=2, headwidth=3
                )

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=2)
        st.pyplot(fig)

with tab2:
    st.subheader("Registro de Pases en este Minuto")
    passes_min = final_passes[final_passes.minute == selected_minute]
    
    display_cols = [c for c in ['second', 'team', 'player', 'pass_recipient', 'x0', 'y0', 'x1', 'y1'] if c in passes_min.columns]
    st.dataframe(passes_min[display_cols], use_container_width=True)

    st.subheader("Muestra General del Dataset Procesado")
    st.dataframe(final_passes.head(15), use_container_width=True)

with tab3:
    st.subheader("Mapa de Valores Faltantes (NaN) en Eventos Generales")
    
    fig_nulls, ax_nulls = plt.subplots(figsize=(10, 4))
    sns.heatmap(events.isna(), ax=ax_nulls, cbar=False, cmap='Blues')
    plt.xlabel("Columnas del Evento")
    plt.ylabel("Registros")
    st.pyplot(fig_nulls)
