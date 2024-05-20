from django import forms

from .models import AgencyReference


class SearchForm(forms.Form):
    q = forms.CharField(max_length=255, required=False, label="Search")
    sort_by = forms.ChoiceField(
        choices=[
            ("most_relevant", "Most Relevant"),
            ("most_recent", "Most Recent"),
            ("most_comments", "Most Comments"),
            ("least_comments", "Least Comments"),
        ],
        required=False,
        label="Sort By",
    )
    selected_agencies = forms.MultipleChoiceField(
        choices=[
            (agency.id, agency.name) for agency in AgencyReference.objects.all()
        ],
        required=False,
        label="Selected Agencies",
    )
    comments_any = forms.BooleanField(required=False, label="Comments Any")
    comments_over_hundred = forms.BooleanField(
        required=False, label="Comments Over Hundred"
    )
    rule = forms.CharField(required=False, label="Rule")
    proposed_rule = forms.CharField(
        required=False, initial="Proposed Rule", label="Proposed Rule"
    )
    notice = forms.CharField(required=False, label="Notice")
    other = forms.CharField(required=False, label="Other")
    source = forms.BooleanField(required=False, label="Source")
