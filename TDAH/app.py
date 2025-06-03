import tkinter as tk
from tkinter import ttk, messagebox
from pypmml import Model
import pandas as pd
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Cargar modelo PMML
model = Model.load('prueba3.pmml')  # Asegúrate que esté en la misma carpeta

input_fields = model.inputNames
target_fields = model.targetFields

# Opciones para variables categóricas según tu XML
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

# Ventana principal
ventana = tk.Tk()
ventana.title("🧠 Evaluación de Bienestar Mental")
ventana.geometry("1200x800")
ventana.configure(bg="#f0f9ff")

# Estilo
estilo = ttk.Style()
estilo.configure("TFrame", background="#f0f9ff")
estilo.configure("TLabel", background="#f0f9ff", font=("Arial", 10))
estilo.configure("TButton", font=("Arial", 10, "bold"), background="#4fc3f7", foreground="black")
estilo.map("TButton", background=[("active", "#29b6f6")])

# Marco principal
main_frame = ttk.Frame(ventana, padding=20)
main_frame.pack(fill="both", expand=True)

# Título
titulo_frame = ttk.Frame(main_frame)
titulo_frame.pack(fill="x", pady=(0, 20))

tk.Label(titulo_frame, text="🧠 Sistema de Evaluación de Bienestar Mental",
         font=("Helvetica", 24, "bold"), bg="#e3f2fd", fg="#1565c0",
         padx=20, pady=10).pack(fill="x")

# Contenedor para formulario y resultados
content_frame = ttk.Frame(main_frame)
content_frame.pack(fill="both", expand=True)

# Formulario
form_frame = ttk.LabelFrame(content_frame, text="📋 Información del Usuario", padding=15)
form_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

# Dividir campos en 2 columnas
mid_point = len(input_fields) // 2
variables = {}

for i, campo in enumerate(input_fields):
    col = i // (mid_point + 1)
    row = i % (mid_point + 1)

    frame_campo = ttk.Frame(form_frame)
    frame_campo.grid(row=row, column=col, sticky="ew", pady=5, padx=5)

    ttk.Label(frame_campo, text=f"{campo.replace('_', ' ').title()}:",
              width=30, anchor="e").pack(side="left", padx=(0, 10))

    var = tk.StringVar()

    if campo in opciones_categoricas:
        entrada = ttk.Combobox(frame_campo, textvariable=var,
                              values=opciones_categoricas[campo],
                              state="readonly", width=20)
        entrada.current(0)
    elif campo in ["Edad", "Promedio_Horas_Diarias_Uso", "Conflictos_Por_Redes_Sociales",
                   "Afecta_Rendimiento_Academico", "Descanso", "Puntaje_Salud_Mental"]:
        # Valores enteros (spinbox)
        entrada = ttk.Spinbox(frame_campo, from_=0, to=24, textvariable=var, width=5)
        entrada.set(0)
    else:
        entrada = ttk.Entry(frame_campo, textvariable=var, width=22)

    entrada.pack(side="left", fill="x", expand=True)
    variables[campo] = var

# Botón de evaluación
btn_frame = ttk.Frame(form_frame)
btn_frame.grid(row=mid_point+1, column=0, columnspan=2, pady=20)
ttk_btn = ttk.Button(btn_frame, text="🔍 Realizar Evaluación", command=lambda: predecir())
ttk_btn.pack(pady=10)

# Resultados
result_frame = ttk.LabelFrame(content_frame, text="📊 Resultados de la Evaluación", padding=15)
result_frame.pack(side="right", fill="both", expand=True)

# Gráficos
graph_frame = ttk.Frame(result_frame)
graph_frame.pack(fill="both", expand=True, pady=(0, 20))

# Canvas para gráficos
canvas_container = ttk.Frame(graph_frame)
canvas_container.pack(fill="both", expand=True)

# Feedback
feedback_frame = ttk.LabelFrame(result_frame, text="📝 Recomendaciones", padding=15)
feedback_frame.pack(fill="both", expand=True)

feedback_text = tk.Text(feedback_frame, wrap="word", height=8,
                       font=("Arial", 11), bg="#fffde7", padx=10, pady=10)
feedback_text.pack(fill="both", expand=True)
feedback_text.config(state="disabled")

# Variables globales para gráficos
fig, ax = plt.subplots(figsize=(6, 4), dpi=80)
fig.subplots_adjust(left=0.15, bottom=0.15)
canvas = None

# Conversión sí/no a binario
def si_no_a_binario(valor):
    if isinstance(valor, str):
        return 1 if valor.strip().lower() == "sí" else 0 if valor.strip().lower() == "no" else valor
    return valor

