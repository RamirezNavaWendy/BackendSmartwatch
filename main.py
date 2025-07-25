from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
from datetime import datetime
from transformers import pipeline
from openai import OpenAI
import uvicorn
import os
import json
import tempfile
import whisper



app = FastAPI()

# Cargar modelo Whisper
model_whisper = whisper.load_model("base")
TRANSCRIPCIONES_DIR = "transcripciones"
os.makedirs(TRANSCRIPCIONES_DIR, exist_ok=True)

# Modelo de datos esperado desde el smartwatch
class Transcripcion(BaseModel):
    fecha: str
    texto: str

#Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

#Endpoint que recibe y procesa
@app.post("/recibir-clase/")
async def recibir_clase(datos: Transcripcion):
    texto_limpio = limpiar_con_gpt(datos.texto)
    titulo_raw = generar_titulo(texto_limpio)
    titulo_limpio = titulo_raw.strip('"')

    return {
        "estado": "procesado",
        "fecha": datos.fecha,
        "original": datos.texto,
        "limpio": texto_limpio,
        "titulo": titulo_limpio
    }


# Endpoint para transcribir audio con Whisper
@app.post("/whisper-transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        result = model_whisper.transcribe(temp_path, language=None)
        texto_raw = result["text"]
        idioma = result.get("language", "en")
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Limpieza con GPT
        texto_limpio = limpiar_con_gpt(texto_raw)

        # Título generado
        titulo_raw = generar_titulo(texto_limpio)
        titulo_limpio = titulo_raw.strip('"')

        # Guardar transcripción cruda
        json_data = {
            "fecha": fecha,
            "original": texto_raw,
            "limpio": texto_limpio,
            "idioma": idioma,
            "titulo": titulo_limpio
        }

        json_filename = f"transcripcion_{fecha}.json"
        json_path = os.path.join(TRANSCRIPCIONES_DIR, json_filename)

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        return json_data

    except Exception as e:
        return {"error": f"Error en transcripción o limpieza: {str(e)}"}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


#Arrancar el servidor
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 4000)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

