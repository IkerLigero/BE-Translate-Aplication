import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 1. Importamos la Base y los Modelos (Crucial para que SQLAlchemy los vea)
from app.db.base_class import Base
from app.models.user import User
from app.models.translation import Translation

# 2. Importamos la utilidad de hashing
from passlib.context import CryptContext

# Configuración rápida de hashing (por si no tienes el core/security listo aún)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 3. Configuración de conexión (Ajustada a tu docker-compose)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/tms_db"

async def recomponer():
    print("🚀 Iniciando recomposición total de la base de datos...")
    
    # Creamos el motor asíncrono
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # --- PASO 1: RECONSTRUIR TABLAS ---
    async with engine.begin() as conn:
        print("🔨 Borrando tablas antiguas (limpieza profunda)...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("🏗️ Creando tablas nuevas desde los modelos...")
        await conn.run_sync(Base.metadata.create_all)

    # --- PASO 2: INSERTAR USUARIO SEMILLA CON HASH ---
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        async with session.begin():
            print("👤 Generando usuario de prueba seguro...")
            
            password_plana = "password123"
            # Usamos el contexto de forma directa para evitar el bug del backend
            password_haseada = pwd_context.hash(password_plana)
            
            user = User(
                email="test@gmail.com", 
                hashed_password=str(password_haseada), # Forzamos a string
                is_active=True
            )
            session.add(user)
            
        print(f"✅ Usuario 'test@gmail.com' creado con hash: {password_haseada[:20]}...")

    await engine.dispose()
    print("\n✨ ¡Base de datos lista y reluciente! ✨")

if __name__ == "__main__":
    try:
        asyncio.run(recomponer())
    except Exception as e:
        print(f"\n❌ Error durante la recomposición: {e}")