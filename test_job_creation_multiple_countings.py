#!/usr/bin/env python
"""
Script de test pour la nouvelle logique de création de jobs avec comptages multiples
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Inventory, Counting, Job, JobDetail, Assigment
from apps.masterdata.models import Warehouse, Zone, SousZone, Location, ZoneType, LocationType
from apps.inventory.usecases.job_creation import JobCreationUseCase

def create_test_data():
    """Crée les données de test nécessaires"""
    print("Création des données de test...")
    
    # Créer un warehouse
    warehouse = Warehouse.objects.create(
        warehouse_name="Entrepôt Test",
        reference="WH-TEST"
    )
    
    # Créer un type de zone
    zone_type = ZoneType.objects.create(
        reference="ZT-TEST",
        type_name="Type Test",
        status="ACTIVE"
    )
    
    # Créer une zone
    zone = Zone.objects.create(
        zone_name="Zone Test",
        reference="ZONE-TEST",
        warehouse=warehouse,
        zone_type=zone_type,
        zone_status="ACTIVE"
    )
    
    # Créer une sous-zone
    sous_zone = SousZone.objects.create(
        sous_zone_name="Sous-Zone Test",
        reference="SZ-TEST",
        zone=zone
    )
    
    # Créer un type d'emplacement
    location_type = LocationType.objects.create(
        reference="LT-TEST",
        name="Type Emplacement Test",
        is_active=True
    )
    
    # Créer des emplacements
    locations = []
    for i in range(1, 6):
        location = Location.objects.create(
            location_reference=f"LOC-TEST-{i:03d}",
            sous_zone=sous_zone,
            location_type=location_type
        )
        locations.append(location)
    
    # Créer un inventaire avec comptage "image de stock"
    inventory_image_stock = Inventory.objects.create(
        reference="INV-IMAGE-STOCK",
        label="Inventaire Image de Stock",
        date=timezone.now(),
        status="EN PREPARATION",
        inventory_type="GENERAL"
    )
    
    # Créer les comptages pour l'inventaire "image de stock"
    counting1_image = Counting.objects.create(
        reference="CNT-IMG-1",
        order=1,
        count_mode="image de stock",
        inventory=inventory_image_stock
    )
    
    counting2_image = Counting.objects.create(
        reference="CNT-IMG-2",
        order=2,
        count_mode="par article",
        inventory=inventory_image_stock
    )
    
    # Créer un inventaire avec comptage normal
    inventory_normal = Inventory.objects.create(
        reference="INV-NORMAL",
        label="Inventaire Normal",
        date=timezone.now(),
        status="EN PREPARATION",
        inventory_type="GENERAL"
    )
    
    # Créer les comptages pour l'inventaire normal
    counting1_normal = Counting.objects.create(
        reference="CNT-NORM-1",
        order=1,
        count_mode="en vrac",
        inventory=inventory_normal
    )
    
    counting2_normal = Counting.objects.create(
        reference="CNT-NORM-2",
        order=2,
        count_mode="par article",
        inventory=inventory_normal
    )
    
    print(f"✅ Données de test créées:")
    print(f"   - Warehouse: {warehouse.warehouse_name}")
    print(f"   - Emplacements: {len(locations)} créés")
    print(f"   - Inventaire 'Image de Stock': {inventory_image_stock.reference}")
    print(f"   - Inventaire 'Normal': {inventory_normal.reference}")
    
    return {
        'warehouse': warehouse,
        'locations': locations,
        'inventory_image_stock': inventory_image_stock,
        'inventory_normal': inventory_normal
    }

def test_job_creation_image_stock(test_data):
    """Test de création de job avec configuration 'image de stock'"""
    print("\n🧪 Test 1: Configuration 'Image de Stock'")
    
    use_case = JobCreationUseCase()
    emplacement_ids = [loc.id for loc in test_data['locations']]
    
    try:
        result = use_case.execute(
            test_data['inventory_image_stock'].id,
            test_data['warehouse'].id,
            emplacement_ids
        )
        
        print(f"✅ Job créé avec succès:")
        print(f"   - Job ID: {result['job_id']}")
        print(f"   - Job Reference: {result['job_reference']}")
        print(f"   - Emplacements: {result['emplacements_count']}")
        print(f"   - Mode 1er comptage: {result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {result['counting2_mode']}")
        print(f"   - Assignments créés: {result['assignments_created']}")
        
        # Vérifier les JobDetails
        job = Job.objects.get(id=result['job_id'])
        job_details = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails créés: {job_details.count()}")
        
        # Vérifier les Assignments
        assignments = Assigment.objects.filter(job=job)
        print(f"   - Assignments créés: {assignments.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_job_creation_normal(test_data):
    """Test de création de job avec configuration normale"""
    print("\n🧪 Test 2: Configuration 'Normale'")
    
    use_case = JobCreationUseCase()
    emplacement_ids = [loc.id for loc in test_data['locations']]
    
    try:
        result = use_case.execute(
            test_data['inventory_normal'].id,
            test_data['warehouse'].id,
            emplacement_ids
        )
        
        print(f"✅ Job créé avec succès:")
        print(f"   - Job ID: {result['job_id']}")
        print(f"   - Job Reference: {result['job_reference']}")
        print(f"   - Emplacements: {result['emplacements_count']}")
        print(f"   - Mode 1er comptage: {result['counting1_mode']}")
        print(f"   - Mode 2ème comptage: {result['counting2_mode']}")
        print(f"   - Assignments créés: {result['assignments_created']}")
        
        # Vérifier les JobDetails
        job = Job.objects.get(id=result['job_id'])
        job_details = JobDetail.objects.filter(job=job)
        print(f"   - JobDetails créés: {job_details.count()}")
        
        # Vérifier les Assignments
        assignments = Assigment.objects.filter(job=job)
        print(f"   - Assignments créés: {assignments.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    
    # Supprimer les jobs créés
    Job.objects.filter(reference__startswith="JOB-").delete()
    
    # Supprimer les inventaires de test
    Inventory.objects.filter(reference__in=["INV-IMAGE-STOCK", "INV-NORMAL"]).delete()
    
    # Supprimer les emplacements de test
    Location.objects.filter(location_reference__startswith="LOC-TEST-").delete()
    
    # Supprimer les types d'emplacement de test
    LocationType.objects.filter(reference="LT-TEST").delete()
    
    # Supprimer les sous-zones de test
    SousZone.objects.filter(reference="SZ-TEST").delete()
    
    # Supprimer les zones de test
    Zone.objects.filter(reference="ZONE-TEST").delete()
    
    # Supprimer les types de zone de test
    ZoneType.objects.filter(reference="ZT-TEST").delete()
    
    # Supprimer le warehouse de test
    Warehouse.objects.filter(reference="WH-TEST").delete()
    
    print("✅ Données de test nettoyées")

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests de création de jobs avec comptages multiples")
    
    try:
        # Créer les données de test
        test_data = create_test_data()
        
        # Test 1: Configuration "image de stock"
        success1 = test_job_creation_image_stock(test_data)
        
        # Test 2: Configuration normale
        success2 = test_job_creation_normal(test_data)
        
        # Résumé
        print("\n📊 Résumé des tests:")
        print(f"   - Test 'Image de Stock': {'✅ Réussi' if success1 else '❌ Échoué'}")
        print(f"   - Test 'Normal': {'✅ Réussi' if success2 else '❌ Échoué'}")
        
        if success1 and success2:
            print("\n🎉 Tous les tests sont passés avec succès!")
        else:
            print("\n⚠️ Certains tests ont échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")
        
    finally:
        # Nettoyer les données de test
        cleanup_test_data()

if __name__ == "__main__":
    main()
