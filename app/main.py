from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router 

app = FastAPI(title="TMS - Translation Management System", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route setup - This includes ALL endpoints defined in api.py, which currently is just translations but can grow in the future.
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}