#!/usr/bin/env python3
"""
Test de la création des numéros de série après correction
"""

import requests
import json

def test_nserie_creation_fixed():
    """Test de la création des numéros de série après correction"""
    
    print("🧪 Test de la création des numéros de série après correction")
    print("=" * 70)
    
    # 1. Test de connexion
    print("\n1. Test de connexion...")
    
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access')
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            print("✅ Connexion réussie")
        else:
            print(f"❌ Échec de la connexion: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 2. Test avec numéros de série
    print("\n2. Test avec numéros de série...")
    
    data_test = {
        "counting_id": 17,                    # Mode "par article" (n_serie=False)
        "location_id": 3930,                  # Obligatoire
        "quantity_inventoried": 15,           # Obligatoire
        "assignment_id": 55,                  # OBLIGATOIRE
        "product_id": 13118,                  # Produit avec n_serie=True
        "dlc": "2024-12-31",                 # DLC fournie
        "n_lot": "LOT456",                   # n_lot fourni
        "numeros_serie": [                    # Numéro de série valide dans masterdata
            {"n_serie": "1234567iuytr"}
        ]
    }
    
    print("📤 Envoi des données:")
    print(json.dumps(data_test, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data_test,
            headers=headers
        )
        
        print(f"\n📥 Réponse reçue:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            response_data = response.json()
            numeros_serie = response_data.get('data', {}).get('numeros_serie', [])
            
            print(f"\n📋 Analyse de la réponse:")
            print(f"   ✅ Création réussie")
            print(f"   📱 Numéros de série créés: {len(numeros_serie)}")
            
            if len(numeros_serie) > 0:
                print("   🎯 SUCCÈS: Les numéros de série sont maintenant créés!")
                for ns in numeros_serie:
                    print(f"      - {ns['n_serie']} (ID: {ns['id']})")
            else:
                print("   ❌ PROBLÈME: Aucun numéro de série créé malgré la correction")
                
        elif response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', '')
            print(f"\n❌ Erreur de validation: {error_msg}")
            
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_nserie_creation_fixed()
