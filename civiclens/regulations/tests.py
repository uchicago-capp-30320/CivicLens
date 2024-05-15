from django.test import TestCase  # noqa: F401
from django.test import Client


# from regulations.forms import Search

# run tests by the following line of code:
# python civiclens/manage.py test --keepdb

client = Client()


class PagesRenderTestCase(TestCase):
    def setUp(self):
        self.root_url = "/regulations"

    def test_home_renders(self):
        """Home renders"""
        full_url = self.root_url + "/"
        response = client.get(full_url)
        self.assertEqual(response.status_code, 200)

    def test_search_renders(self):
        """Search renders"""
        full_url = self.root_url + "/search/"
        response = client.get(full_url)
        self.assertEqual(response.status_code, 200)

    def test_search_results_renders(self):
        """Search results renders for random phrase"""
        full_url = self.root_url + "/search/results/?q=brocolli+rabe+sandwich"
        response = client.get(full_url)
        self.assertEqual(response.status_code, 200)

    def test_document_renders(self):
        """Document summary renders for random document"""
        full_url = self.root_url + "/docs/FWS-HQ-NWRS-2022-0106-35375"
        response = client.get(full_url)
        self.assertEqual(response.status_code, 200)
