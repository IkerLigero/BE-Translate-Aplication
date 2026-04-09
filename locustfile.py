from locust import HttpUser, task, between

# This is a simple Locust test file to simulate load on the two endpoints we created: the sync and async translation list endpoints.
class TranslationUser(HttpUser):
    wait_time = between(1, 2) 

    @task
    def test_sync(self):
        self.client.get("/translations/sync-list")

    @task
    def test_async(self):
        self.client.get("/translations/async-list")