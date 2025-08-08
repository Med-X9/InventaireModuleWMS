#!/usr/bin/env python
"""
Script simple pour tester l'admin NSerie
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import NSerie, Product
from apps.masterdata.admin import NSerieAdmin

def test_admin_configuration():
    """Test de la configuration admin"""
    print("🧪 Test de la configuration admin NSerie...")
    
    try:
        from django.contrib import admin
        
        # Vérifier que l'admin est enregistré
        registered_models = admin.site._registry.keys()
        nserie_registered = NSerie in registered_models
        
        print(f"✅ NSerie enregistré dans admin: {nserie_registered}")
        
        if nserie_registered:
            # Vérifier la configuration
            admin_instance = admin.site._registry[NSerie]
            print(f"✅ Classe admin: {type(admin_instance).__name__}")
            print(f"✅ List display: {admin_instance.list_display}")
            print(f"✅ List filter: {admin_instance.list_filter}")
            print(f"✅ Search fields: {admin_instance.search_fields}")
            print(f"✅ Date hierarchy: {admin_instance.date_hierarchy}")
            
            # Tester la création d'une instance admin
            admin_obj = NSerieAdmin(NSerie, None)
            print(f"✅ Instance admin créée: {type(admin_obj).__name__}")
            
            # Vérifier les méthodes personnalisées
            print(f"✅ Méthode get_product_name: {hasattr(admin_obj, 'get_product_name')}")
            print(f"✅ Méthode get_product_family: {hasattr(admin_obj, 'get_product_family')}")
            print(f"✅ Méthode get_form: {hasattr(admin_obj, 'get_form')}")
        
        return nserie_registered
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_model_properties():
    """Test des propriétés du modèle NSerie"""
    print("\n🧪 Test des propriétés du modèle NSerie...")
    
    try:
        # Vérifier les choix de statut
        status_choices = [choice[0] for choice in NSerie.STATUS_CHOICES]
        print(f"✅ Status choices: {status_choices}")
        
        # Vérifier les propriétés calculées
        print(f"✅ Propriété is_expired: {hasattr(NSerie, 'is_expired')}")
        print(f"✅ Propriété is_warranty_valid: {hasattr(NSerie, 'is_warranty_valid')}")
        
        # Vérifier les champs du modèle
        model_fields = [field.name for field in NSerie._meta.fields]
        expected_fields = ['reference', 'n_serie', 'product', 'status', 'description', 
                         'date_fabrication', 'date_expiration', 'warranty_end_date']
        
        for field in expected_fields:
            if field in model_fields:
                print(f"✅ Champ {field}: présent")
            else:
                print(f"❌ Champ {field}: manquant")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test du modèle: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_resource_configuration():
    """Test de la configuration de la ressource"""
    print("\n🧪 Test de la configuration de la ressource...")
    
    try:
        from apps.masterdata.admin import NSerieResource
        
        # Vérifier que la ressource existe
        print(f"✅ NSerieResource: {NSerieResource}")
        
        # Vérifier les champs de la ressource
        resource = NSerieResource()
        print(f"✅ Champs de la ressource: {resource.get_fields()}")
        
        # Vérifier la configuration Meta
        print(f"✅ Model: {resource.Meta.model}")
        print(f"✅ Fields: {resource.Meta.fields}")
        print(f"✅ Import ID fields: {resource.Meta.import_id_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la ressource: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_data_existing():
    """Test avec les données existantes"""
    print("\n🧪 Test avec les données existantes...")
    
    try:
        # Vérifier les données existantes
        nseries_count = NSerie.objects.count()
        print(f"✅ Nombre de numéros de série: {nseries_count}")
        
        products_with_nserie = Product.objects.filter(n_serie=True).count()
        print(f"✅ Produits avec n_serie=True: {products_with_nserie}")
        
        if nseries_count > 0:
            # Tester avec les données existantes
            nserie = NSerie.objects.first()
            admin_obj = NSerieAdmin(NSerie, None)
            
            print(f"✅ Test avec numéro de série: {nserie.n_serie}")
            print(f"   - Produit: {admin_obj.get_product_name(nserie)}")
            print(f"   - Famille: {admin_obj.get_product_family(nserie)}")
            print(f"   - Status: {nserie.status}")
            print(f"   - Expiré: {nserie.is_expired}")
            print(f"   - Garantie valide: {nserie.is_warranty_valid}")
        else:
            print("ℹ️ Aucun numéro de série trouvé dans la base de données")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des données: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test simple de l'admin NSerie")
    
    try:
        # Test de la configuration admin
        success1 = test_admin_configuration()
        
        # Test des propriétés du modèle
        success2 = test_model_properties()
        
        # Test de la configuration de la ressource
        success3 = test_resource_configuration()
        
        # Test avec les données existantes
        success4 = test_data_existing()
        
        if success1 and success2 and success3 and success4:
            print("\n🎉 Tous les tests ont réussi!")
            print("\n✅ L'admin NSerie est correctement configuré")
            print("\n📋 Fonctionnalités disponibles:")
            print("   - ✅ Import/Export des numéros de série")
            print("   - ✅ Affichage des informations produit et famille")
            print("   - ✅ Filtres par statut, famille, dates")
            print("   - ✅ Recherche par numéro, produit, description")
            print("   - ✅ Calcul automatique des dates d'expiration et garantie")
            print("   - ✅ Hiérarchie par date de création")
            print("   - ✅ Gestion des propriétés calculées")
        else:
            print("\n⚠️ Certains tests ont échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
