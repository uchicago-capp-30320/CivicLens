from django import forms

class Search(forms.Form):
    searchterm = forms.CharField(max_length=100)