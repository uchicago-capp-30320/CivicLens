from django.db import models


class Docket(models.Model):
    "Model representing a docket."
    id = models.TextField(primary_key=True)
    docket_type = models.CharField(max_length=255, blank=True, null=True)
    last_modified_date = models.DateTimeField(null=True)
    agency_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.TextField(null=True)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    highlighted_content = models.CharField(
        max_length=255, blank=True, null=True
    )


class Document(models.Model):
    "Model representing a document."
    id = models.CharField(max_length=255, primary_key=True)
    document_type = models.CharField(max_length=255, blank=True, null=True)
    last_modified_date = models.DateTimeField(null=True)
    fr_doc_num = models.CharField(max_length=100, blank=True, null=True)
    withdrawn = models.BooleanField(default=False)
    agency_id = models.CharField(max_length=100, blank=True, null=True)
    comment_end_date = models.DateField(null=True, blank=True)
    posted_date = models.DateField(null=True)
    title = models.TextField(null=True)
    docket = models.ForeignKey(Docket, on_delete=models.CASCADE)
    subtype = models.CharField(max_length=255, blank=True, null=True)
    comment_start_date = models.DateField(blank=True, null=True)
    open_for_comment = models.BooleanField(default=False, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    full_text_xml_url = models.CharField(max_length=255, blank=True, null=True)
    sub_agy = models.CharField(max_length=255, blank=True, null=True)
    agency_type = models.CharField(max_length=100, blank=True, null=True)
    cfr = models.CharField(max_length=100, blank=True, null=True)
    rin = models.CharField(max_length=100, blank=True, null=True)
    title = models.TextField(null=True)
    summary = models.TextField(null=True)
    dates = models.TextField(null=True)
    further_information = models.TextField(blank=True, null=True)
    supplementary_information = models.TextField(blank=True, null=True)


class Comment(models.Model):
    "Model representing a public comment."
    id = models.CharField(max_length=255, primary_key=True)
    object_id = models.CharField(max_length=255)
    comment_on = models.CharField(max_length=255, blank=True, null=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    duplicate_comments = models.IntegerField(default=0)
    state_province_region = models.CharField(
        max_length=100, blank=True, null=True
    )
    subtype = models.CharField(max_length=100, blank=True, null=True)
    comment = models.TextField(null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    address1 = models.CharField(max_length=200, blank=True, null=True)
    address2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    gov_agency = models.CharField(max_length=100, blank=True, null=True)
    gov_agency_type = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    original_document_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    modify_date = models.DateTimeField(null=True)
    page_count = models.IntegerField(null=True)
    posted_date = models.DateTimeField(null=True)
    receive_date = models.DateTimeField(null=True)
    title = models.TextField(null=True)
    tracking_nbr = models.CharField(max_length=255, blank=True, null=True)
    withdrawn = models.BooleanField(default=False)
    reason_withdrawn = models.CharField(max_length=255, blank=True, null=True)
    zip = models.CharField(max_length=50, blank=True, null=True)
    restrict_reason = models.CharField(max_length=100, blank=True, null=True)
    restrict_reason_type = models.CharField(
        max_length=100, blank=True, null=True
    )
    submitter_rep = models.CharField(max_length=100, blank=True, null=True)
    submitter_rep_address = models.CharField(
        max_length=255, blank=True, null=True
    )
    submitter_rep_city_state = models.CharField(
        max_length=100, blank=True, null=True
    )


class AgencyReference(models.Model):
    "Model representing a reference to an agency."
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)


class NLPoutput(models.Model):
    "Model representing NLP output at the document level."
    document = models.OneToOneField(
        Document, on_delete=models.CASCADE, related_name="nlpoutput"
    )
    comments = models.JSONField(null=True)
    doc_plain_english_title = models.CharField(
        max_length=255, blank=True, null=True
    )
    num_total_comments = models.IntegerField(default=0)
    num_unique_comments = models.IntegerField(default=0)
    num_representative_comment = models.IntegerField(default=0)
    topics = models.JSONField(null=True)
    num_topics = models.IntegerField(default=0)
    last_updated = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    search_topics = models.TextField(null=True)
    is_representative = models.BooleanField(default=False, null=True)


class DataQA(models.Model):
    """Model representing dockets, documents, and comments that were
    flagged for QA issues"""

    added_at = models.DateTimeField(auto_now_add=True)
    data_id = models.CharField(max_length=255, blank=True, null=True)
    data_type = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(null=True)
