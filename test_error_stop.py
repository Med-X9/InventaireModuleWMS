#!/usr/bin/env python3
"""
Test pour vérifier que le traitement s'arrête dès qu'il y a une erreur.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/mobile/api"
LOGIN_URL = f"{BASE_URL}/auth/jwt-login/"
COUNTING_DETAIL_URL = f"{BASE_URL}/counting-detail/"

def test_error_stop():
    """Test pour vérifier que le traitement s'arrête dès qu'il y a une erreur."""
    
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
    
    # 2. Test avec 5 enregistrements où le 2ème va échouer
    print("\n📝 Test avec 5 enregistrements (le 2ème va échouer)...")
    
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
                "n_lot": "LOT_OK_1",
                "numeros_serie": [{"n_serie": "NS_OK_001"}]
            },
            {
                "counting_id": 2,
                "location_id": 3596,
                "quantity_inventoried": 8,
                "assignment_id": 52,  # Cet assignment n'a pas de JobDetail pour counting_id 2
                "product_id": 11329,
                "dlc": "2024-12-31",
                "n_lot": "LOT_ERROR_2",
                "numeros_serie": [{"n_serie": "NS_ERROR_002"}]
            },
            {
                "counting_id": 17,
                "location_id": 3930,
                "quantity_inventoried": 3,
                "assignment_id": 55,
                "product_id": 13118,
                "dlc": "2024-12-31",
                "n_lot": "LOT_OK_3",
                "numeros_serie": [{"n_serie": "NS_OK_003"}]
            },
            {
                "counting_id": 17,
                "location_id": 3930,
                "quantity_inventoried": 7,
                "assignment_id": 55,
                "product_id": 13118,
                "dlc": "2024-12-31",
                "n_lot": "LOT_OK_4",
                "numeros_serie": [{"n_serie": "NS_OK_004"}]
            },
            {
                "counting_id": 17,
                "location_id": 3930,
                "quantity_inventoried": 9,
                "assignment_id": 55,
                "product_id": 13118,
                "dlc": "2024-12-31",
                "n_lot": "LOT_OK_5",
                "numeros_serie": [{"n_serie": "NS_OK_005"}]
            }
        ]
    }
    
    try:
        response = requests.post(COUNTING_DETAIL_URL, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            result = data['data']
            
            print(f"\n📊 Résultats:")
            print(f"   - Success: {result['success']}")
            print(f"   - Total traité: {result['total_processed']}")
            print(f"   - Réussis: {result['successful']}")
            print(f"   - Échecs: {result['failed']}")
            
            if 'message' in result:
                print(f"   - Message: {result['message']}")
            
            if result['results']:
                print(f"\n✅ Enregistrements réussis:")
                for item in result['results']:
                    action = item['result']['action']
                    print(f"     * Index {item['index']}: {action}")
            
            if result['errors']:
                print(f"\n❌ Erreurs détectées:")
                for error in result['errors']:
                    print(f"     * Index {error['index']}: {error['error']}")
            
            # Vérifier que le traitement s'est arrêté au bon endroit
            if result['successful'] == 1 and result['failed'] == 1:
                print(f"\n🎉 SUCCÈS: Le traitement s'est arrêté correctement !")
                print(f"   - Seul l'enregistrement 0 a été traité")
                print(f"   - L'enregistrement 1 a échoué et le traitement s'est arrêté")
                print(f"   - Les enregistrements 2, 3, 4 n'ont PAS été traités")
                return True
            else:
                print(f"\n❌ ÉCHEC: Le traitement ne s'est pas arrêté correctement")
                print(f"   - Attendu: 1 réussi, 1 échec")
                print(f"   - Obtenu: {result['successful']} réussi, {result['failed']} échec")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    test_error_stop()
