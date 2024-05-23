import lxml.html
import pytest
import requests
from django.urls import reverse
from regulations.models import Document


def get_page_links(resp_content, client):
    links = lxml.html.fromstring(resp_content).xpath("//a/@href")
    for link in links:
        print(link)
        resp = None
        if "results" in str(link):
            continue
        elif link.startswith("/"):
            resp = client.get(str(link))
        else:
            resp = requests.get(str(link))
        yield resp


@pytest.mark.django_db
def test_home_links(client):
    resp_content = client.get(reverse("home")).content
    for resp in get_page_links(resp_content, client):
        assert resp.status_code == 200


@pytest.mark.django_db
def test_doc_links(client):
    resp = client.get("/docs/HHS-OMH-2024-0004-0001")
    for link in get_page_links(resp.content, client):
        assert link.status_code == 200


@pytest.mark.django_db
def test_search_links(client):
    resp = client.get(reverse("search"))
    for link in get_page_links(resp.content, client):
        assert link.status_code == 200


@pytest.mark.django_db()
def test_hit_db():
    """Make sure test database is working"""
    doc = Document.objects.get(id="HHS-OMH-2024-0004-0001")
    assert doc.id == "HHS-OMH-2024-0004-0001"


@pytest.mark.django_db
def test_home_renders(client):
    """Home renders"""
    full_url = "/"
    response = client.get(full_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_404(client):
    full_url = "/docs/FWS-HQ-NWRS-2022-0106-35375"
    response = client.get(full_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_document_renders(client):
    """Document summary renders for random document"""
    full_url = "/docs/HHS-OMH-2024-0004-0001"
    response = client.get(full_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_search_renders(client):
    """Search renders"""
    full_url = "/search/"
    response = client.get(full_url)
    assert response.status_code == 200
