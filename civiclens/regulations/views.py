from django.shortcuts import render, redirect  # noqa: F401
from .models import Comment, Document, Search # noqa: F401
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity, SearchHeadline # noqa: F401
from datetime import datetime
from django.core.cache import cache

# https://docs.djangoproject.com/en/5.0/ref/contrib/postgres/search/
# https://medium.com/@nandagopal05/django-full-text-search-with-postgresql-f063aaf34e35
# https://testdriven.io/blog/django-search/
# https://medium.com/@dumanov/powerfull-and-simple-search-engine-in-django-rest-framework-cb24213f5ef5


def home(request):
    return render(request, "home.html")


def search_page(request):        
    return render(request, "search_page.html")


def search_results(request):
    
    context = {}
    ############################################################
    # get response and save query term to output context
    if request.method == "GET":
        search = Search()
        search.searchterm = request.GET["q"]
        print(search.searchterm)
        
        context["Search"] = search
    
    print(context)
    ############################################################
    if request.method == "GET":
        content = None
        query = request.GET.get("q")
        if query:
            search = Search()
            search.searchterm = query
        
            vector = SearchVector('title')
            documents = Document.objects.annotate(search=vector).filter(search=query)

            # cache_key = f"search_results_{search.searchterm}"
            # cache.set(cache_key, {'results': results, 'count': len(results)}, timeout=3600)

            context['documents'] = documents
            context['Search'] = search

            print("Search Term:", search.searchterm)
            print("Documents Found:", documents.count())

    return render(request, "search_results.html", {"context": context})


def document(request, doc_id):
    try:
        doc = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        doc = None
    try:
        comments = Comment.objects.filter(document=doc_id)
    except Comment.DoesNotExist:
        comments = None
    return render(request, "document.html", {"doc": doc, "comments": comments})


def comment(request):
    return render(request, "comment.html")