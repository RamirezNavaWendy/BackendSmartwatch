from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
import os, json, tempfile
from bson import ObjectId
from modelos import client
from schemas import TextoEntrada
from mongo import fs
from logica import generar_contenido_enriquecido


from modelos import model_whisper
from logica import limpiar_con_gpt, generar_titulo
from schemas import Transcripcion 
from latexConverter import procesar_transcripcion
from mongo import db

router = APIRouter()
TRANSCRIPCIONES_DIR = "transcripciones"
os.makedirs(TRANSCRIPCIONES_DIR, exist_ok=True)

coleccion = db["audios_transcritos"]

#  Endpoint para transcribir audio con Whisper
@router.post("/whisper-transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

    try:

        with open(temp_path, "wb") as f:
            f.write(await file.read())

        result = model_whisper.transcribe(temp_path, language=None)
        texto_raw = result["text"]
        idioma = result.get("language", "en")
        print(f" Idioma detectado por Whisper: {idioma}")

        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        texto_limpio = limpiar_con_gpt(texto_raw,idioma)
        titulo_raw = generar_titulo(texto_limpio,idioma)
        titulo_limpio = titulo_raw.strip('"')

        contenido_enriquecido = generar_contenido_enriquecido(texto_limpio, idioma)

        metadata = {
            "titulo": titulo_limpio,
            "fecha": fecha,
            "texto_limpio": texto_limpio,
            "idioma": idioma,
            "contenido_enriquecido": contenido_enriquecido
        }

        mongo_id = procesar_transcripcion(metadata)

        
        if mongo_id in ["error", "compilacion_fallida", "archivo_no_encontrado", "archivo_vacio"]:
            raise HTTPException(status_code=500, detail="Error al generar y guardar el PDF.")

        return {
            "mensaje": "PDF generado y guardado exitosamente",
            "mongo_pdf_id": mongo_id
        }

    except Exception as e:
        return {"error": f"Error en transcripción o generación de PDF: {str(e)}"}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# Endpoint para recibir texto limpio y generar título
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

# Endpoint para generar y guardar PDF en Mongo
@router.post("/guardar-pdf/")
def guardar_pdf_endpoint(data: Transcripcion):
    metadata = {
        "titulo": data.titulo,
        "fecha": data.fecha,
        "texto_limpio": data.texto,
        "idioma": data.idioma,
        "enlaces_recomendados": data.enlaces_recomendados or []
    }

    mongo_id = procesar_transcripcion(metadata)

    if mongo_id == "contenido_invalido":
        raise HTTPException(status_code=400, detail="Contenido LaTeX inválido. Revisa el texto generado.")

    if mongo_id == "compilacion_fallida":
        raise HTTPException(status_code=500, detail="LaTeX falló al compilar el PDF.")

    if mongo_id == "pdf_invalido":
        raise HTTPException(status_code=500, detail="El PDF generado está vacío o corrupto.")

    if mongo_id == "error":
        raise HTTPException(status_code=500, detail="Error al guardar el PDF en MongoDB.")

    return {
        "mensaje": "PDF generado y guardado exitosamente",
        "mongo_pdf_id": mongo_id
    }


# Endpoint para verificar estado de Mongo
@router.get("/mongo-status/")
def mongo_status():
    try:
        colecciones = db.list_collection_names()
        return {"colecciones": colecciones}
    except Exception as e:
        return {"error": str(e)}


@router.get("/ver-pdfs/")
def ver_pdfs():
    try:
        archivos = fs.find().sort("uploadDate", -1).limit(5)
        resultado = []
        for archivo in archivos:
            resultado.append({
                "filename": archivo.filename,
                "fecha": archivo.uploadDate.isoformat(),
                "id": str(archivo._id),
                "metadata": archivo.metadata
            })
        return resultado
    except Exception as e:
        return {"error": str(e)}


@router.post("/detectar-tema/")
async def detectar_tema(datos: TextoEntrada):
    prompt = f"""Analiza el siguiente texto y responde con una breve descripción del tema principal. Sé conciso y específico.

Texto:
\"\"\"{datos.texto}\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    tema = response.choices[0].message.content.strip()
    return {"tema": tema}




