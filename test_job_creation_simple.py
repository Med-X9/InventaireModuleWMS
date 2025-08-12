#!/usr/bin/env python
"""
Script de test simple pour la nouvelle logique de création de jobs avec comptages multiples
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Inventory, Counting, Job, JobDetail, Assigment
from apps.masterdata.models import Warehouse, Location
from apps.inventory.usecases.job_creation import JobCreationUseCase

def test_with_existing_data():
    """Test avec des données existantes"""
    print("🔍 Recherche de données existantes...")
    
    # Vérifier s'il y a des inventaires
    inventories = Inventory.objects.all()
    print(f"   - Inventaires trouvés: {inventories.count()}")
    
    # Vérifier s'il y a des warehouses
    warehouses = Warehouse.objects.all()
    print(f"   - Warehouses trouvés: {warehouses.count()}")
    
    # Vérifier s'il y a des emplacements
    locations = Location.objects.all()
    print(f"   - Emplacements trouvés: {locations.count()}")
    
    if inventories.count() == 0:
        print("❌ Aucun inventaire trouvé. Créez d'abord un inventaire.")
        return False
    
    if warehouses.count() == 0:
        print("❌ Aucun warehouse trouvé. Créez d'abord un warehouse.")
        return False
    
    if locations.count() == 0:
        print("❌ Aucun emplacement trouvé. Créez d'abord des emplacements.")
        return False
    
    # Prendre le premier inventaire
    inventory = inventories.first()
    print(f"   - Utilisation de l'inventaire: {inventory.reference}")
    
    # Vérifier les comptages de l'inventaire
    countings = Counting.objects.filter(inventory=inventory).order_by('order')
    print(f"   - Comptages trouvés: {countings.count()}")
    
    if countings.count() < 2:
        print("❌ L'inventaire doit avoir au moins 2 comptages.")
        return False
    
    # Prendre le premier warehouse
    warehouse = warehouses.first()
    print(f"   - Utilisation du warehouse: {warehouse.warehouse_name}")
    
    # Prendre les 3 premiers emplacements
    test_locations = locations[:3]
    print(f"   - Utilisation de {len(test_locations)} emplacements")
    
    # Test de création de job
    print("\n🧪 Test de création de job...")
    
    use_case = JobCreationUseCase()
    emplacement_ids = [loc.id for loc in test_locations]
    
    try:
        result = use_case.execute(
            inventory.id,
            warehouse.id,
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
        
        # Nettoyer le job créé
        job.delete()
        print("   - Job de test supprimé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de création de jobs avec données existantes")
    
    try:
        success = test_with_existing_data()
        
        if success:
            print("\n🎉 Test réussi!")
        else:
            print("\n⚠️ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")

if __name__ == "__main__":
    main()
