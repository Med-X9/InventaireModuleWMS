# Generated by Django 5.2 on 2025-05-17 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='counting',
            name='quantity_show',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalcounting',
            name='quantity_show',
            field=models.BooleanField(default=False),
        ),
    ]
