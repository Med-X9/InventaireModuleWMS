#!/usr/bin/env python3
"""
Test de l'API avec les données corrigées.
"""

import os
import sys
import django
import json
import requests

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

class APITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
    
    def login(self):
        """Se connecter et obtenir le token JWT."""
        login_url = f"{self.base_url}/mobile/api/auth/jwt-login/"
        login_data = {
            "username": "testuser_api",
            "password": "testpass123"
        }
        
        try:
            response = requests.post(login_url, json=login_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data['access']
                    print("✅ Connexion réussie")
                    return True
                else:
                    print(f"❌ Échec de connexion: {data}")
                    return False
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {str(e)}")
            return False
    
    def test_validation(self, data):
        """Test de validation en lot."""
        url = f"{self.base_url}/mobile/api/counting-detail/"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.put(url, json=data, headers=headers)
            print(f"📊 Statut: {response.status_code}")
            print(f"📋 Réponse: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.json()
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return None
    
    def test_creation(self, data):
        """Test de création en lot."""
        url = f"{self.base_url}/mobile/api/counting-detail/"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            print(f"📊 Statut: {response.status_code}")
            print(f"📋 Réponse: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.json()
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return None

def main():
    print("🚀 TEST DE L'API AVEC LES DONNÉES CORRIGÉES")
    print("=" * 60)
    
    # Données corrigées (7 enregistrements valides)
    corrected_data = {
        "batch": True,
        "data": [
            {
                "counting_id": 17,
                "location_id": 3930,
                "quantity_inventoried": 10,
                "assignment_id": 55,
                "product_id": 13118,
                "dlc": "2024-12-31",
                "n_lot": "LOT123",
                "numeros_serie": [{"n_serie": "1234trew"}]
            },
            {
                "counting_id": 29,
                "location_id": 3942,
                "quantity_inventoried": 3,
                "assignment_id": 56,
                "product_id": 11331,
                "numeros_serie": [
                    {"n_serie": "NS002"},
                    {"n_serie": "NS003"}
                ]
            },
            {
                "counting_id": 1,
                "location_id": 3598,
                "quantity_inventoried": 8,
                "assignment_id": 33,
                "product_id": 11332,
                "dlc": "2024-11-30",
                "n_lot": "LOT002"
            },
            {
                "counting_id": 16,
                "location_id": 3599,
                "quantity_inventoried": 12,
                "assignment_id": 54,
                "product_id": 11333
            },
            {
                "counting_id": 1,
                "location_id": 3600,
                "quantity_inventoried": 15,
                "assignment_id": 34,
                "product_id": 11334,
                "dlc": "2025-01-15",
                "n_lot": "LOT003"
            },
            {
                "counting_id": 16,
                "location_id": 3601,
                "quantity_inventoried": 7,
                "assignment_id": 55,
                "product_id": 11335,
                "numeros_serie": [{"n_serie": "NS004"}]
            },
            {
                "counting_id": 29,
                "location_id": 3604,
                "quantity_inventoried": 9,
                "assignment_id": 56,
                "product_id": 11338,
                "dlc": "2024-12-31",
                "n_lot": "LOT005"
            }
        ]
    }
    
    # Données pour validation (sans batch)
    validation_data = {
        "data": corrected_data["data"]
    }
    
    # Initialiser le testeur
    tester = APITester()
    
    # Se connecter
    if not tester.login():
        print("❌ Impossible de se connecter")
        return
    
    # Test de validation
    print(f"\n🔍 TEST DE VALIDATION EN LOT")
    print("-" * 40)
    validation_result = tester.test_validation(validation_data)
    
    if validation_result and validation_result.get('success'):
        print("✅ Validation réussie !")
        
        # Test de création
        print(f"\n🚀 TEST DE CRÉATION EN LOT")
        print("-" * 40)
        creation_result = tester.test_creation(corrected_data)
        
        if creation_result and creation_result.get('success'):
            print("✅ Création réussie !")
            print(f"📊 Total traité: {creation_result['data']['total_processed']}")
            print(f"✅ Réussis: {creation_result['data']['successful']}")
            print(f"❌ Échoués: {creation_result['data']['failed']}")
        else:
            print("❌ Création échouée")
    else:
        print("❌ Validation échouée")

if __name__ == "__main__":
    main()

