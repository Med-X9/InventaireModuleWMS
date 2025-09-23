#!/usr/bin/env python3
"""
Test de validation avec un counting en mode "par article"
"""

import requests
import json

def test_validation_par_article():
    """Test de validation avec un counting en mode 'par article'"""
    
    print("🧪 Test de validation avec counting en mode 'par article'")
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
    
    # 2. Test avec counting_id=2 (mode "par article") et n_lot=null
    print("\n2. Test avec counting_id=2 (mode 'par article') et n_lot=null...")
    
    data = {
        "counting_id": 2,                    # Mode "par article" - validation des propriétés activée
        "location_id": 3942,                 # Obligatoire
        "quantity_inventoried": 10,          # Obligatoire
        "assignment_id": 33,                 # OBLIGATOIRE
        "product_id": 13118,                 # OBLIGATOIRE en mode "par article"
        "dlc": "2024-12-31",                # Optionnel
        "n_lot": None,                       # ERREUR ATTENDUE si product.n_lot=True
        "numeros_serie": [                   # Optionnel
            {"n_serie": "NS001-2024"}
        ]
    }
    
    print("📤 Envoi des données:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:8000/mobile/api/counting-detail/',
            json=data,
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
                
                if "null n'est pas accepté" in error_msg:
                    print("✅ SUCCÈS: Validation null fonctionne - le produit nécessite un n_lot valide")
                elif "déjà utilisé" in error_msg:
                    print("✅ SUCCÈS: Validation numéro de série dupliqué fonctionne")
                else:
                    print("❌ Type d'erreur inattendu")
                    
            except:
                print("❌ Impossible de parser la réponse JSON")
                
        elif response.status_code == 201:
            print("❌ PROBLÈME: Création réussie malgré n_lot=null")
            print("   La validation des propriétés du produit ne fonctionne pas")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_validation_par_article()
