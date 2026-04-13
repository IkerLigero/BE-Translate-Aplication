
from app.models.translation import Translation


def list_translations(user):
    """
    Refactored task for Endpoint 1: GET /translations
    We use 'user' as an argument to access the HttpUser client.
    """
    with user.client.get("/translations", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Failed to list translations: {response.status_code}")