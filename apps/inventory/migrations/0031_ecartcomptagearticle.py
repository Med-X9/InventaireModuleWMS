from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0030_inventory_max_entame_assignments'),
        ('masterdata', '0021_stock_quantity_available_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='EcartComptageArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='Quantité retenue')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ecart_comptage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_results', to='inventory.ecartcomptage')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='masterdata.product')),
            ],
            options={
                'verbose_name': "Résultat article d'un écart",
                'verbose_name_plural': "Résultats articles d'écarts",
            },
        ),
        migrations.AddConstraint(
            model_name='ecartcomptagearticle',
            constraint=models.UniqueConstraint(fields=('ecart_comptage', 'product'), name='ecart_article_unique'),
        ),
    ]
