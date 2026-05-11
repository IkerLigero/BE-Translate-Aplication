import os
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import select
from app.models.translation import Translation  # Path checked based on your worker imports

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    # Esto te ayudará a debuguear si el problema persiste
    raise ValueError("CRÍTICO: La API Key de OpenAI no se encuentra en las variables de entorno.")

client = OpenAI(api_key=api_key)

# Function to get embedding for a given text
def get_embedding(text: str):
    """
    Convert text to a vector embedding using OpenAI's API.
    According to official docs, text-embedding-3-small is efficient and cost-effective.
    """
    # In case the text is empty or None
    if not text:
        return None

    # Clean text to improve embedding quality
    text = text.replace("\n", " ").strip()
    
    try:
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        # The response object follows the new Pydantic model structure
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


# Async function to search for similar translations based on cosine similarity
async def search_similar_translations(db, user_id: int, query_text: str, limit: int = 5):
    """
    1. Converts query to vector via OpenAI.
    2. Performs cosine similarity search via pgvector (<=> operator).
    3. Filters by user_id and active status.
    """
    # Convert the search term into a vector
    query_vector = get_embedding(query_text)
    
    if not query_vector:
        return []

    # Using pgvector's cosine_distance (<=>)
    # We filter by user, active status and ensure the record has an embedding
    stmt = (
        select(Translation)
        .where(
            Translation.user_id == user_id,
            Translation.is_active == True,
            Translation.embedding.isnot(None)
        )
        .order_by(Translation.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()