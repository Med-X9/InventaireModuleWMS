# Generated by Django 5.2 on 2025-07-16 18:51

import apps.inventory.models
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Counting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True, verbose_name='Référence')),
                ('order', models.IntegerField(verbose_name='Ordre')),
                ('count_mode', models.CharField(max_length=100, verbose_name='Mode de comptage')),
                ('unit_scanned', models.BooleanField(default=False, verbose_name='Unité scannée')),
                ('entry_quantity', models.BooleanField(default=False, verbose_name='Saisie de quantité')),
                ('is_variant', models.BooleanField(default=False, verbose_name='Est une variante')),
                ('n_lot', models.BooleanField(default=False, verbose_name='N° lot')),
                ('n_serie', models.BooleanField(default=False, verbose_name='N° série')),
                ('dlc', models.BooleanField(default=False, verbose_name='DLC')),
                ('show_product', models.BooleanField(default=False, verbose_name='Afficher le produit')),
                ('stock_situation', models.BooleanField(default=False, verbose_name='Situation de stock')),
                ('quantity_show', models.BooleanField(default=False, verbose_name='Afficher la quantité')),
            ],
            options={
                'verbose_name': 'Comptage',
                'verbose_name_plural': 'Comptages',
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='EcartComptage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('ecart', models.IntegerField(blank=True, null=True)),
                ('result', models.IntegerField(blank=True, null=True)),
                ('justification', models.TextField(blank=True, null=True)),
                ('resolved', models.BooleanField(default=False)),
            ],
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='HistoricalAssigment',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('status', models.CharField(choices=[('EN ATTENTE', 'EN ATTENTE'), ('AFFECTE', 'AFFECTE'), ('PRET', 'PRET'), ('TRANSFERT', 'TRANSFERT'), ('ENTAME', 'ENTAME'), ('TERMINE', 'TERMINE')], max_length=10)),
                ('transfert_date', models.DateTimeField(blank=True, null=True)),
                ('entame_date', models.DateTimeField(blank=True, null=True)),
                ('affecte_date', models.DateTimeField(blank=True, null=True)),
                ('pret_date', models.DateTimeField(blank=True, null=True)),
                ('date_start', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Affectation',
                'verbose_name_plural': 'historical Affectations',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalCounting',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20, verbose_name='Référence')),
                ('order', models.IntegerField(verbose_name='Ordre')),
                ('count_mode', models.CharField(max_length=100, verbose_name='Mode de comptage')),
                ('unit_scanned', models.BooleanField(default=False, verbose_name='Unité scannée')),
                ('entry_quantity', models.BooleanField(default=False, verbose_name='Saisie de quantité')),
                ('is_variant', models.BooleanField(default=False, verbose_name='Est une variante')),
                ('n_lot', models.BooleanField(default=False, verbose_name='N° lot')),
                ('n_serie', models.BooleanField(default=False, verbose_name='N° série')),
                ('dlc', models.BooleanField(default=False, verbose_name='DLC')),
                ('show_product', models.BooleanField(default=False, verbose_name='Afficher le produit')),
                ('stock_situation', models.BooleanField(default=False, verbose_name='Situation de stock')),
                ('quantity_show', models.BooleanField(default=False, verbose_name='Afficher la quantité')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Comptage',
                'verbose_name_plural': 'historical Comptages',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalCountingDetail',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('quantity_inventoried', models.IntegerField()),
                ('dlc', models.DateField(blank=True, null=True)),
                ('n_lot', models.CharField(blank=True, max_length=100, null=True)),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical counting detail',
                'verbose_name_plural': 'historical counting details',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalEcartComptage',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('ecart', models.IntegerField(blank=True, null=True)),
                ('result', models.IntegerField(blank=True, null=True)),
                ('justification', models.TextField(blank=True, null=True)),
                ('resolved', models.BooleanField(default=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical ecart comptage',
                'verbose_name_plural': 'historical ecart comptages',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalInventory',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=50)),
                ('label', models.CharField(max_length=200)),
                ('date', models.DateTimeField()),
                ('status', models.CharField(choices=[('EN PREPARATION', 'EN PREPARATION'), ('EN REALISATION', 'EN REALISATION'), ('TERMINE', 'TERMINE'), ('CLOTURE', 'CLOTURE')], max_length=50)),
                ('inventory_type', models.CharField(choices=[('TOURNANT', 'TOURNANT'), ('GENERAL', 'GENERAL')], default='GENERAL', max_length=20)),
                ('en_preparation_status_date', models.DateTimeField(blank=True, null=True)),
                ('en_realisation_status_date', models.DateTimeField(blank=True, null=True)),
                ('termine_status_date', models.DateTimeField(blank=True, null=True)),
                ('cloture_status_date', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical inventory',
                'verbose_name_plural': 'historical inventorys',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalInventoryDetailRessource',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical inventory detail ressource',
                'verbose_name_plural': 'historical inventory detail ressources',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalJob',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('status', models.CharField(choices=[('EN ATTENTE', 'EN ATTENTE'), ('AFFECTE', 'AFFECTE'), ('PRET', 'PRET'), ('TRANSFERT', 'TRANSFERT'), ('ENTAME', 'ENTAME'), ('VALIDE', 'VALIDE'), ('TERMINE', 'TERMINE')], max_length=10)),
                ('en_attente_date', models.DateTimeField(blank=True, null=True)),
                ('affecte_date', models.DateTimeField(blank=True, null=True)),
                ('pret_date', models.DateTimeField(blank=True, null=True)),
                ('transfert_date', models.DateTimeField(blank=True, null=True)),
                ('entame_date', models.DateTimeField(blank=True, null=True)),
                ('valide_date', models.DateTimeField(blank=True, null=True)),
                ('termine_date', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical job',
                'verbose_name_plural': 'historical jobs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalJobDetail',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('status', models.CharField(max_length=50)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical job detail',
                'verbose_name_plural': 'historical job details',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalJobDetailRessource',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical job detail ressource',
                'verbose_name_plural': 'historical job detail ressources',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalNSerie',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('n_serie', models.CharField(blank=True, max_length=100, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical n serie',
                'verbose_name_plural': 'historical n series',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPersonne',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('nom', models.CharField(max_length=200)),
                ('prenom', models.CharField(max_length=200)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical personne',
                'verbose_name_plural': 'historical personnes',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPlanning',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20, verbose_name='Référence')),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de fin')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Planification',
                'verbose_name_plural': 'historical Planifications',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSetting',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(db_index=True, max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical setting',
                'verbose_name_plural': 'historical settings',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('label', models.CharField(max_length=200)),
                ('date', models.DateTimeField()),
                ('status', models.CharField(choices=[('EN PREPARATION', 'EN PREPARATION'), ('EN REALISATION', 'EN REALISATION'), ('TERMINE', 'TERMINE'), ('CLOTURE', 'CLOTURE')], max_length=50)),
                ('inventory_type', models.CharField(choices=[('TOURNANT', 'TOURNANT'), ('GENERAL', 'GENERAL')], default='GENERAL', max_length=20)),
                ('en_preparation_status_date', models.DateTimeField(blank=True, null=True)),
                ('en_realisation_status_date', models.DateTimeField(blank=True, null=True)),
                ('termine_status_date', models.DateTimeField(blank=True, null=True)),
                ('cloture_status_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='InventoryDetailRessource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('status', models.CharField(choices=[('EN ATTENTE', 'EN ATTENTE'), ('AFFECTE', 'AFFECTE'), ('PRET', 'PRET'), ('TRANSFERT', 'TRANSFERT'), ('ENTAME', 'ENTAME'), ('VALIDE', 'VALIDE'), ('TERMINE', 'TERMINE')], max_length=10)),
                ('en_attente_date', models.DateTimeField(blank=True, null=True)),
                ('affecte_date', models.DateTimeField(blank=True, null=True)),
                ('pret_date', models.DateTimeField(blank=True, null=True)),
                ('transfert_date', models.DateTimeField(blank=True, null=True)),
                ('entame_date', models.DateTimeField(blank=True, null=True)),
                ('valide_date', models.DateTimeField(blank=True, null=True)),
                ('termine_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='JobDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('status', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='JobDetailRessource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='NSerie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('n_serie', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='Personne',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('nom', models.CharField(max_length=200)),
                ('prenom', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='Planning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True, verbose_name='Référence')),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Date de fin')),
            ],
            options={
                'verbose_name': 'Planification',
                'verbose_name_plural': 'Planifications',
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='Assigment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('status', models.CharField(choices=[('EN ATTENTE', 'EN ATTENTE'), ('AFFECTE', 'AFFECTE'), ('PRET', 'PRET'), ('TRANSFERT', 'TRANSFERT'), ('ENTAME', 'ENTAME'), ('TERMINE', 'TERMINE')], max_length=10)),
                ('transfert_date', models.DateTimeField(blank=True, null=True)),
                ('entame_date', models.DateTimeField(blank=True, null=True)),
                ('affecte_date', models.DateTimeField(blank=True, null=True)),
                ('pret_date', models.DateTimeField(blank=True, null=True)),
                ('date_start', models.DateTimeField(blank=True, null=True)),
                ('session', models.ForeignKey(blank=True, limit_choices_to={'type': 'Mobile'}, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('counting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.counting')),
            ],
            options={
                'verbose_name': 'Affectation',
                'verbose_name_plural': 'Affectations',
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
        migrations.CreateModel(
            name='CountingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('quantity_inventoried', models.IntegerField()),
                ('dlc', models.DateField(blank=True, null=True)),
                ('n_lot', models.CharField(blank=True, max_length=100, null=True)),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('counting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.counting')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, apps.inventory.models.ReferenceMixin),
        ),
    ]
