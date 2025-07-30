from modelos import client

# Función de limpieza con IA
def limpiar_con_gpt(texto: str) -> str:
    print(" Enviando texto a OpenAI:", texto)
    prompt = f"Corrige este texto eliminando muletillas y mejorando su claridad, si ya es bastante claro y coherente dejalo tal cual únicamente eliminando las muletillas y ruidos inutiles:\n{texto}"

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        texto_limpio = respuesta.choices[0].message.content.strip()
        print(" Respuesta de OpenAI:", texto_limpio)
        return texto_limpio
    except Exception as e:
        print(" Error al llamar a OpenAI:", str(e))
        return "Error al procesar el texto con OpenAI"

#Genera un titulo para el texto limpio
def generar_titulo(texto_limpio):
    prompt = f"Genera un título académico breve y descriptivo para el siguiente texto:\n\n{texto_limpio}"
    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        modelo_respuesta = respuesta.choices[0].message.content.strip()
        print(" Respuesta de OpenAI:", modelo_respuesta)
        return modelo_respuesta
    except Exception as e:
        print(" Error al llamar a OpenAI:", str(e))
        return "Error al procesar el texto con OpenAI"
