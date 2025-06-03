import streamlit as st
import pandas as pd
from pypmml import Model
import re
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="🧠 Evaluación de Bienestar Mental",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar modelo PMML
@st.cache_resource
def load_model():
    return Model.load('prueba3.pmml')

model = load_model()

# Variables del modelo
input_fields = model.inputNames
target_fields = model.targetFields

# Opciones para variables categóricas
opciones_categoricas = {
    "genero": ["Femenino", "Masculino"],
    "Nivel_Academico": ["Escuela Secundaria", "Pregrado", "Posgrado"],
    "Plataforma_mas_usada": [
        "Instagram", "Twitter", "TikTok", "YouTube", "Facebook",
        "LinkedIn", "Snapchat", "LINE", "KakaoTalk", "VKontakte",
        "WhatsApp", "WeChat"
    ],
    "Estado_Sentimental": ["Soltero/a", "En una relación", "Complicado"],
    "Afecta_Rendimiento_Academico": ["Sí", "No"],
    "Conflictos_Por_Redes_Sociales": ["Sí", "No"]
}

# Conversión sí/no a binario
def si_no_a_binario(valor):
    if isinstance(valor, str):
        return 1 if valor.strip().lower() == "sí" else 0
    return valor

# Función auxiliar para obtener color según puntaje
def get_color(puntaje):
    if puntaje <= 3:
        return "#4caf50"  # Verde
    elif puntaje <= 6:
        return "#ffc107"  # Amarillo
    elif puntaje <= 8:
        return "#ff9800"  # Naranja
    else:
        return "#f44336"  # Rojo

# Diseño de la interfaz
st.title("🧠 Sistema de Evaluación de Bienestar Mental")
st.markdown("""
    <style>
    .main {background-color: #f0f9ff;}
    .stButton>button {background-color: #4fc3f7; color: black; font-weight: bold;}
    .stButton>button:hover {background-color: #29b6f6;}
    .css-1d391kg {padding-top: 1.5rem;}
    .reportview-container .markdown-text-container {font-family: Arial;}
    .header-style {font-size:24px; font-weight:bold; color:#1565c0; background-color:#e3f2fd; padding:15px; border-radius:10px;}
    </style>
    """, unsafe_allow_html=True)

# Dividir en columnas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Información del Usuario")
    datos = {}
    
    # Crear formulario
    for campo in input_fields:
        label = campo.replace('_', ' ').title()
        
        if campo in opciones_categoricas:
            datos[campo] = st.selectbox(
                label, 
                options=opciones_categoricas[campo],
                key=campo
            )
        elif campo in ["Edad", "Promedio_Horas_Diarias_Uso", "Descanso", "Puntaje_Salud_Mental"]:
            datos[campo] = st.slider(
                label,
                min_value=0,
                max_value=24 if campo in ["Promedio_Horas_Diarias_Uso", "Descanso"] else 100,
                value=0,
                key=campo
            )
        else:
            datos[campo] = st.number_input(
                label,
                min_value=0,
                max_value=100,
                value=0,
                key=campo
            )
    
    # Botón de evaluación
    if st.button("🔍 Realizar Evaluación", use_container_width=True):
        st.session_state.evaluated = True
        st.session_state.datos = datos
    else:
        st.session_state.evaluated = False

