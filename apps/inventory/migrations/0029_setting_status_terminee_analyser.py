# Generated manually — Setting TERMINEE / ANALYSER + dates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0028_ecart_stock_theorique"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalsetting",
            name="status_date_analyse",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalsetting",
            name="status_date_termine",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="setting",
            name="status_date_analyse",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="setting",
            name="status_date_termine",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalsetting",
            name="status",
            field=models.CharField(
                choices=[
                    ("EN ATTENTE", "EN ATTENTE"),
                    ("LANCEE", "LANCEE"),
                    ("TERMINEE", "TERMINEE"),
                    ("ANALYSER", "ANALYSER"),
                    ("CLOTURE", "CLOTURE"),
                ],
                default="EN ATTENTE",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="setting",
            name="status",
            field=models.CharField(
                choices=[
                    ("EN ATTENTE", "EN ATTENTE"),
                    ("LANCEE", "LANCEE"),
                    ("TERMINEE", "TERMINEE"),
                    ("ANALYSER", "ANALYSER"),
                    ("CLOTURE", "CLOTURE"),
                ],
                default="EN ATTENTE",
                max_length=20,
            ),
        ),
    ]
