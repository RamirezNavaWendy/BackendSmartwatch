from modelos import client

# Función de limpieza con IA - MULTIIDIOMA
def limpiar_con_gpt(texto: str, idioma: str = "en") -> str:
    print(f" Enviando texto a OpenAI (idioma: {idioma}):", texto[:100] + "...")
    
    # Prompts en diferentes idiomas
    prompts = {
        'es': f"Corrige este texto eliminando muletillas y mejorando su claridad. Si ya es bastante claro y coherente déjalo tal cual únicamente eliminando las muletillas y ruidos inútiles:\n{texto}",
        'en': f"Clean this text by removing filler words and improving clarity. If it's already clear and coherent, leave it as is, only removing filler words and unnecessary noise:\n{texto}"
    }
    
    prompt = prompts.get(idioma, prompts['en'])  # Default a inglés si no existe el idioma

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        texto_limpio = respuesta.choices[0].message.content.strip()
        print(" Respuesta de OpenAI:", texto_limpio[:100] + "...")
        return texto_limpio
    except Exception as e:
        print(" Error al llamar a OpenAI:", str(e))
        return "Error al procesar el texto con OpenAI"

# Genera un título para el texto limpio - MULTIIDIOMA
def generar_titulo(texto_limpio: str, idioma: str = "en") -> str:
    
    # Prompts para generar títulos en diferentes idiomas
    prompts = {
        'es': f"Genera un título académico breve y descriptivo para el siguiente texto:\n\n{texto_limpio}",
        'en': f"Generate a brief and descriptive academic title for the following text:\n\n{texto_limpio}"
    }
    
    prompt = prompts.get(idioma, prompts['en'])  # Default a inglés
    
    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        modelo_respuesta = respuesta.choices[0].message.content.strip()
        print(f" Título generado ({idioma}):", modelo_respuesta)
        return modelo_respuesta
    except Exception as e:
        print(" Error al llamar a OpenAI:", str(e))
        return "Error al procesar el texto con OpenAI"

# Genera una versión corta y válida del título para usar como nombre de archivo
def generar_titulo_corto(titulo_largo: str) -> str:
    import re
    # Elimina caracteres no válidos para nombres de archivo
    limpio = re.sub(r'[\\/*?:"<>|]', '', titulo_largo)
    # Recorta a 30 caracteres y elimina espacios finales
    return limpio[:30].strip()

# Genera contenido enriquecido a partir del texto limpio - MULTIIDIOMA
def generar_contenido_enriquecido(texto_limpio: str, idioma: str = "en") -> str:
    print(f" Generando contenido enriquecido (idioma: {idioma})...")

    prompts = {
        'es': f"""A partir del siguiente texto, genera un contenido enriquecido que incluya:

- Un resumen breve (100 palabras)
- 5 ideas clave
- 3 preguntas de reflexión

Texto:
\"\"\"{texto_limpio}\"\"\"
""",
        'en': f"""Based on the following text, generate enriched content including:

- A brief summary (100 words)
- 5 key ideas
- 3 reflective questions

Text:
\"\"\"{texto_limpio}\"\"\"
"""
    }

    prompt = prompts.get(idioma, prompts['en'])

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        contenido = respuesta.choices[0].message.content.strip()
        print(" Contenido enriquecido generado:", contenido[:100] + "...")
        return contenido
    except Exception as e:
        print(" Error al generar contenido enriquecido:", str(e))
        return ""
