import time
import os

# Nota: Asegúrate de que la ruta de importación sea correcta según tu estructura
# Si este archivo está en locust/tasks/, quizás necesites ajustar el sys.path 
# o importar directamente si el entorno lo permite.
# from core.storage import s3_client 

def list_translations(user):
    """
    Endpoint 1: GET /translations
    Lista todas las traducciones existentes.
    """
    with user.client.get("/translations", name="GET /translations", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Error {response.status_code}: {response.text}")

def create_translation(user):
    """
    Endpoint 2: POST /translations
    Crea una nueva traducción con el payload completo requerido (4 campos).
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
    Crea una traducción y solicita su regeneración.
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
            
            # Agrupamos por nombre fijo para evitar filas infinitas en Locust
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
    Consulta los detalles/estado de una traducción específica.
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
    Simula el flujo de un usuario que crea un documento y luego descarga la URL firmada.
    """
    payload = {
        "text_to_translate": "Generando PDF para test de URL firmada",
        "pdf_lang": "en",
        "source_lang": "en",
        "target_lang": "es"
    }
    
    # 1. Crear
    with user.client.post("/translations", json=payload, name="POST /translations (for PDF)", catch_response=True) as response:
        if response.status_code in [200, 201]:
            translation_id = response.json().get("id")
            
            # Simulamos tiempo de espera para que el worker procese
            time.sleep(1)
            
            # 2. Obtener la Pre-signed URL
            with user.client.get(
                f"/translations/{translation_id}/pdf", 
                name="GET /translations/{id}/pdf (Presigned)", 
                catch_response=True
            ) as pdf_response:
                if pdf_response.status_code == 200:
                    # Validamos que el backend nos da el JSON con la URL
                    data = pdf_response.json()
                    if "download_url" in data:
                        pdf_response.success()
                    else:
                        pdf_response.failure("200 OK but 'download_url' missing in JSON")
                elif pdf_response.status_code == 202:
                    pdf_response.success() # Aceptamos "todavía procesando" como éxito de flujo
                else:
                    pdf_response.failure(f"PDF error: {pdf_response.status_code}")
        else:
            response.failure(f"Initial create failed: {response.text}")