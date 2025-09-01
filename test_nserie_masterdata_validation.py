#!/usr/bin/env python3
"""
Test de validation des numéros de série dans masterdata
"""

import requests
import json

def test_nserie_masterdata_validation():
    """Test de validation des numéros de série dans masterdata"""
    
    print("🧪 Test de validation des numéros de série dans masterdata")
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
    
    # 2. Test avec numéro de série inexistant dans masterdata
    print("\n2. Test avec numéro de série inexistant dans masterdata...")
    
    data_nserie_inexistant = {
        "counting_id": 17,                    # Mode "par article"
        "location_id": 3930,                  # Obligatoire
        "quantity_inventoried": 10,           # Obligatoire
        "assignment_id": 55,                  # OBLIGATOIRE
        "product_id": 13118,                  # Produit avec n_serie=True
        "dlc": "2024-12-31",                 # DLC fournie
        "n_lot": "LOT123",                   # n_lot fourni
        "numeros_serie": [                    # Numéro de série inexistant
            {"n_serie": "NS999-INEXISTANT"}
        ]
    }
    
    print("📤 Envoi des données:")
    print(json.dumps(data_nserie_inexistant, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data_nserie_inexistant,
            headers=headers
        )
        
        print(f"\n📥 Réponse reçue:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            try:
                response_data = response.json()
                error_msg = response_data.get('error', '')
                error_type = response_data.get('error_type', '')
                
                print(f"\n📋 Analyse de l'erreur:")
                print(f"   Type: {error_type}")
                print(f"   Message: {error_msg}")
                
                if "n'existe pas dans masterdata" in error_msg:
                    print("✅ SUCCÈS: Validation masterdata fonctionne - numéro de série inexistant rejeté")
                elif "déjà utilisé" in error_msg:
                    print("✅ SUCCÈS: Validation duplication fonctionne")
                else:
                    print("❌ Type d'erreur inattendu")
                    
            except:
                print("❌ Impossible de parser la réponse JSON")
                
        elif response.status_code == 201:
            print("❌ PROBLÈME: Création réussie malgré numéro de série inexistant")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Test avec numéro de série valide dans masterdata
    print("\n3. Test avec numéro de série valide dans masterdata...")
    
    data_nserie_valide = {
        "counting_id": 17,                    # Mode "par article"
        "location_id": 3930,                  # Obligatoire
        "quantity_inventoried": 10,           # Obligatoire
        "assignment_id": 55,                  # OBLIGATOIRE
        "product_id": 13118,                  # Produit avec n_serie=True
        "dlc": "2024-12-31",                 # DLC fournie
        "n_lot": "LOT456",                   # n_lot fourni
        "numeros_serie": [                    # Numéro de série valide (à adapter selon vos données)
            {"n_serie": "NS001-2024"}
        ]
    }
    
    print("📤 Envoi des données:")
    print(json.dumps(data_nserie_valide, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data_nserie_valide,
            headers=headers
        )
        
        print(f"\n📥 Réponse reçue:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCÈS: Création réussie avec numéro de série valide")
        elif response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', '')
            print(f"❌ Erreur de validation: {error_msg}")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_nserie_masterdata_validation()
