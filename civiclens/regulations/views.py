from django.shortcuts import render, redirect  # noqa: F401
from .forms import Search

# from .models import  # noqa: F401


def home(request):
    return render(request, "home.html")


def search_page(request):        
    return render(request, "search_page.html")


def search_results(request):
    
    # get response and save query term to output context
    query_dict = request.POST
    context = {}
    context["searchterm"] = query_dict["searchterm"]

    return render(request, "search_results.html", context=context)


def document(request):
    return render(request, "document.html")


def comment(request):
    return render(request, "comment.html")