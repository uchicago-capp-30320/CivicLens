import logging

from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.core.paginator import Paginator
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
    try:
        last_updated = (
            Document.objects.all()
            .order_by(
                "-last_modified_date",
            )
            .values("last_modified_date")[0:1][0]["last_modified_date"]
        )
    except IndexError:
        last_updated = None

    # TOP 5 MOST COMMENTED ON WITH NLP ANALYSIS
    # list of active documents open for comment
    active_documents_ids = Document.objects.filter(
        comment_end_date__gt=today
    ).values("id")

    # select top documents from NLP table where # of comments is highest
    try:
        top_commented_documents = (
            NLPoutput.objects.order_by("-num_total_comments")
            .filter(document_id__in=active_documents_ids)
            .select_related("nlpoutput")
            .values(
                "doc_plain_english_title",
                "num_total_comments",
                "document_id",
                "num_unique_comments",
                "document__title",
            )[:5]
        )
    except IndexError:
        top_commented_documents = None

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
    counts = comment_counts.aggregate(avg_comments=Avg("comment_count"))[
        "avg_comments"
    ]
    if counts:
        avg_comments = round(counts)
    else:
        avg_comments = None

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
    search_info = {}

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
                SearchVector("nlpoutput__doc_plain_english_title", weight="A")
                + SearchVector("nlpoutput__topics", weight="A")
                + SearchVector("nlpoutput__search_topics", weight="A")
                + SearchVector("title", weight="A")
                + SearchVector("summary", weight="B")
                + SearchVector("agency_id", weight="D")
                + SearchVector("agency_type", weight="D")
                + SearchVector("further_information", weight="D")
            )
            search_query = SearchQuery(query)
            search_headline = SearchHeadline("title", search_query)
            documents = (
                Document.objects.select_related("nlpoutput")
                .annotate(rank=SearchRank(vector, search_query))
                .annotate(headline=search_headline)
                .filter(rank__gte=0.0001)
                .filter(comment_end_date__gte=today)
                .order_by("-rank")
            )
            if not documents.exists():
                weight_a = 1.0
                weight_b = 0.75
                weight_d = 0.25

                documents = (
                    Document.objects.prefetch_related("nlpoutput")
                    .annotate(
                        rank=TrigramSimilarity("title", query) * weight_a
                        # + TrigramSimilarity(
                        #     "nlpoutput__doc_plain_english_title", query
                        # )
                        # * weight_a
                        # + TrigramSimilarity("nlpoutput__search_topics", query
                        #     ) * weight_d
                        + TrigramSimilarity("summary", query) * weight_b
                        + TrigramSimilarity("agency_id", query) * weight_d
                        + TrigramSimilarity("agency_type", query) * weight_d
                    )
                    .filter(rank__gt=0.20)
                    .filter(comment_end_date__gte=today)
                    .order_by("-rank")
                )

            if sort_by == "most_recent":
                documents = documents.order_by("-posted_date")
            elif sort_by == "most_comments":
                documents = documents.order_by("-nlpoutput__num_total_comments")
            elif sort_by == "least_comments":
                documents = documents.order_by("nlpoutput__num_total_comments")

            if selected_agencies:
                documents = documents.filter(agency_id__in=selected_agencies)

            if search_results:
                documents = documents.filter(document_type__in=category_lst)
                if comments_any:
                    documents = documents.filter(
                        nlpoutput__num_total_comments__gte=1
                    )
                if comments_over_hundred:
                    documents = documents.filter(
                        nlpoutput__num_total_comments__gte=100
                    )

            paginator = Paginator(documents, 20)
            page_number = request.GET.get("page")
            page = paginator.get_page(page_number)

            search_info["documents_page"] = page
        else:
            query = ""
            search_info["documents_page"] = None
    else:
        logger.error("Form validation failed: %s", form.errors)
        query = ""
        search_info["documents_page"] = None

    search_info["search"] = query
    search_info["form"] = form

    return render(
        request,
        "search_results.html",
        {
            "search_info": search_info,
            "agencies": AgencyReference.objects.all().order_by("id"),
        },
    )


def document(request, doc_id):  # noqa: E501
    today = timezone.now().date()

    doc = get_object_or_404(
        Document.objects.filter(id=doc_id).filter(comment_end_date__gte=today)
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
    except Comment.DoesNotExist:
        comments_api = None

    try:
        nlp = NLPoutput.objects.get(document=doc_id)
    except NLPoutput.DoesNotExist:
        nlp = NLPoutput()

    return render(
        request,
        "document.html",
        {
            "doc": doc,
            "nlp": nlp,
            "comments_api": comments_api,
            "fed_register_url": fed_register_url,
        },
    )


def handler404(request, exception):
    return render(request, "404.html")
