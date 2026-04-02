from locust import HttpUser, task, between

class TranslationUser(HttpUser):
    wait_time = between(1, 2) 

    @task
    def test_sync(self):
        # La barra inicial es importante si el Host no la tiene
        self.client.get("/translations/sync-list")

    @task
    def test_async(self):
        self.client.get("/translations/async-list")