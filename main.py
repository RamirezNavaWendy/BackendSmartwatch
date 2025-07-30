from fastapi import FastAPI
import uvicorn
from endpoints import router

app = FastAPI()
app.include_router(router)

#Arrancar el servidor
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 4000)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

