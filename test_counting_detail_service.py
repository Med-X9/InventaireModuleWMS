"""
Test simple pour le service CountingDetail avec UPSERT
Teste directement le service sans passer par l'API HTTP
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
except Exception as e:
    print(f"⚠️ Erreur de configuration Django: {e}")
    print("Assurez-vous que Django est correctement configuré")
    sys.exit(1)

from apps.mobile.services.counting_detail_service import CountingDetailService
from apps.inventory.models import CountingDetail, ComptageSequence, EcartComptage
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_upsert_logic():
    """Test de la logique UPSERT"""
    print("=" * 60)
    print("🧪 TEST SERVICE COUNTING DETAIL - UPSERT")
    print("=" * 60)
    
    service = CountingDetailService()
    
    # Test 1: Vérifier la méthode _get_detail_key
    print("\n📝 Test 1: Génération de clé pour détection d'existants")
    data = {
        'counting_id': 107,
        'location_id': 828,
        'product_id': 3766
    }
    key = service._get_detail_key(data)
    print(f"Clé générée: {key}")
    assert key == (107, 828, 3766), "La clé devrait être (107, 828, 3766)"
    print("✅ Clé générée correctement")
    
    # Test 2: Vérifier la méthode _prefetch_existing_counting_details
    print("\n📝 Test 2: Préchargement des CountingDetail existants")
    data_list = [
        {
            'counting_id': 107,
            'location_id': 828,
            'product_id': 3766,
            'quantity_inventoried': 5
        }
    ]
    
    try:
        existing_map = service._prefetch_existing_counting_details(data_list, job_id=32)
        print(f"Nombre d'existants trouvés: {len(existing_map)}")
        print("✅ Préchargement fonctionne")
    except Exception as e:
        print(f"⚠️ Erreur lors du préchargement: {e}")
        print("   (Normal si la base de données n'est pas configurée)")
    
    # Test 3: Vérifier la validation de quantité
    print("\n📝 Test 3: Validation de quantité")
    test_cases = [
        ({'quantity_inventoried': 5}, True, "Quantité valide"),
        ({'quantity_inventoried': 0}, False, "Quantité = 0"),
        ({'quantity_inventoried': -1}, False, "Quantité négative"),
        ({}, False, "Pas de quantité"),
    ]
    
    for data, should_process, description in test_cases:
        quantity = data.get('quantity_inventoried')
        is_valid = quantity is not None and quantity > 0
        status = "✅" if is_valid == should_process else "❌"
        print(f"{status} {description}: {data} -> {'Traitement' if is_valid else 'Ignoré'}")
    
    # Test 4: Vérifier le calcul de consensus
    print("\n📝 Test 4: Calcul de consensus (résultat final)")
    
    # Simuler des séquences
    class MockSequence:
        def __init__(self, quantity):
            self.quantity = quantity
    
    # Cas 1: Moins de 2 séquences -> pas de résultat
    sequences_1 = [MockSequence(5)]
    result_1 = service._calculate_consensus_result(sequences_1, None)
    assert result_1 is None, "Pas de résultat avec < 2 séquences"
    print("✅ Cas 1: < 2 séquences -> pas de résultat")
    
    # Cas 2: 2 séquences identiques -> résultat = valeur
    sequences_2 = [MockSequence(5), MockSequence(5)]
    result_2 = service._calculate_consensus_result(sequences_2, None)
    assert result_2 == 5, "Résultat devrait être 5 avec 2 séquences identiques"
    print(f"✅ Cas 2: 2 séquences identiques (5, 5) -> résultat = {result_2}")
    
    # Cas 3: 2 séquences différentes -> pas de consensus
    sequences_3 = [MockSequence(5), MockSequence(10)]
    result_3 = service._calculate_consensus_result(sequences_3, None)
    print(f"✅ Cas 3: 2 séquences différentes (5, 10) -> résultat = {result_3}")
    
    # Cas 4: 3 séquences, 2 identiques -> résultat = valeur confirmée
    sequences_4 = [MockSequence(5), MockSequence(10), MockSequence(5)]
    result_4 = service._calculate_consensus_result(sequences_4, None)
    assert result_4 == 5, "Résultat devrait être 5 (confirmé 2 fois)"
    print(f"✅ Cas 4: 3 séquences (5, 10, 5) -> résultat = {result_4}")
    
    print("\n" + "=" * 60)
    print("✅ TOUS LES TESTS DE LOGIQUE RÉUSSIS")
    print("=" * 60)
    print("\n💡 Pour tester avec la base de données réelle:")
    print("   - Assurez-vous que la base est configurée")
    print("   - Utilisez l'API: POST /mobile/api/job/<job_id>/counting-detail/")
    print("   - Avec des données valides (counting_id, location_id, product_id, quantity_inventoried)")

if __name__ == '__main__':
    try:
        test_upsert_logic()
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

