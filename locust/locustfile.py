from locust import HttpUser, task, between
import uuid
from tasks.translations import (
    list_translations, 
    create_translation, 
    create_and_regenerate, 
    create_and_get_status, 
    create_and_download_pdf
)

class TranslationUser(HttpUser):
    wait_time = between(1, 2)
    api_prefix = "/api/v1"

    def on_start(self):
        """ 
        Registers and authenticates a unique user for this session.
        """
        self.email = f"test_{uuid.uuid4()}@example.com"
        self.password = "testpassword123"
        
        # Create User
        create_payload = {"email": self.email, "password": self.password, "is_active": True}
        self.client.post(f"{self.api_prefix}/users", json=create_payload, name="[Setup] User Registration")

        # Login
        login_data = {"username": self.email, "password": self.password}
        with self.client.post(
            f"{self.api_prefix}/login", 
            data=login_data, 
            name="[Setup] User Login", 
            catch_response=True
        ) as response:
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {token}"})
                response.success()
            else:
                response.failure(f"Setup login failed: {response.status_code}")

    @task(5)
    def test_list(self):
        list_translations(self)
    
    @task(3) # Increased weight: creation is the core of the app
    def test_create_only(self):
        create_translation(self)
        
    @task(1)
    def test_regen_flow(self):
        create_and_regenerate(self)
    
    @task(2)
    def test_status_flow(self):
        create_and_get_status(self)

    @task(2)
    def test_download_flow(self):
        create_and_download_pdf(self)