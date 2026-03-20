from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import translations

# Disable redirect_slashes to strictly avoid trailing slashes
app = FastAPI(title="TMS - Translation Management System", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router without trailing slash in prefix
app.include_router(
    translations.router, 
    prefix="/translations", 
    tags=["Translations"]
)

@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}