from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_merge_20250702_1350'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='termine_status_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ] 