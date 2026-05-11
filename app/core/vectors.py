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
    1. Generate an embedding for the query text.
    2. Use SQLAlchemy to query the database for translations of the user that have an embedding.
    3. Calculate cosine similarity between the query embedding and the stored embeddings.
    4. Order results by similarity and return the top matches.
    """
    
    # Step 1: Get the embedding for the query text
    query_vector = get_embedding(query_text)
    if not query_vector:
        return []

    # Step 2: Calculate cosine similarity between the query embedding and the stored embeddings
    # Calculate the similarity: 1 - (vector <=> column)
    # Multiply by 100 to get a percentage.
    similarity_score = (1 - Translation.embedding.cosine_distance(query_vector)).label("similarity")

    # Step 3: Query the database for translations that belong to the user, are active, and have an embedding
    stmt = (
        select(Translation, similarity_score) # Select the Translation and its similarity score
        .where(
            Translation.user_id == user_id,
            Translation.is_active == True,
            Translation.embedding.isnot(None)
        )
        .order_by(Translation.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    
    # Step 4: Execute the query and return results
    result = await db.execute(stmt)
    # When returning Translation and similarity, SQLAlchemy returns tuples.
    return result.all()