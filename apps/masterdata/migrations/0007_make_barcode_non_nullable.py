# Generated manually

from django.db import migrations, models


def fill_null_barcodes(apps, schema_editor):
    """
    Remplit les valeurs NULL dans historicalproduct avec une chaîne vide.
    Comme la base est vide, cette fonction ne fait rien mais est nécessaire
    pour la migration.
    """
    HistoricalProduct = apps.get_model('masterdata', 'HistoricalProduct')
    HistoricalProduct.objects.filter(Barcode__isnull=True).update(Barcode='')


class Migration(migrations.Migration):

    dependencies = [
        ('masterdata', '0006_alter_historicalproduct_short_description_and_more'),
    ]

    operations = [
        # D'abord, remplir les valeurs NULL
        migrations.RunPython(fill_null_barcodes, migrations.RunPython.noop),
        # Ensuite, rendre le champ non-nullable
        migrations.AlterField(
            model_name='historicalproduct',
            name='Barcode',
            field=models.CharField(max_length=30, verbose_name='Code-barres'),
        ),
        migrations.AlterField(
            model_name='product',
            name='Barcode',
            field=models.CharField(max_length=30, verbose_name='Code-barres'),
        ),
    ]

