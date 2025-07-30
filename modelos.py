# modelos.py
from openai import OpenAI
import whisper
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_whisper = whisper.load_model("base")