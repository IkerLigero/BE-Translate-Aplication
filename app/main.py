from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router 

app = FastAPI(title="TMS - Translation Management System", redirect_slashes=False)

# Configuramos CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos el router único que ya trae toda la estructura
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}

# Eliminamos startup_event con Base.metadata.create_all 
# porque ahora gestionas la DB con Alembic.