# Generated manually — statut EN CONFIGURATION + date associée

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0026_inventory_type_magasin_setting_warehouse_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='en_configuration_status_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalinventory',
            name='en_configuration_status_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='status',
            field=models.CharField(
                choices=[
                    ('EN CONFIGURATION', 'EN CONFIGURATION'),
                    ('EN PREPARATION', 'EN PREPARATION'),
                    ('EN REALISATION', 'EN REALISATION'),
                    ('TERMINE', 'TERMINE'),
                    ('CLOTURE', 'CLOTURE'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='historicalinventory',
            name='status',
            field=models.CharField(
                choices=[
                    ('EN CONFIGURATION', 'EN CONFIGURATION'),
                    ('EN PREPARATION', 'EN PREPARATION'),
                    ('EN REALISATION', 'EN REALISATION'),
                    ('TERMINE', 'TERMINE'),
                    ('CLOTURE', 'CLOTURE'),
                ],
                max_length=50,
            ),
        ),
    ]
