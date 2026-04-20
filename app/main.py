from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router 
from app.models.user import User 
from app.models.translation import Translation
from app.db.base_class import Base
from app.db.session import async_engine as engine
from app.api.endpoints import login, users

app = FastAPI(title="TMS - Translation Management System", redirect_slashes=False)
app.include_router(login.router, tags=["Auth"]) 
app.include_router(users.router, prefix="/users", tags=["Usuarios"])
app.include_router(api_router)
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

# Database initialization - This will create the tables in the database based on the models defined (User and Translation) when the app starts.
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # This line creates all the tables in the database based on the models defined in Base (which includes User and Translation).
        # It ensures that the database schema is ready when the application starts.
        await conn.run_sync(Base.metadata.create_all)
    print("Base de datos sincronizada!")