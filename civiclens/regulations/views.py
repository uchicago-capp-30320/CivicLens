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
    # try:
    #     comments = Comment.objects.filter(document=doc_id)
    # except Comment.DoesNotExist:
    #     comments = None

    # test data from jack
    comments = {
        "id": "7588edfc-4239-4970-970e-d080eecf4da7", 
        "rep_comments": [
            {"id": "ED-2023-OPE-0123-28272", 
             "text": "The more student loan debt that can be forgiven the better. Over the years , I have had yo pause my student l9ans because of financial hardships I was facing.The period of time that loans were in repayment I had made my payments on time.My loans are currently in repayment, and if that burden could be lifted it would be life-changing for me. Right now. I find it very difficult to pay off my student loan debt. It has been following me for quite some time. Loan forgiveness would be good if I can qualify for it. ", 
             "num_represented": 450, 
             "topic": "Debt Forgiveness", 
             "form_letter": True}, 
             {"id": "ED-2023-OPE-0123-28250", 
              "text": "Hello I am a current student who would greatly appreciate the privilege of having my student loans forgiven. Thank you so much in advance!", 
              "num_represented": 231, 
              "topic": "Student Loans", 
              "form_letter": False}], 
        "doc_plain_english_title": "Student Loan Debt Waiver: Department Of Education", 
        "num_total_comments": 980, 
        "num_unique_comments": 762, 
        "num_rep_comments": 2, 
        "topics": 
            [{"topic": "Debt Forgiveness", 
              "positive": 129, 
              "negative": 98, 
              "neutral": 32}, 
            {"topic": "Student Loans", 
             "positive": 123, 
             "negative": 32, 
             "neutral": 149
             },
            {"topic": "topic 3",
             "positive": 1003, 
             "negative": 32, 
             "neutral": 149
             }],
        "num_topics": 2, 
        "last_updated": "May 6, 2024",
        "document_id": "ED-2023-OPE-0123-26398"
    }

    return render(request, "document.html", {"doc": doc, "comments": comments})


def comment(request):
    return render(request, "comment.html")
