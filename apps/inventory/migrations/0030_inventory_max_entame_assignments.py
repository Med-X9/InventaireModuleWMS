from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0029_setting_status_terminee_analyser'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='max_entame_assignments',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalinventory',
            name='max_entame_assignments',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
