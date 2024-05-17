from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import AgencyReference, Comment, Document


def home(request):
    return render(request, "home.html")


def search_page(request):
    return render(request, "search_page.html")


# require method decorqator to only allow GET requests
def search_results(request):  # noqa: C901
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
            category_lst = [
                category_rule,
                category_proprosed_rule,
                category_notice,
                category_other,
            ]

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
                .annotate(comment_count=Count("comment"))
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
                    .annotate(comment_count=Count("comment"))
                    .filter(rank__gt=0.20)
                    .filter(comment_end_date__gte=today)
                    .order_by("-rank")
                )
            if sort_by == "most_recent":
                documents = documents.order_by("-posted_date")
            elif sort_by == "most_comments":
                documents = documents.order_by("-comment_count")
            elif sort_by == "least_comments":
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

    return render(
        request,
        "search_results.html",
        {
            "context": context,
            "agencies": AgencyReference.objects.all().order_by("id"),
        },
    )


def document(request, doc_id):  # noqa: E501
    today = timezone.now().date()

    doc = get_object_or_404(
        Document.objects.filter(id=doc_id)
        .filter(comment_end_date__gte=today)
        .annotate(comment_count=Count("comment"))
    )

    try:
        comments_api = (
            Comment.objects.filter(document=doc_id)
            .annotate(posted_date_only=TruncDate("posted_date"))
            .annotate(modify_date_only=TruncDate("modify_date"))
            .annotate(receive_date_only=TruncDate("receive_date"))
        )
        comments_last_updated = comments_api.latest("modify_date_only").modify_date_only
        unique_comments = comments_api.distinct("comment").count()
    except Comment.DoesNotExist:
        comments_api = None
        unique_comments = 0

    if comments_api:
        try:
            latest_comment = comments_api.latest("modify_date_only")
            comments_last_updated = latest_comment.modify_date_only
        except ObjectDoesNotExist:
            comments_last_updated = "No comments found."
    else:
        comments_last_updated = "No comments found."

    # test data from jack
    comments_nlp = {
        "id": "7588edfc-4239-4970-970e-d080eecf4da7",
        "rep_comments": [
            {
                "id": "ED-2023-OPE-0123-28272",
                "text": """The more student loan debt that can be forgiven the
                better. Over the years , I have had yo pause my student l9ans
                because of financial hardships I was facing.The period of time
                that loans were in repayment I had made my payments on time.
                My loans are currently in repayment, and if that burden could
                be lifted it would be life-changing for me. Right now. I find
                it very difficult to pay off my student loan debt. It has been
                following me for quite some time. Loan forgiveness would be
                good if I can qualify for it. """,
                "num_represented": 450,
                "topic": "Debt Forgiveness",
                "form_letter": True,
            },
            {
                "id": "ED-2023-OPE-0123-28250",
                "text": """Hello I am a current student who would greatly
                appreciate the privilege of having my student loans forgiven.
                Thank you so much in advance!""",
                "num_represented": 231,
                "topic": "Student Loans",
                "form_letter": False,
            },
        ],
        "doc_plain_english_title": """Student Loan Debt Waiver: Department Of
        Education""",
        "num_total_comments": 980,
        "num_unique_comments": 762,
        "num_rep_comments": 2,
        "topics": [
            {
                "topic": "Debt Forgiveness",
                "positive": 129,
                "negative": 98,
                "neutral": 32,
            },
            {
                "topic": "Student Loans",
                "positive": 123,
                "negative": 32,
                "neutral": 149,
            },
            {
                "topic": "topic 3",
                "positive": 103,
                "negative": 32,
                "neutral": 149,
            },
            {
                "topic": "topic 4",
                "positive": 903,
                "negative": 32,
                "neutral": 149,
            },
        ],
        "num_topics": 2,
        "last_updated": "May 6, 2024",
        "document_id": "ED-2023-OPE-0123-26398",
    }
    # comments_nlp = {}
    return render(
        request,
        "document.html",
        {
            "doc": doc,
            "comments_nlp": comments_nlp,
            "comments_api": comments_api,
            "unique_comments": unique_comments,
            "comments_last_updated": comments_last_updated,
        },
    )


def comment(request):
    return render(request, "comment.html")
