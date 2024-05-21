import logging

from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import SearchForm
from .models import AgencyReference, Comment, Document, NLPoutput


logger = logging.getLogger("django")


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def search_page(request):
    today = timezone.now().date()

    # find date for when one doc in the db was last updated (MVP technique)
    last_updated = (
        Document.objects.all()
        .order_by(
            "-last_modified_date",
        )
        .values("last_modified_date")[:1][0]["last_modified_date"]
    )

    # TOP 5 MOST COMMENTED ON WITH NLP ANALYSIS
    # list of active documents open for comment
    active_documents_ids = Document.objects.filter(
        comment_end_date__gt=today
    ).values("id")

    # select top documents from NLP table where # of comments is highest
    top_commented_documents = (
        NLPoutput.objects.order_by("-num_total_comments")
        .filter(document_id__in=active_documents_ids)
        .values(
            "doc_plain_english_title",
            "num_total_comments",
            "document_id",
            "num_unique_comments",
        )[:5]
    )

    # DATA FOR QUICK FACTS
    active_documents_count = Document.objects.filter(
        comment_end_date__gt=today
    ).count()

    # count by doc_id in comment table
    comment_counts = Comment.objects.values("document_id").annotate(
        comment_count=Count("id")
    )

    # join docs with comments, only on the docs open for comment
    joined_table = (
        Document.objects.all()
        .select_related("comment_counts")
        .filter(id__in=[item["document_id"] for item in comment_counts])
    )
    # count only the docs with any comments
    active_documents_with_comments = joined_table.count()

    # use NLP table to do the tallies
    avg_comments = round(
        comment_counts.aggregate(avg_comments=Avg("comment_count"))[
            "avg_comments"
        ]
    )

    return render(
        request,
        "search_page.html",
        {
            "top_commented_documents": top_commented_documents,
            "active_documents_count": active_documents_count,
            "active_documents_with_comments": active_documents_with_comments,
            "active_documents_with_no_comments": active_documents_count
            - active_documents_with_comments,
            "avg_comments": avg_comments,
            "last_updated": last_updated,
        },
    )


@require_http_methods(["GET"])
def search_results(request):  # noqa: C901
    today = timezone.now().date()
    context = {}

    form = SearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get("q", "")
        sort_by = form.cleaned_data.get("sort_by", "most_relevant")
        selected_agencies = form.cleaned_data.get("selected_agencies", [])
        search_results = form.cleaned_data.get("source", False)
        if search_results:
            comments_any = form.cleaned_data.get("comments_any")
            comments_over_hundred = form.cleaned_data.get(
                "comments_over_hundred"
            )
            category_rule = form.cleaned_data.get("rule", "")
            category_proposed_rule = form.cleaned_data.get("proposed_rule", "")
            category_notice = form.cleaned_data.get("notice", "")
            category_other = form.cleaned_data.get("other", "")
            category_lst = [
                category_rule,
                category_proposed_rule,
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
            query = ""
            context["documents"] = None

    else:
        logger.error("Form validation failed: %s", form.errors)
        query = ""
        context["documents"] = None

    context["search"] = query
    context["form"] = form

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

    fed_register_url = {
        "doc_posted_month": doc.posted_date.strftime("%m"),
        "doc_posted_day": doc.posted_date.strftime("%d"),
        "doc_posted_year": doc.posted_date.strftime("%Y"),
        "doc_name_url": doc.title.replace(" ", "-").lower(),
    }

    try:
        comments_api = (
            Comment.objects.filter(document=doc_id)
            .annotate(posted_date_only=TruncDate("posted_date"))
            .annotate(modify_date_only=TruncDate("modify_date"))
            .annotate(receive_date_only=TruncDate("receive_date"))
        )
        comments_last_updated = comments_api.latest(
            "modify_date_only"
        ).modify_date_only
        unique_comments = comments_api.distinct("comment").count()
    except Comment.DoesNotExist:
        comments_api = None
        unique_comments = 0
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
            "fed_register_url": fed_register_url,
        },
    )


def handler404(request, exception):
    return render(request, "404.html")
