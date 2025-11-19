"""
Test simple pour l'API Counting Detail - Utilise le service directement
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.mobile.services.counting_detail_service import CountingDetailService
from apps.inventory.models import CountingDetail, ComptageSequence, EcartComptage
import json

def test_upsert_logic():
    """Test de la logique UPSERT"""
    print("=" * 60)
    print("🧪 TEST UPSERT - Counting Detail Service")
    print("=" * 60)
    
    service = CountingDetailService()
    
    # Test 1: Création
    print("\n📝 Test 1: Création d'un nouveau CountingDetail")
    data_create = [{
        "counting_id": 107,
        "location_id": 828,
        "quantity_inventoried": 5,
        "assignment_id": 58,
        "product_id": 3766
    }]
    
    try:
        result1 = service.create_counting_details_batch(data_create, job_id=32)
        print(f"   Status: {'✅ Succès' if result1.get('success') else '❌ Échec'}")
        print(f"   Éléments traités: {result1.get('successful', 0)}/{result1.get('total_processed', 0)}")
        
        if result1.get('success'):
            results = result1.get('results', [])
            if results:
                action = results[0].get('result', {}).get('action')
                print(f"   Action: {action}")
                counting_detail_id = results[0].get('result', {}).get('counting_detail', {}).get('id')
                print(f"   CountingDetail ID: {counting_detail_id}")
                
                # Vérifier si créé
                if counting_detail_id:
                    cd = CountingDetail.objects.get(id=counting_detail_id)
                    print(f"   Quantité: {cd.quantity_inventoried}")
                    print(f"   ✅ Création confirmée")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Mise à jour (UPSERT)
    print("\n📝 Test 2: Mise à jour d'un CountingDetail existant (UPSERT)")
    data_update = [{
        "counting_id": 107,
        "location_id": 828,
        "quantity_inventoried": 7,  # Nouvelle quantité
        "assignment_id": 58,
        "product_id": 3766
    }]
    
    try:
        result2 = service.create_counting_details_batch(data_update, job_id=32)
        print(f"   Status: {'✅ Succès' if result2.get('success') else '❌ Échec'}")
        print(f"   Éléments traités: {result2.get('successful', 0)}/{result2.get('total_processed', 0)}")
        
        if result2.get('success'):
            results = result2.get('results', [])
            if results:
                action = results[0].get('result', {}).get('action')
                print(f"   Action: {action} (devrait être 'updated')")
                counting_detail_id = results[0].get('result', {}).get('counting_detail', {}).get('id')
                
                if counting_detail_id:
                    cd = CountingDetail.objects.get(id=counting_detail_id)
                    print(f"   Nouvelle quantité: {cd.quantity_inventoried} (devrait être 7)")
                    if cd.quantity_inventoried == 7:
                        print(f"   ✅ Mise à jour confirmée")
                    else:
                        print(f"   ⚠️  Quantité incorrecte")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Élément sans quantité (doit être ignoré)
    print("\n📝 Test 3: Élément sans quantité (doit être ignoré)")
    data_no_quantity = [
        {
            "counting_id": 107,
            "location_id": 829,
            "quantity_inventoried": None,  # Pas de quantité
            "assignment_id": 58,
            "product_id": 3767
        },
        {
            "counting_id": 107,
            "location_id": 830,
            "quantity_inventoried": 10,  # Quantité valide
            "assignment_id": 58,
            "product_id": 3768
        }
    ]
    
    try:
        result3 = service.create_counting_details_batch(data_no_quantity, job_id=32)
        print(f"   Status: {'✅ Succès' if result3.get('success') else '❌ Échec'}")
        print(f"   Éléments traités: {result3.get('successful', 0)}/{len(data_no_quantity)}")
        print(f"   (Seul l'élément avec quantité valide devrait être traité)")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Consensus (résultat final)
    print("\n📝 Test 4: Logique de consensus (résultat final)")
    print("   Premier comptage...")
    data_consensus1 = [{
        "counting_id": 107,
        "location_id": 831,
        "quantity_inventoried": 5,
        "assignment_id": 58,
        "product_id": 3769
    }]
    
    try:
        result_c1 = service.create_counting_details_batch(data_consensus1, job_id=32)
        if result_c1.get('success'):
            results = result_c1.get('results', [])
            if results:
                ecart = results[0].get('result', {}).get('ecart_comptage', {})
                final_result = ecart.get('final_result')
                print(f"   Premier comptage - final_result: {final_result} (devrait être None)")
        
        print("   Deuxième comptage (même valeur)...")
        data_consensus2 = [{
            "counting_id": 107,
            "location_id": 831,
            "quantity_inventoried": 5,  # Même valeur
            "assignment_id": 58,
            "product_id": 3769
        }]
        
        result_c2 = service.create_counting_details_batch(data_consensus2, job_id=32)
        if result_c2.get('success'):
            results = result_c2.get('results', [])
            if results:
                ecart = results[0].get('result', {}).get('ecart_comptage', {})
                final_result = ecart.get('final_result')
                print(f"   Deuxième comptage - final_result: {final_result} (devrait être 5)")
                if final_result == 5:
                    print(f"   ✅ Consensus confirmé")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)


if __name__ == '__main__':
    test_upsert_logic()

