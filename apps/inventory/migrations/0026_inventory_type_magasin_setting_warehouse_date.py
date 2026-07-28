# Generated manually for MAGASIN inventory type + Setting.warehouse_date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0025_assigment_bloqued_date_assigment_debloqued_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='inventory_type',
            field=models.CharField(
                choices=[
                    ('TOURNANT', 'TOURNANT'),
                    ('GENERAL', 'GENERAL'),
                    ('MAGASIN', 'MAGASIN'),
                ],
                default='GENERAL',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='historicalinventory',
            name='inventory_type',
            field=models.CharField(
                choices=[
                    ('TOURNANT', 'TOURNANT'),
                    ('GENERAL', 'GENERAL'),
                    ('MAGASIN', 'MAGASIN'),
                ],
                default='GENERAL',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='setting',
            name='warehouse_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalsetting',
            name='warehouse_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
