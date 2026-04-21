import time

# Helper to avoid repeating the base name and keep stats clean
POST_NAME = "POST /api/v1/translations"

def list_translations(user):
    url = f"{user.api_prefix}/translations"
    # Here we don't use 'with', so catch_response is NOT needed
    user.client.get(url, name="GET /api/v1/translations")

def create_translation(user):
    url = f"{user.api_prefix}/translations"
    payload = {
        "text_to_translate": "Standard performance test text",
        "pdf_lang": "en", "source_lang": "en", "target_lang": "es"
    }
    # Here we don't use 'with', so catch_response is NOT needed
    user.client.post(url, json=payload, name=POST_NAME)

def create_and_regenerate(user):
    url = f"{user.api_prefix}/translations"
    payload = {
        "text_to_translate": "Text for regeneration test",
        "pdf_lang": "es", "source_lang": "en", "target_lang": "es"
    }
    
    # FIX: Added catch_response=True because we use 'with' to get the ID
    with user.client.post(url, json=payload, name=POST_NAME, catch_response=True) as response:
        if response.status_code in [200, 201]:
            t_id = response.json().get("id")
            gen_url = f"{url}/{t_id}/generate"
            user.client.post(gen_url, name="POST /api/v1/translations/{id}/generate")
            response.success()
        else:
            response.failure(f"Creation for regen failed: {response.status_code}")

def create_and_get_status(user):
    url = f"{user.api_prefix}/translations"
    payload = {"text_to_translate": "Status check test", "pdf_lang": "en", "source_lang": "en", "target_lang": "es"}
    
    # FIX: Added catch_response=True because we use 'with' to get the ID
    with user.client.post(url, json=payload, name=POST_NAME, catch_response=True) as response:
        if response.status_code in [200, 201]:
            t_id = response.json().get("id")
            status_url = f"{url}/{t_id}"
            user.client.get(status_url, name="GET /api/v1/translations/{id}")
            response.success()
        else:
            response.failure(f"Creation for status failed: {response.status_code}")

def create_and_download_pdf(user):
    url = f"{user.api_prefix}/translations"
    payload = {"text_to_translate": "PDF download test", "pdf_lang": "en", "source_lang": "en", "target_lang": "es"}
    
    # FIX: Added catch_response=True because we use 'with' to get the ID
    with user.client.post(url, json=payload, name=POST_NAME, catch_response=True) as response:
        if response.status_code in [200, 201]:
            t_id = response.json().get("id")
            response.success()
            
            # Wait 0.5s to let the worker process
            time.sleep(0.5)
            
            pdf_url = f"{url}/{t_id}/pdf"
            with user.client.get(pdf_url, name="GET /api/v1/translations/{id}/pdf", catch_response=True) as pdf_res:
                if pdf_res.status_code in [200, 202]:
                    pdf_res.success()
                else:
                    pdf_res.failure(f"Download error: {pdf_res.status_code}")
        else:
            response.failure(f"Creation for download failed: {response.status_code}")