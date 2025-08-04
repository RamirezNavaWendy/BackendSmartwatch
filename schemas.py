from typing import List, Optional
from pydantic import BaseModel

class TextoEntrada(BaseModel):
    texto: str


class Enlace(BaseModel):
    titulo: str
    url: str

class Transcripcion(BaseModel):
    titulo: str
    fecha: str
    texto: str
    idioma: str
    enlaces_recomendados: Optional[List[Enlace]] = None
    