from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.shortcuts import render

from .models import Comment, Document


def home(request):
    return render(request, "home.html")


def search_page(request):
    return render(request, "search_page.html")


def search_results(request):
    context = {}
    if request.method == "GET":
        query = request.GET.get("q", "")

        if query:
            vector = (
                SearchVector("title", weight="A")
                + SearchVector("summary", weight="B")
                + SearchVector("agency_id", weight="D")
                + SearchVector("agency_type", weight="D")
                + SearchVector("further_information", weight="D")
            )
            search_query = SearchQuery(query)
            search_headline = SearchHeadline("title", search_query)
            documents = (
                Document.objects.annotate(rank=SearchRank(vector, search_query))
                .annotate(headline=search_headline)
                .filter(rank__gte=0.0001)
            ).order_by("-rank")

            documents = documents.order_by("-rank")

            if not documents.exists():
                documents = (
                    Document.objects.annotate(
                        rank=TrigramSimilarity("title", query)
                        + TrigramSimilarity("summary", query)
                        + TrigramSimilarity("agency_id", query)
                        + TrigramSimilarity("agency_type", query)  # +
                    )
                    .filter(rank__gt=0.20)
                    .order_by("-rank")
                )

            context["documents"] = documents
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
