from django.shortcuts import render, redirect  # noqa: F401
from .models import Comment, Document, Search # noqa: F401


def home(request):
    return render(request, "home.html")


def search_page(request):        
    return render(request, "search_page.html")

# @api.get("/regulations/search/results/")
def search_results(request):
    
    context = {}

    # get response and save query term to output context
    if request.method == "GET":
        search = Search()
        search.search_term = request.GET["q"]
        # search.sort_by = request.GET["sort_by"]
        
        context["Search"] = search
    
        print(search)

        return render(request, "search_results.html", context=context)
    else:
        return render(request, "search_page.html", context=context)


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