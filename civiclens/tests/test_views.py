import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_active_docs(client):
    """Make sure document count is correct"""
    resp = client.get(reverse("search"))
    doc_facts = resp.context["doc_cmt_facts"]
    assert doc_facts["active_documents_count"] == 2


@pytest.mark.django_db
def test_average_comments(client):
    """Make sure average count is right"""
    resp = client.get(reverse("search"))
    doc_facts = resp.context["doc_cmt_facts"]
    assert doc_facts["avg_comments"] == 2


@pytest.mark.django_db
def test_num_docs(client):
    """Find right number of top documents"""
    resp = client.get(reverse("search"))
    doc_facts = resp.context["doc_cmt_facts"]
    assert len(doc_facts["top_commented_documents"]) == 1


@pytest.mark.django_db
def test_num_no_docs(client):
    """Assert active doc count math is correct"""
    resp_cont = client.get(reverse("search")).context
    doc_facts = resp_cont["doc_cmt_facts"]
    assert (
        doc_facts["active_documents_with_no_comments"]
        == doc_facts["active_documents_count"]
        - doc_facts["active_documents_with_comments"]
    )


@pytest.mark.django_db
def test_render_graph(client):
    """Make sure graph render for NLP pages"""
    graph_resp = client.get("/docs/HHS-OMH-2024-0004-0001").context
    nlp_object = graph_resp["document_info"]["nlp"]
    assert nlp_object.id == 308


@pytest.mark.django_db
def test_render_no_graph(client):
    """Assert no graph renders for pages w/o NLP"""
    no_graph_resp = client.get("/docs/BIS-2024-0003-0001").context
    nlp_object = no_graph_resp["document_info"]["nlp"]
    assert not nlp_object.id
