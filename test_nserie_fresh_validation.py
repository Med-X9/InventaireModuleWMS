#!/usr/bin/env python3
"""
Test de validation avec un numéro de série frais (existant dans masterdata mais non utilisé)
"""

import requests
import json

def test_nserie_fresh_validation():
    """Test avec un numéro de série valide et non utilisé"""
    
    print("🧪 Test de validation avec numéro de série frais")
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
    
    # 2. Test avec numéro de série frais (existant dans masterdata, non utilisé)
    print("\n2. Test avec numéro de série frais...")
    
    # Utilisez un numéro de série qui existe dans masterdata mais qui n'est pas encore utilisé
    # Vous devez adapter ce numéro selon vos données réelles
    data_nserie_frais = {
        "counting_id": 17,                    # Mode "par article"
        "location_id": 3930,                  # Obligatoire
        "quantity_inventoried": 10,           # Obligatoire
        "assignment_id": 55,                  # OBLIGATOIRE
        "product_id": 13118,                  # Produit avec n_serie=True
        "dlc": "2024-12-31",                 # DLC fournie
        "n_lot": "LOT789",                   # n_lot fourni
        "numeros_serie": [                    # Numéro de série frais (à adapter)
            {"n_serie": "NS-FRESH-2024"}
        ]
    }
    
    print("📤 Envoi des données:")
    print(json.dumps(data_nserie_frais, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data_nserie_frais,
            headers=headers
        )
        
        print(f"\n📥 Réponse reçue:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCÈS: Création réussie avec numéro de série frais")
            print("🎯 La validation masterdata + duplication fonctionne parfaitement !")
        elif response.status_code == 400:
            response_data = response.json()
            error_msg = response_data.get('error', '')
            error_type = response_data.get('error_type', '')
            
            print(f"\n📋 Analyse de l'erreur:")
            print(f"   Type: {error_type}")
            print(f"   Message: {error_msg}")
            
            if "n'existe pas dans masterdata" in error_msg:
                print("❌ Le numéro de série n'existe pas dans masterdata")
                print("💡 Vous devez utiliser un numéro de série qui existe dans masterdata.NSerie")
            elif "déjà utilisé" in error_msg:
                print("❌ Le numéro de série est déjà utilisé")
                print("💡 Vous devez utiliser un numéro de série qui n'est pas encore utilisé")
            else:
                print("❌ Autre erreur de validation")
                
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Test terminé")
    print("\n💡 Pour que ce test fonctionne, vous devez :")
    print("   1. Vérifier qu'un numéro de série existe dans masterdata.NSerie pour le produit 13118")
    print("   2. Vérifier que ce numéro de série n'est pas encore utilisé dans CountingDetail")
    print("   3. Adapter le numéro de série dans le test")

if __name__ == "__main__":
    test_nserie_fresh_validation()
