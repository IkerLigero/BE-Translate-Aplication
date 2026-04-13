from locust import HttpUser, task, between
# We import the individual function from our tasks folder
from tasks.translations import list_translations

class TranslationUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_list_translations(self):
        # We pass 'self' (the current user) to the function
        list_translations(self)