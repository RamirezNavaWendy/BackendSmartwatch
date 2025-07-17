from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
#from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


app = FastAPI()

# Modelo de datos esperado desde el smartwatch
class Transcripcion(BaseModel):
    fecha: str
    texto: str

# Carga del modelo FLAN-T5
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

# Función de limpieza con IA
def limpiar_con_flan(texto: str) -> str:
    instruccion = f"Corrige y mejora este texto: {texto}"
    inputs = tokenizer(instruccion, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=512)
    texto_limpio = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return texto_limpio


#Endpoint que recibe y procesa
@app.post("/recibir-clase/")
async def recibir_clase(datos: Transcripcion):
    texto_limpio = limpiar_con_flan(datos.texto)

    return {
        "estado": "procesado",
        "fecha": datos.fecha,
        "original": datos.texto,
        "limpio": texto_limpio
    }


#Arrancar el servidor
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 4000)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

