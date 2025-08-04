from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv
import os

# Carga las variables del archivo .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Conexión a Mongo Atlas
client = MongoClient(MONGO_URI)

# Selecciona la base de datos
db = client["BdTextFlow"]

# Inicializa GridFS para guardar PDFs
fs = gridfs.GridFS(db)