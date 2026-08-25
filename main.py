import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

warnings.filterwarnings('ignore')
Python
import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

warnings.filterwarnings('ignore')

# Configuración de página
st.set_page_config(
    page_title="Visualizador de Pases - StatsBomb", layout="wide"
)

st.title("⚽ Análisis de Pases con StatsBomb y Streamlit")
st.write(
    "Visualización interactiva del mapa de pases de un partido del Mundial Qatar 2022."
)


# Función con caché para optimizar la carga de datos
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
    passes = events[variables]

    # Filtrar solo pases
    final = passes[passes['type'] == 'Pass'].copy()
    final.reset_index(drop=True, inplace=True)

    # Extraer coordenadas x, y
    final['x0'] = final.location.apply(lambda x: x[0] if isinstance(x, list) else np.nan)
    final['y0'] = final.location.apply(lambda x: x[1] if isinstance(x, list) else np.nan)
    final['x1'] = final.pass_end_location.apply(
        lambda x: x[0] if isinstance(x, list) else np.nan
    )
    final['y1'] = final.pass_end_location.apply(
        lambda x: x[1] if isinstance(x, list) else np.nan
    )

    final.drop(columns=['location', 'pass_end_location'], inplace=True)
    return events, final


# Cargar datos del partido seleccionado (Match ID: 3857255 -> Japón)
with st.spinner('Cargando eventos del partido de StatsBomb...'):
    events, final_passes = load_match_data(3857255)

# Sidebar / Selectores de usuario
st.sidebar.header("Opciones de Control")

# Slider para seleccionar el minuto (reemplaza ipywidgets.interact)
min_minute = int(final_passes['minute'].min())
max_minute = int(final_passes['minute'].max())
selected_minute = st.sidebar.slider(
    "Selecciona el Minuto:",
    min_value=min_minute,
    max_value=max_minute,
    value=0,
)

# Sección principal con pestañas
tab1, tab2, tab3 = st.tabs(
    ["🌱 Mapa de Pases", "📊 Análisis de Datos", "🔍 Diagnóstico de Datos Faltantes"]
)

with tab1:
    st.subheader(f"Pases en el Minuto {selected_minute}")

    passes_min = final_passes[final_passes.minute == selected_minute]

    if passes_min.empty:
        st.warning(
            f"No hay registros de pases registrados en el minuto {selected_minute}."
        )
    else:
        # Dibujar campo de juego
        pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
        fig, ax = pitch.draw(figsize=(10, 6))

        sns.scatterplot(
            data=passes_min,
            x='x0',
            y='y0',
            ax=ax,
            hue='team',
            s=100,
            alpha=0.9,
        )
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=2)

        # Mostrar gráfico en Streamlit
        st.pyplot(fig)

    st.subheader("Pases Registrados en este Minuto")
    st.dataframe(
        passes_min[
            ['minute', 'second', 'team', 'player', 'pass_recipient', 'x0', 'y0']
        ]
    )

with tab2:
    st.subheader("Muestra de Datos de Pases Procesados")
    st.dataframe(final_passes.head(20))

    st.subheader("Columnas Disponibles en los Eventos")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Columnas relacionadas con 'pass':**")
        pass_cols = [col for col in events.columns if 'pass' in col]
        st.write(pass_cols)

    with col2:
        st.write("**Otras columnas:**")
        other_cols = [col for col in events.columns if 'pass' not in col]
        st.write(other_cols[:15])  # Muestra primeros 15

with tab3:
    st.subheader("Mapa de Calor de Datos Faltantes (Na) en Eventos")
    fig_nulls, ax_nulls = plt.subplots(figsize=(10, 4))
    sns.heatmap(events.isna(), ax=ax_nulls, cbar=False, cmap='Blues')
    st.pyplot(fig_nulls)
