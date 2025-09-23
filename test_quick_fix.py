#!/usr/bin/env python3
"""
Test rapide pour vérifier la correction de l'erreur job_detail.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/mobile/api"
LOGIN_URL = f"{BASE_URL}/auth/jwt-login/"
COUNTING_DETAIL_URL = f"{BASE_URL}/counting-detail/"

def test_quick_fix():
    """Test rapide avec 2 enregistrements."""
    
    # 1. Connexion
    print("🔐 Connexion...")
    login_data = {
        "username": "testuser_api",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data['access']
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                print("✅ Connexion réussie")
            else:
                print(f"❌ Erreur de connexion: {data.get('error')}")
                return
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return
    
    # 2. Test avec 2 enregistrements
    print("\n📝 Test de création avec 2 enregistrements...")
    
    test_data = {
        "batch": True,
        "data": [
            {
                "counting_id": 17,
                "location_id": 3930,
                "quantity_inventoried": 5,
                "assignment_id": 55,
                "product_id": 13118,
                "dlc": "2024-12-31",
                "n_lot": "LOT123",
                "numeros_serie": [
                    {"n_serie": "NS_TEST_001"}
                ]
            },
            {
                "counting_id": 2,
                "location_id": 3596,
                "quantity_inventoried": 8,
                "assignment_id": 52,
                "product_id": 11329,
                "dlc": "2024-12-31",
                "n_lot": "LOT001",
                "numeros_serie": [
                    {"n_serie": "NS_TEST_002"}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(COUNTING_DETAIL_URL, json=test_data, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                result = data['data']
                print(f"✅ Test réussi:")
                print(f"   - Total traité: {result['total_processed']}")
                print(f"   - Réussis: {result['successful']}")
                print(f"   - Échecs: {result['failed']}")
                
                if result['results']:
                    print(f"   - Actions effectuées:")
                    for item in result['results']:
                        action = item['result']['action']
                        print(f"     * Index {item['index']}: {action}")
                
                if result['errors']:
                    print(f"   - Erreurs:")
                    for error in result['errors'][:3]:  # Afficher les 3 premières erreurs
                        print(f"     * Index {error['index']}: {error['error']}")
                
                print("\n🎉 La correction fonctionne !")
                return True
            else:
                print(f"❌ Échec: {data.get('error')}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    test_quick_fix()
