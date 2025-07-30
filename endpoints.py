from fastapi import APIRouter, UploadFile, File
from datetime import datetime
import os, json, tempfile

from modelos import model_whisper
from logica import limpiar_con_gpt, generar_titulo
from schemas import Transcripcion

router = APIRouter()

TRANSCRIPCIONES_DIR = "transcripciones"
os.makedirs(TRANSCRIPCIONES_DIR, exist_ok=True)

# Endpoint para transcribir audio con Whisper
@router.post("/whisper-transcribe/")
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

#Endpoint que recibe y procesa
@router.post("/recibir-clase/")
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