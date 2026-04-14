from locust import HttpUser, task, between
# We import the individual function from our tasks folder
from tasks.translations import list_translations, create_translation,create_and_regenerate, create_and_get_status, create_and_download_pdf

class TranslationUser(HttpUser):
    wait_time = between(1, 2)

    # [Endpoint 1] List translations
    @task(5)
    def test_list_translations(self):
        list_translations(self)
    
    # [Endpoint 2] Create translation
    @task(2)
    def test_create(self):
        create_translation(self)
        
    # [Endpoint 3] Regenerate translation
    @task(1)
    def test_regen(self):
        create_and_regenerate(self)
    
    # [Endpoint 4] Get translation status
    @task(2)
    def test_get_status(self):
        create_and_get_status(self)

    # [Endpoint 5] Create and download PDF
    @task(2)
    def create_and_download_pdf(self):
        create_and_download_pdf(self)