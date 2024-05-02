from django.urls import path # noqa: F401

from . import views # noqa: F401

urlpatterns = [
    path("", views.home, name="home"),
    path("docs/<str:doc_id>", views.document, name="document"),
    path("search/", views.search_page, name="search"),
    path("search/results/", views.search_results, name="search_results"),
    path("docs/<str:doc_id>/comment/", views.comment, name="comment"),   
]