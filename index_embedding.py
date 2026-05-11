import psycopg2
import json
from openai import OpenAI
import os

# --- Configuration ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Docker database configuration
DB_CONFIG = {
    "dbname": "tms_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

def update_embeddings():
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Conexión exitosa a PostgreSQL.")

        # 1. Select original_texts without embedding
        query_select = """
            SELECT id, original_text 
            FROM translations 
            WHERE embedding IS NULL AND original_text IS NOT NULL;
        """
        cursor.execute(query_select)
        filas = cursor.fetchall()

        if not filas:
            print("No pending translations found.")
            return

        print(f"Translations found: {len(filas)}. Processing...")

        # 2. Generate the embedding for each original_text using OpenAI API
        for id_fila, texto in filas:
            try:
                # Skip if the text is empty or too short
                if not texto or len(texto.strip()) == 0:
                    continue

                # Generate embedding using OpenAI API
                response = client.embeddings.create(
                    input=texto,
                    model="text-embedding-3-small"
                )
                vector = response.data[0].embedding

                # 3. Save in the 'vector' column
                # Since it's pgvector, we pass the list directly, Postgres handles it
                query_update = "UPDATE translations SET embedding = %s WHERE id = %s"
                cursor.execute(query_update, (vector, id_fila))
                
                conn.commit()
                print(f"✨ ID {id_fila} indexed successfully.")

            except Exception as e:
                print(f"❌ Error in ID {id_fila}: {e}")
                conn.rollback()

    except Exception as error:
        print(f"Critical error: {error}")
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    update_embeddings()