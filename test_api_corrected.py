#!/usr/bin/env python3
"""
Test de l'API corrigée
"""

import requests
import json

def test_api_corrected():
    """Test de l'API corrigée"""
    
    print("🧪 Test de l'API corrigée")
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
    
    # 2. Test avec le numéro de série 1234567iuytr
    print("\n2. Test avec le numéro de série 1234567iuytr...")
    
    data_test = {
        "counting_id": 17,                    # Mode "par article"
        "location_id": 3930,                  # Obligatoire
        "quantity_inventoried": 10,           # Obligatoire
        "assignment_id": 55,                  # OBLIGATOIRE
        "product_id": 13118,                  # Produit avec n_serie=True
        "dlc": "2024-12-31",                 # DLC fournie
        "n_lot": "LOT123",                   # n_lot fourni
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
            print("✅ SUCCÈS: Création réussie !")
            print("🎯 Le bug est corrigé - l'API accepte maintenant le numéro de série valide")
        elif response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', '')
            error_type = response_data.get('error_type', '')
            
            print(f"\n📋 Analyse de l'erreur:")
            print(f"   Type: {error_type}")
            print(f"   Message: {error_msg}")
            
            if "déjà utilisé" in error_msg:
                print("❌ Le bug persiste - l'API considère encore le numéro de série comme utilisé")
            else:
                print("❌ Autre erreur de validation")
                
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_api_corrected()
