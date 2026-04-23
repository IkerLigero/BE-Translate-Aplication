import uuid
from locust import HttpUser, task, between
from tasks.translations import (
    list_translations, 
    create_translation, 
    create_and_regenerate, 
    create_and_get_status, 
    create_and_download_pdf
)

# Logic for user setup and tasks is encapsulated within the TranslationUser class, which inherits from HttpUser.
class TranslationUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = between(1, 2)
    api_prefix = "/api/v1"

    def on_start(self):
        """ 
        Executed when a simulated user starts. It handles user registration and login to obtain a JWT token for authenticated requests.
        This setup ensures that all subsequent tasks are performed with a valid user session.
        """
        self.email = f"test_{uuid.uuid4()}@example.com"
        self.password = "testpassword123"
        
        # 1. User Registration: We need to create a user before we can log in and perform tasks.
        create_payload = {
            "email": self.email, 
            "password": self.password, 
            "is_active": True,
            "registration_secret": "admin"  # Secret password [In future, consider using an environment variable for this]
        }
        
        # We use 'with' to capture the response and determine if the registration was successful, which is crucial for the next step (login).
        with self.client.post(
            f"{self.api_prefix}/users", 
            json=create_payload, 
            name="[Setup] User Registration",
            catch_response=True
        ) as reg_response:
            if reg_response.status_code == 200:
                reg_response.success()
            else:
                reg_response.failure(f"User registration failed: {reg_response.status_code} - {reg_response.text}")
                return # If registration fails, do not attempt login

        # 2. Login to obtain JWT token
        login_data = {
            "username": self.email, 
            "password": self.password
        }
        with self.client.post(
            f"{self.api_prefix}/login", 
            data=login_data, 
            name="[Setup] User Login", 
            catch_response=True
        ) as login_response:
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                # Inject the token into the headers for all future requests
                self.client.headers.update({"Authorization": f"Bearer {token}"})
                login_response.success()
            else:
                login_response.failure(f"Login failed: {login_response.status_code}")

    # --- USER TASKS (Indented within the class) ---
    # This resolves the "No tasks defined" error

    @task(5)
    def test_list(self):
        """List all user translations"""
        list_translations(self)
    
    @task(3)
    def test_create_only(self):
        """Create a simple translation"""
        create_translation(self)
        
    @task(1)
    def test_regen_flow(self):
        """Create a translation and force its regeneration"""
        create_and_regenerate(self)
    
    @task(2)
    def test_status_flow(self):
        """Create a translation and check its status"""
        create_and_get_status(self)

    @task(2)
    def test_download_flow(self):
        """Create a translation and attempt to download the PDF"""
        create_and_download_pdf(self)