# Función de predicción
def predecir():
    global canvas, fig, ax

    try:
        datos = {}
        for campo, var in variables.items():
            val = var.get()
            if campo in ["Afecta_Rendimiento_Academico", "Conflictos_Por_Redes_Sociales"]:
                val = si_no_a_binario(val)
            # Convertir a número si es posible
            try:
                val = float(val) if '.' in val else int(val)
            except:
                pass
            datos[campo] = val

        df = pd.DataFrame([datos])
        resultado = model.predict(df)
        resultado_dict = resultado.to_dict(orient='records')[0]

        prediccion = None
        for k, v in resultado_dict.items():
            k_limpio = re.sub(r'[^a-zA-Z0-9_]', '', k).lower()
            if 'predicted' in k_limpio or any(t.lower() in k_limpio for t in target_fields):
                prediccion = v
                break

        if prediccion is not None:
            mostrar_graficos(float(prediccion))
            mostrar_feedback(float(prediccion))
        else:
            salida = "\n".join(f"{k}: {v}" for k, v in resultado_dict.items())
            messagebox.showwarning("Predicción no encontrada", f"No se encontró una predicción.\nSalida:\n{salida}")
    except Exception as e:
        messagebox.showerror("Error", f"❌ Error al predecir:\n{str(e)}")

# Mostrar gráficos
def mostrar_graficos(pred):
    global canvas, fig, ax

    if canvas:
        canvas.get_tk_widget().destroy()

    fig, axs = plt.subplots(1, 2, figsize=(10, 4), dpi=80)
    fig.subplots_adjust(wspace=0.4)

    ax = axs[0]
    ax.bar(["Salud Mental"], [pred], color=get_color(pred))
    ax.set_ylim(0, 10)
    ax.set_ylabel("Puntaje (0-10)")
    ax.set_title("📊 Puntaje de Salud Mental")

    # Líneas de referencia
    ax.axhline(y=3, color='green', linestyle='--', alpha=0.5)
    ax.axhline(y=6, color='orange', linestyle='--', alpha=0.5)
    ax.axhline(y=8, color='red', linestyle='--', alpha=0.5)

    ax = axs[1]

    # Usamos variables que sí existen
    factores = ["Horas Uso (Promedio)", "Descanso (Calidad)", "Conflictos"]
    valores = [
        float(variables["Promedio_Horas_Diarias_Uso"].get()),
        10 - float(variables["Descanso"].get()),
        8 if variables["Conflictos_Por_Redes_Sociales"].get() == "Sí" else 2
    ]

    colores = [get_color(v) for v in valores]

    ax.barh(factores, valores, color=colores)
    ax.set_xlim(0, 10)
    ax.set_title("📈 Factores de Riesgo")
    ax.set_xlabel("Nivel de Riesgo")

    for i, v in enumerate(valores):
        ax.text(v + 0.2, i, f"{v:.1f}", color='black', va='center')

    canvas = FigureCanvasTkAgg(fig, master=canvas_container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# Función auxiliar para obtener color según puntaje
def get_color(puntaje):
    if puntaje <= 3:
        return "#4caf50"
    elif puntaje <= 6:
        return "#ffc107"
    elif puntaje <= 8:
        return "#ff9800"
    else:
        return "#f44336"

# Retroalimentación
def mostrar_feedback(puntaje):
    feedback_text.config(state="normal")
    feedback_text.delete(1.0, tk.END)

    color = get_color(puntaje)
    feedback_text.tag_configure("header", font=("Arial", 12, "bold"), foreground=color)
    feedback_text.insert(tk.END, f"Tu puntaje de salud mental es: {puntaje:.1f}/10\n\n", "header")

    if puntaje <= 3:
        feedback_text.insert(tk.END, "✅ Excelente salud mental. ¡Sigue con tus buenos hábitos!\n\n")
        recomendaciones = [
            "• Continúa manteniendo un equilibrio saludable entre tecnología y actividades offline",
            "• Practica actividades de mindfulness para mantener tu bienestar",
            "• Comparte tus hábitos saludables con amigos y familiares"
        ]
    elif puntaje <= 6:
        feedback_text.insert(tk.END, "⚠️ Estado mental aceptable, pero hay áreas de oportunidad\n\n")
        recomendaciones = [
            "• Reduce tu tiempo en redes sociales en 1 hora diaria",
            "• Establece horarios libres de dispositivos electrónicos",
            "• Practica técnicas de respiración cuando sientas estrés",
            "• Mejora tu higiene de sueño con rutinas consistentes"
        ]
    elif puntaje <= 8:
        feedback_text.insert(tk.END, "⚠️⚠️ Tu salud mental podría estar en riesgo. Necesitas cambios\n\n")
        recomendaciones = [
            "• Considera una desintoxicación digital durante al menos un día a la semana",
            "• Habla con un profesional de salud mental si la ansiedad persiste",
            "• Fomenta actividades físicas y sociales presenciales",
            "• Limita el uso de plataformas que generan ansiedad"
        ]
    else:
        feedback_text.insert(tk.END, "❌ Tu salud mental está en un nivel crítico. Busca ayuda profesional.\n\n")
        recomendaciones = [
            "• Consulta con un psicólogo o psiquiatra lo antes posible",
            "• No dudes en apoyarte en familiares y amigos",
            "• Considera reducir el uso de redes sociales drásticamente",
            "• Sigue un plan de tratamiento profesional"
        ]

    for r in recomendaciones:
        feedback_text.insert(tk.END, r + "\n")

    feedback_text.config(state="disabled")

ventana.mainloop()
