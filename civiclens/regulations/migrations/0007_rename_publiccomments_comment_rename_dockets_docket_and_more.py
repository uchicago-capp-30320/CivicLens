# Generated by Django 4.2.11 on 2024-04-23 04:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("regulations", "0006_rename_agencyid_dockets_agency_id_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="PublicComments",
            new_name="Comment",
        ),
        migrations.RenameModel(
            old_name="Dockets",
            new_name="Docket",
        ),
        migrations.RenameModel(
            old_name="Documents",
            new_name="Document",
        ),
    ]