# Resultados
with col2:
    st.subheader("📊 Resultados de la Evaluación")
    
    if st.session_state.get('evaluated', False):
        try:
            # Preparar datos para predicción
            datos_pred = {}
            for campo, valor in st.session_state.datos.items():
                if campo in ["Afecta_Rendimiento_Academico", "Conflictos_Por_Redes_Sociales"]:
                    datos_pred[campo] = si_no_a_binario(valor)
                else:
                    datos_pred[campo] = valor
            
            # Realizar predicción
            df = pd.DataFrame([datos_pred])
            resultado = model.predict(df)
            resultado_dict = resultado.to_dict(orient='records')[0]
            
            # Obtener predicción
            prediccion = None
            for k, v in resultado_dict.items():
                k_limpio = re.sub(r'[^a-zA-Z0-9_]', '', k).lower()
                if 'predicted' in k_limpio or any(t.lower() in k_limpio for t in target_fields):
                    prediccion = v
                    break
            
            if prediccion is not None:
                # Mostrar gráficos
                fig, axs = plt.subplots(1, 2, figsize=(10, 4))
                
                # Gráfico 1: Puntaje de salud mental
                ax = axs[0]
                ax.bar(["Salud Mental"], [prediccion], color=get_color(prediccion))
                ax.set_ylim(0, 10)
                ax.set_ylabel("Puntaje (0-10)")
                ax.set_title("📊 Puntaje de Salud Mental")
                ax.axhline(y=3, color='green', linestyle='--', alpha=0.5)
                ax.axhline(y=6, color='orange', linestyle='--', alpha=0.5)
                ax.axhline(y=8, color='red', linestyle='--', alpha=0.5)
                
                # Gráfico 2: Factores de riesgo
                ax = axs[1]
                factores = ["Horas Uso", "Calidad Descanso", "Conflictos"]
                valores = [
                    float(st.session_state.datos["Promedio_Horas_Diarias_Uso"]),
                    10 - float(st.session_state.datos["Descanso"]),
                    8 if st.session_state.datos["Conflictos_Por_Redes_Sociales"] == "Sí" else 2
                ]
                colores = [get_color(v) for v in valores]
                
                ax.barh(factores, valores, color=colores)
                ax.set_xlim(0, 10)
                ax.set_title("📈 Factores de Riesgo")
                ax.set_xlabel("Nivel de Riesgo")
                
                for i, v in enumerate(valores):
                    ax.text(v + 0.2, i, f"{v:.1f}", color='black', va='center')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Mostrar recomendaciones
                st.subheader("📝 Recomendaciones")
                
                color = get_color(prediccion)
                st.markdown(f"<p style='font-size:18px; color:{color}; font-weight:bold;'>"
                            f"Tu puntaje de salud mental es: {prediccion:.1f}/10</p>", 
                            unsafe_allow_html=True)
                
                if prediccion <= 3:
                    st.success("✅ Excelente salud mental. ¡Sigue con tus buenos hábitos!")
                    st.markdown("""
                    - Continúa manteniendo un equilibrio saludable entre tecnología y actividades offline
                    - Practica actividades de mindfulness para mantener tu bienestar
                    - Comparte tus hábitos saludables con amigos y familiares
                    """)
                elif prediccion <= 6:
                    st.warning("⚠️ Estado mental aceptable, pero hay áreas de oportunidad")
                    st.markdown("""
                    - Reduce tu tiempo en redes sociales en 1 hora diaria
                    - Establece horarios libres de dispositivos electrónicos
                    - Practica técnicas de respiración cuando sientas estrés
                    - Mejora tu higiene de sueño con rutinas consistentes
                    """)
                elif prediccion <= 8:
                    st.warning("⚠️⚠️ Tu salud mental podría estar en riesgo. Necesitas cambios")
                    st.markdown("""
                    - Considera una desintoxicación digital durante al menos un día a la semana
                    - Habla con un profesional de salud mental si la ansiedad persiste
                    - Fomenta actividades físicas y sociales presenciales
                    - Limita el uso de plataformas que generan ansiedad
                    """)
                else:
                    st.error("❌ Tu salud mental está en un nivel crítico. Busca ayuda profesional.")
                    st.markdown("""
                    - Consulta con un psicólogo o psiquiatra lo antes posible
                    - No dudes en apoyarte en familiares y amigos
                    - Considera reducir el uso de redes sociales drásticamente
                    - Sigue un plan de tratamiento profesional
                    """)
                
                # Guardar resultados en sesión
                st.session_state.prediccion = prediccion
                
            else:
                st.error("No se pudo obtener una predicción válida del modelo")
        
        except Exception as e:
            st.error(f"Error al realizar la evaluación: {str(e)}")
    
    else:
        # Estado inicial
        st.info("Complete el formulario y haga clic en 'Realizar Evaluación' para ver los resultados")
        placeholder = Image.new('RGB', (800, 400), color='#f0f9ff')
        st.image(placeholder, caption='Resultados de evaluación aparecerán aquí')

# Notas al pie
st.markdown("---")
st.markdown("""
**Nota:** Esta aplicación evalúa el bienestar mental basado en tus hábitos de uso de redes sociales y otros factores. 
Los resultados son aproximados y no sustituyen una evaluación profesional.
""")