from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router 

app = FastAPI(title="TMS - Translation Management System", redirect_slashes=False)

# CORS configuration - adjust origins as needed for security in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with versioning prefix
app.include_router(api_router, prefix="/api/v1")

# Root endpoint for health check or welcome message
@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}
