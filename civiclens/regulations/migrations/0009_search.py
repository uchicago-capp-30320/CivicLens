# Generated by Django 5.0.4 on 2024-05-06 19:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulations", "0008_agencyreference"),
    ]

    operations = [
        migrations.CreateModel(
            name="Search",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("search_term", models.CharField(max_length=100)),
                ("sort_by", models.CharField(max_length=100)),
            ],
        ),
    ]
