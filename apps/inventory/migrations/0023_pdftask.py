from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0022_assigment_bloqued_date_assigment_debloqued_date_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PdfTask",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("task_type", models.CharField(choices=[("inventory_jobs_pdf", "PDF jobs inventaire")], max_length=50)),
                ("params", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("PENDING", "En attente"), ("RUNNING", "En cours"), ("SUCCESS", "Terminé"), ("ERROR", "Erreur")], default="PENDING", max_length=20)),
                ("result_file", models.FileField(blank=True, null=True, upload_to="pdf_tasks/")),
                ("error_message", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Tâche PDF",
                "verbose_name_plural": "Tâches PDF",
            },
        ),
        migrations.AddIndex(
            model_name="pdftask",
            index=models.Index(fields=["task_type", "status"], name="pdf_task_type_status_idx"),
        ),
        migrations.AddIndex(
            model_name="pdftask",
            index=models.Index(fields=["created_at"], name="pdf_task_created_at_idx"),
        ),
    ]

