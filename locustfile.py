from locust import HttpUser, task, between

# This is a simple Locust test file to simulate load on the two endpoints we created: the sync and async translation list endpoints.
class TranslationUser(HttpUser):
    wait_time = between(1, 2) # Simulate a user waiting between 1 and 2 seconds between requests

    # This task will hit the synchronous endpoint that lists translations
    @task
    def test_async(self):
        self.client.get("/translations")