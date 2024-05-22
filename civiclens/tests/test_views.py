import pytest
from django.urls import reverse


# home page
# do names equal the right names
# is the search logic request
# test if the regulations link is the correct link and leads to 200
# look for 'if comments_nlp'
# link works for Federal register


@pytest.mark.django_db
def test_active_docs(client):
    resp = client.get(reverse("search"))
    assert resp.context["active_documents_count"] == 2


@pytest.mark.django_db
def test_average_comments(client):
    resp = client.get(reverse("search"))
    assert resp.context["avg_comments"] == 2


@pytest.mark.django_db
def test_num_docs(client):
    resp = client.get(reverse("search"))
    assert len(resp.context["top_commented_documents"]) == 1


@pytest.mark.django_db
def test_num_no_docs(client):
    resp_cont = client.get(reverse("search")).context
    assert (
        resp_cont["active_documents_with_no_comments"]
        == resp_cont["active_documents_count"]
        - resp_cont["active_documents_with_comments"]
    )


@pytest.mark.django_db
def test_render_graph(client):
    graph_resp = client.get("/docs/HHS-OMH-2024-0004-0001").context
    no_graph_resp = client.get("/docs/BIS-2024-0003-0001").context

    assert "nlp" in graph_resp and "nlp" not in no_graph_resp
