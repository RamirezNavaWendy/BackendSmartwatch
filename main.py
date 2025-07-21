from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from transformers import pipeline
from openai import OpenAI


app = FastAPI()

# Modelo de datos esperado desde el smartwatch
class Transcripcion(BaseModel):
    fecha: str
    texto: str


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Función de limpieza con IA
def limpiar_con_gpt(texto: str) -> str:
    print(" Enviando texto a OpenAI:", texto)
    prompt = f"Corrige este texto eliminando muletillas y mejorando su claridad:\n{texto}"

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




#Endpoint que recibe y procesa
@app.post("/recibir-clase/")
async def recibir_clase(datos: Transcripcion):
    texto_limpio = limpiar_con_gpt(datos.texto)


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

