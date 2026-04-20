import time
import os


def list_translations(user):
    """
    Endpoint 1: GET /translations
    List all existing translations for the authenticated user.
    """
    with user.client.get("/translations", name="GET /translations", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Error {response.status_code}: {response.text}")

def create_translation(user):
    """
    Endpoint 2: POST /translations
    Create a new translation with the complete required payload (4 fields).
    """
    payload = {
        "text_to_translate": "Texto de prueba para carga asíncrona",
        "pdf_lang": "en",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    with user.client.post("/translations", json=payload, name="POST /translations", catch_response=True) as response:
        if response.status_code in [200, 201]:
            response.success()
        else:
            response.failure(f"Error {response.status_code}: {response.text}")

def create_and_regenerate(user):
    """
    Endpoint 3: POST /translations/{id}/generate
    Create a translation and request its regeneration.
    """
    payload = {
        "text_to_translate": "Texto para forzar regeneración",
        "pdf_lang": "es",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    with user.client.post("/translations", json=payload, name="POST /translations (for regen)", catch_response=True) as response:
        if response.status_code in [200, 201]:
            translation_id = response.json().get("id")
            
            # Group by fixed name to avoid infinite queues in Locust
            with user.client.post(
                f"/translations/{translation_id}/generate", 
                name="POST /translations/{id}/generate", 
                catch_response=True
            ) as gen_response:
                if gen_response.status_code == 200:
                    gen_response.success()
                else:
                    gen_response.failure(f"Regen failed: {gen_response.status_code}")
        else:
            response.failure(f"Initial create failed: {response.text}")

def create_and_get_status(user):
    """
    Endpoint 4: GET /translations/{id}
    Check the details/status of a specific translation.
    """
    payload = {
        "text_to_translate": "Verificando estado de la traducción",
        "pdf_lang": "en",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    with user.client.post("/translations", json=payload, name="POST /translations (for status)", catch_response=True) as response:
        if response.status_code in [200, 201]:
            translation_id = response.json().get("id")
            
            with user.client.get(
                f"/translations/{translation_id}", 
                name="GET /translations/{id}", 
                catch_response=True
            ) as get_response:
                if get_response.status_code == 200:
                    get_response.success()
                else:
                    get_response.failure(f"Get status failed: {get_response.status_code}")
        else:
            response.failure(f"Initial create failed: {response.text}")

def create_and_download_pdf(user):
    """
    Endpoint 5: GET /translations/{id}/pdf (Pre-signed URL)
    Simulate the flow of a user who creates a document and then downloads the signed URL.
    """
    payload = {
        "text_to_translate": "Generando PDF para test de URL firmada",
        "pdf_lang": "en",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    # Step 1: Create the translation
    with user.client.post("/translations", json=payload, name="POST /translations (for PDF)", catch_response=True) as response:
        if response.status_code in [200, 201]:
            translation_id = response.json().get("id")
            
            # Simulate user waiting for the PDF to be generated (since it's async, we might need to wait a bit before the PDF is ready)
            time.sleep(1)
            
            # Step 2: Get the Pre-signed URL
            with user.client.get(
                f"/translations/{translation_id}/pdf", 
                name="GET /translations/{id}/pdf (Presigned)", 
                catch_response=True
            ) as pdf_response:
                if pdf_response.status_code == 200:
                    # Validate that the backend provides the JSON with the URL
                    data = pdf_response.json()
                    if "download_url" in data:
                        pdf_response.success()
                    else:
                        pdf_response.failure("200 OK but 'download_url' missing in JSON")
                elif pdf_response.status_code == 202:
                    pdf_response.success() # Accept "still processing" as a successful flow
                else:
                    pdf_response.failure(f"PDF error: {pdf_response.status_code}")
        else:
            response.failure(f"Initial create failed: {response.text}")