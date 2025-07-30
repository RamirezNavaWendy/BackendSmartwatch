from pydantic import BaseModel

class Transcripcion(BaseModel):
    fecha: str
    texto: str