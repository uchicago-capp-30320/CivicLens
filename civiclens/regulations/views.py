from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.shortcuts import render

from .models import Comment, Document, AgencyReference

from django.db.models import Count

from django.utils import timezone



def home(request):
    return render(request, "home.html")


def search_page(request):
    return render(request, "search_page.html")


def search_results(request):
    today = timezone.now().date()
    context = {}
    
    if request.method == "GET":
        query = request.GET.get("q", "")
        sort_by = request.GET.get("sort_by", "most_relevant")
        selected_agencies = request.GET.getlist("selected_agencies", "") 
        search_results = request.GET.get("source", False)
        if search_results:
            comments_any = request.GET.get("comments_any")
            comments_over_hundred = request.GET.get("comments_over_hundred")
            category_rule = request.GET.get("rule")
            category_proprosed_rule = request.GET.get("proposed_rule")
            category_notice = request.GET.get("notice")
            category_other = request.GET.get("other")
            category_lst = [category_rule, category_proprosed_rule, category_notice, category_other]
            
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
                .annotate(comment_count=Count('comment'))
                .filter(rank__gte=0.0001)
                .filter(comment_end_date__gte=today)
                .order_by("-rank")
            )
            if not documents.exists():
                documents = (
                    Document.objects.annotate(
                        rank=TrigramSimilarity("title", query)
                        + TrigramSimilarity("summary", query)
                        + TrigramSimilarity("agency_id", query)
                        + TrigramSimilarity("agency_type", query)
                    )
                    .annotate(comment_count=Count('comment'))
                    .filter(rank__gt=0.20)
                    .filter(comment_end_date__gte=today)
                    .order_by("-rank")
                ) 
            if sort_by == 'most_recent':
                documents = documents.order_by("-posted_date")
            elif sort_by == 'most_comments':
                documents = documents.order_by("-comment_count")
            elif sort_by == 'least_comments':
                documents = documents.order_by("comment_count")
            
            if selected_agencies:
                documents = documents.filter(agency_id__in=selected_agencies)
            
            if search_results:
                documents = documents.filter(document_type__in=category_lst)
                if comments_any:
                    documents = documents.filter(comment_count__gte=1) 
                if comments_over_hundred:
                    documents = documents.filter(comment_count__gte=100)

            context["documents"] = documents
    else:
        context["documents"] = None

    context["search"] = query

    return render(request, "search_results.html", 
            {"context": context, "agencies": AgencyReference.objects.all().order_by("id")}
    )


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