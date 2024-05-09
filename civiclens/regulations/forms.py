from django.db import models

class Search(models.Model):
    search_term = models.CharField(max_length=100)
    sort_by = models.CharField(max_length=100)

    