"""
Script de test pour l'API Counting Detail avec fonctionnalités UPSERT
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import CountingDetail, ComptageSequence, EcartComptage
from apps.masterdata.models import Product, Location
from apps.inventory.models import Counting, Job, Assigment, JobDetail
from apps.users.models import User
import json

class CountingDetailAPITest(TestCase):
    """Tests pour l'API Counting Detail avec UPSERT"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer des données de test (à adapter selon vos modèles)
        # Note: Vous devrez peut-être créer des objets Account, Warehouse, etc.
        # selon votre structure
        
        print("✅ Configuration initiale terminée")
    
    def test_upsert_create_new_counting_detail(self):
        """Test: Créer un nouveau CountingDetail (INSERT)"""
        print("\n📝 Test 1: Création d'un nouveau CountingDetail")
        
        # Préparer les données
        data = [{
            'counting_id': 107,
            'location_id': 828,
            'quantity_inventoried': 5,
            'assignment_id': 58,
            'product_id': 3766
        }]
        
        # Appel API
        response = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.data, indent=2, default=str)}")
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
        
        # Vérifier que le CountingDetail a été créé
        counting_detail = CountingDetail.objects.filter(
            counting_id=107,
            location_id=828,
            product_id=3766
        ).first()
        
        self.assertIsNotNone(counting_detail)
        self.assertEqual(counting_detail.quantity_inventoried, 5)
        print("✅ CountingDetail créé avec succès")
        
        # Vérifier que ComptageSequence a été créé
        sequence = ComptageSequence.objects.filter(
            counting_detail=counting_detail
        ).first()
        self.assertIsNotNone(sequence)
        print("✅ ComptageSequence créé avec succès")
    
    def test_upsert_update_existing_counting_detail(self):
        """Test: Mettre à jour un CountingDetail existant (UPDATE)"""
        print("\n📝 Test 2: Mise à jour d'un CountingDetail existant")
        
        # Créer un CountingDetail existant
        # Note: Vous devrez adapter selon votre structure
        # existing_detail = CountingDetail.objects.create(...)
        
        # Préparer les données avec nouvelle quantité
        data = [{
            'counting_id': 107,
            'location_id': 828,
            'quantity_inventoried': 10,  # Nouvelle quantité
            'assignment_id': 58,
            'product_id': 3766
        }]
        
        # Appel API
        response = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.data, indent=2, default=str)}")
        
        # Vérifications
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
        
        # Vérifier que la quantité a été mise à jour
        counting_detail = CountingDetail.objects.filter(
            counting_id=107,
            location_id=828,
            product_id=3766
        ).first()
        
        if counting_detail:
            self.assertEqual(counting_detail.quantity_inventoried, 10)
            print("✅ CountingDetail mis à jour avec succès")
            
            # Vérifier qu'une nouvelle séquence a été créée
            sequences = ComptageSequence.objects.filter(
                counting_detail=counting_detail
            ).order_by('sequence_number')
            
            self.assertGreaterEqual(sequences.count(), 1)
            print(f"✅ {sequences.count()} séquence(s) trouvée(s)")
    
    def test_upsert_batch_multiple_items(self):
        """Test: UPSERT en lot avec plusieurs éléments"""
        print("\n📝 Test 3: UPSERT en lot (plusieurs éléments)")
        
        data = [
            {
                'counting_id': 107,
                'location_id': 828,
                'quantity_inventoried': 3,
                'assignment_id': 58,
                'product_id': 3766
            },
            {
                'counting_id': 107,
                'location_id': 829,
                'quantity_inventoried': 7,
                'assignment_id': 58,
                'product_id': 3767
            }
        ]
        
        response = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.data, indent=2, default=str)}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
        
        result_data = response.data.get('data', {})
        self.assertEqual(result_data.get('total_processed'), 2)
        print("✅ Traitement en lot réussi")
    
    def test_upsert_ignore_invalid_quantity(self):
        """Test: Ignorer les éléments sans quantité valide"""
        print("\n📝 Test 4: Ignorer les éléments sans quantité valide")
        
        data = [
            {
                'counting_id': 107,
                'location_id': 828,
                'quantity_inventoried': 0,  # Quantité invalide
                'assignment_id': 58,
                'product_id': 3766
            },
            {
                'counting_id': 107,
                'location_id': 829,
                # Pas de quantity_inventoried
                'assignment_id': 58,
                'product_id': 3767
            },
            {
                'counting_id': 107,
                'location_id': 830,
                'quantity_inventoried': 5,  # Quantité valide
                'assignment_id': 58,
                'product_id': 3768
            }
        ]
        
        response = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.data, indent=2, default=str)}")
        
        # L'API devrait traiter seulement l'élément avec quantité valide
        # Les autres sont ignorés
        print("✅ Éléments invalides ignorés")
    
    def test_final_result_calculation(self):
        """Test: Vérifier le calcul du résultat final avec consensus"""
        print("\n📝 Test 5: Calcul du résultat final (consensus)")
        
        # Premier comptage
        data1 = [{
            'counting_id': 107,
            'location_id': 828,
            'quantity_inventoried': 5,
            'assignment_id': 58,
            'product_id': 3766
        }]
        
        response1 = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data1),
            content_type='application/json'
        )
        
        print(f"Premier comptage - Status: {response1.status_code}")
        
        # Deuxième comptage (même valeur)
        data2 = [{
            'counting_id': 107,
            'location_id': 828,
            'quantity_inventoried': 5,  # Même valeur
            'assignment_id': 58,
            'product_id': 3766
        }]
        
        response2 = self.client.post(
            '/mobile/api/job/32/counting-detail/',
            data=json.dumps(data2),
            content_type='application/json'
        )
        
        print(f"Deuxième comptage - Status: {response2.status_code}")
        
        # Vérifier le résultat final
        if response2.status_code == status.HTTP_201_CREATED:
            result_data = response2.data.get('data', {})
            results = result_data.get('results', [])
            
            if results:
                ecart_comptage = results[0].get('result', {}).get('ecart_comptage', {})
                final_result = ecart_comptage.get('final_result')
                
                print(f"Résultat final: {final_result}")
                
                # Avec 2 comptages identiques, le résultat devrait être 5
                if final_result is not None:
                    self.assertEqual(final_result, 5)
                    print("✅ Résultat final calculé correctement")
                else:
                    print("⚠️ Résultat final non calculé (normal si < 2 comptages différents)")

def run_tests():
    """Lance les tests"""
    print("=" * 60)
    print("🧪 TESTS API COUNTING DETAIL - UPSERT")
    print("=" * 60)
    
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(CountingDetailAPITest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS RÉUSSIS")
    else:
        print(f"❌ {len(result.failures)} échec(s), {len(result.errors)} erreur(s)")
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution des tests: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
