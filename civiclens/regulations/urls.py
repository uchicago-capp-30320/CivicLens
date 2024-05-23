from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("learn/", views.learn, name="learn"),
    path("docs/<str:doc_id>", views.document, name="document"),
    path("search/", views.search_page, name="search"),
    path("search/results/", views.search_results, name="search_results"),
]

handler404 = views.handler404
