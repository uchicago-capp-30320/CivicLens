from django.shortcuts import render # noqa: F401

# from .models import  # noqa: F401


def home(request):
    return render(request, "home.html")


def search_page(request):
    return render(request, "search_page.html")


def search_results(request):
    return render(request, "search_results.html")


def document(request):
    return render(request, "document.html")


def comment(request):
    return render(request, "comment.html")