# Generated manually

from django.db import migrations, models
import django.db.models.deletion

def create_default_type_ressource(apps, schema_editor):
    """Créer un type de ressource par défaut"""
    TypeRessource = apps.get_model('masterdata', 'TypeRessource')
    default_type, created = TypeRessource.objects.get_or_create(
        libelle='Générique',
        defaults={
            'description': 'Type de ressource par défaut'
        }
    )
    return default_type

def set_default_type_ressource(apps, schema_editor):
    """Définir le type de ressource par défaut pour toutes les ressources existantes"""
    Ressource = apps.get_model('masterdata', 'Ressource')
    TypeRessource = apps.get_model('masterdata', 'TypeRessource')
    
    # Récupérer le type par défaut
    default_type = TypeRessource.objects.filter(libelle='Générique').first()
    if not default_type:
        default_type = create_default_type_ressource(apps, schema_editor)
    
    # Mettre à jour toutes les ressources existantes
    Ressource.objects.filter(type_ressource__isnull=True).update(type_ressource=default_type)

def reverse_set_default_type_ressource(apps, schema_editor):
    """Opération inverse - pas besoin de faire quoi que ce soit"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('masterdata', '0004_alter_historicalstock_quantity_available_and_more'),
    ]

    operations = [
        # Créer le type de ressource par défaut
        migrations.RunPython(create_default_type_ressource, reverse_code=migrations.RunPython.noop),
        
        # Ajouter le champ type_ressource avec une valeur par défaut temporaire
        migrations.AddField(
            model_name='ressource',
            name='type_ressource',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='masterdata.typeressource',
                verbose_name='Type de ressource'
            ),
        ),
        
        # Définir la valeur par défaut pour les enregistrements existants
        migrations.RunPython(set_default_type_ressource, reverse_set_default_type_ressource),
        
        # Rendre le champ obligatoire
        migrations.AlterField(
            model_name='ressource',
            name='type_ressource',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='masterdata.typeressource',
                verbose_name='Type de ressource'
            ),
        ),
    ] 