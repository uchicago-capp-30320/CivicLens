# Generated by Django 5.0.4 on 2024-04-17 21:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dockets",
            fields=[
                (
                    "id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("docketType", models.CharField(blank=True, max_length=255)),
                ("lastModifiedDate", models.DateTimeField()),
                ("agencyId", models.CharField(blank=True, max_length=100)),
                ("title", models.TextField()),
                ("objectId", models.CharField(blank=True, max_length=255)),
                ("highlightedContent", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Documents",
            fields=[
                (
                    "id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("documentType", models.CharField(blank=True, max_length=255)),
                ("lastModifiedDate", models.DateTimeField()),
                ("frDocNum", models.CharField(blank=True, max_length=100)),
                ("withdrawn", models.BooleanField(default=False)),
                ("agencyId", models.CharField(blank=True, max_length=100)),
                ("commentEndDate", models.DateField(blank=True, null=True)),
                ("postedDate", models.DateField()),
                ("subtype", models.CharField(blank=True, max_length=255)),
                ("commentStartDate", models.DateField(blank=True, null=True)),
                ("openForComment", models.BooleanField(default=False)),
                ("objectId", models.CharField(blank=True, max_length=100)),
                ("fullTextXmlUrl", models.CharField(blank=True, max_length=255)),
                ("subAgy", models.CharField(blank=True, max_length=255)),
                ("agencyType", models.CharField(blank=True, max_length=100)),
                ("CFR", models.CharField(blank=True, max_length=100)),
                ("RIN", models.CharField(blank=True, max_length=100)),
                ("title", models.CharField(max_length=255)),
                ("summary", models.TextField()),
                ("dates", models.CharField(blank=True, max_length=255)),
                ("furtherInformation", models.TextField(blank=True)),
                ("supplementaryInformation", models.TextField(blank=True)),
                (
                    "docket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="regulations.dockets",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PublicComments",
            fields=[
                (
                    "id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("objectId", models.CharField(max_length=255)),
                ("commentOn", models.CharField(blank=True, max_length=255)),
                ("duplicateComments", models.IntegerField(default=0)),
                ("stateProvinceRegion", models.CharField(blank=True, max_length=100)),
                ("subtype", models.CharField(blank=True, max_length=100)),
                ("comment", models.TextField()),
                ("firstName", models.CharField(blank=True, max_length=255)),
                ("lastName", models.CharField(blank=True, max_length=255)),
                ("address1", models.CharField(blank=True, max_length=200)),
                ("address2", models.CharField(blank=True, max_length=200)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("email", models.EmailField(blank=True, max_length=100)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("govAgency", models.CharField(blank=True, max_length=100)),
                ("govAgencyType", models.CharField(blank=True, max_length=100)),
                ("organization", models.CharField(blank=True, max_length=255)),
                ("originalDocumentId", models.CharField(blank=True, max_length=100)),
                ("modifyDate", models.DateTimeField()),
                ("pageCount", models.IntegerField()),
                ("postedDate", models.DateField()),
                ("receiveDate", models.DateField()),
                ("title", models.TextField()),
                ("trackingNbr", models.CharField(blank=True, max_length=255)),
                ("withdrawn", models.BooleanField(default=False)),
                ("reasonWithdrawn", models.CharField(blank=True, max_length=255)),
                ("zip", models.CharField(blank=True, max_length=50)),
                ("restrictReason", models.CharField(blank=True, max_length=100)),
                ("restrictReasonType", models.CharField(blank=True, max_length=100)),
                ("submitterRep", models.CharField(blank=True, max_length=100)),
                ("submitterRepAddress", models.CharField(blank=True, max_length=255)),
                ("submitterRepCityState", models.CharField(blank=True, max_length=100)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="regulations.documents",
                    ),
                ),
            ],
        ),
    ]
