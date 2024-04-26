from django import forms

class Search(forms.Form):
    searchterm = forms.CharField(widget=forms.Textarea)