from django.shortcuts import render, redirect  # noqa: F401
from .models import Comment, Document # noqa: F401
from .forms import Search
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity, SearchHeadline # noqa: F401
from django.db.models import Value # noqa: F401
from datetime import datetime # noqa: F401
from django.core.cache import cache # noqa: F401

# https://docs.djangoproject.com/en/5.0/ref/contrib/postgres/search/
# https://medium.com/@nandagopal05/django-full-text-search-with-postgresql-f063aaf34e35
# https://testdriven.io/blog/django-search/
# https://medium.com/@dumanov/powerfull-and-simple-search-engine-in-django-rest-framework-cb24213f5ef5


def home(request):
    return render(request, "home.html")


def search_page(request):        
    return render(request, "search_page.html")

# @api.get("/regulations/search/results/")
def search_results(request):
    
    context = {}
    if request.method == "GET":
        query = request.GET.get("q", "")
        sort_by = request.GET.get("sort_by", "most_relevant")
        
        if query:
            vector = SearchVector("title", weight="A") + SearchVector(
                "summary", weight="B") + SearchVector("agency_id", weight="D"
                ) + SearchVector("agency_type", weight="D") + SearchVector(
                "further_information", weight="D")
            search_query = SearchQuery(query)
            search_headline = SearchHeadline("title", search_query)
            documents = Document.objects.annotate(rank=SearchRank(vector, 
                    search_query)).annotate(headline=search_headline).filter(
                    rank__gte=0.0001)# .order_by("-rank")
    
            
            print(Search.sort_by)
            print("Sort By:", sort_by)
            # if sort_by == "most_recent":
            #     documents = documents.order_by("-posted_date")  # Assuming 'created_at' is a field in your Document model
            # elif sort_by == "most_comments":
            #     documents = documents.annotate(comment_count=Count('comments')).order_by("-comment_count")
            # elif sort_by == "least_comments":
            #     documents = documents.annotate(comment_count=Count('comments')).order_by("comment_count")
            # else:  # Default sort by rank if 'most_relevant' or any other unspecified value
            #     documents = documents.order_by("-rank")
            
            documents = documents.order_by("-rank")
                
            # if not documents.exists():
            #     documents = Document.objects.annotate(
            #         rank=TrigramSimilarity("title", query) +
            #              TrigramSimilarity("summary", query) +
            #              TrigramSimilarity("agency_id", query) +
            #              TrigramSimilarity("agency_type", query) +
            #              TrigramSimilarity("further_information", query)
            #     ).filter(rank__gt=0.1).order_by("-rank")

            # cache_key = f"search_results_{search.searchterm}"
            # cache.set(cache_key, {'results': results, 'count': len(results)}, timeout=3600)

            context['documents'] = documents
            print("Search Term:", query)
            print("Documents Found:", documents.count())
    else:
        context["documents"] = None
    

    context["search"] = query
        

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