from django.shortcuts import render, redirect  # noqa: F401
from .models import Search # noqa: F401


def home(request):
    return render(request, "home.html")


def search_page(request):        
    return render(request, "search_page.html")


def search_results(request):
    
    context = {}

    # get response and save query term to output context
    if request.method == "GET":
        search = Search()
        search.searchterm = request.GET["q"]
        print(search.searchterm)
        # search.searchterm = q
        
        context["Search"] = search
    
    print(context)

    return render(request, "search_results.html", context=context)


def document(request):
    return render(request, "document.html")


def comment(request):
    return render(request, "comment.html")