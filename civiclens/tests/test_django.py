import pytest


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
    full_url = "/docs/CMS-2024-0131-0025"
    response = client.get(full_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_search_renders(client):
    """Search renders"""
    full_url = "/search/"
    response = client.get(full_url)
    assert response.status_code == 200
