#!/usr/bin/env python3
"""
Test de l'API CountingDetail avec authentification
"""

import requests
import json

def test_api_with_auth():
    """Test de l'API avec authentification"""
    
    print("🧪 Test de l'API CountingDetail avec authentification")
    print("=" * 60)
    
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
            token = response.json().get('access')  # Utiliser 'access' au lieu de 'access_token'
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            print("✅ Connexion réussie")
            print(f"   Token: {token[:50]}...")  # Afficher le début du token
        else:
            print(f"❌ Échec de la connexion: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # 2. Test avec votre exemple exact
    print("\n2. Test avec votre exemple exact...")
    
    data = {
        "counting_id": 1,                    # Obligatoire
        "location_id": 3942,                 # Obligatoire
        "quantity_inventoried": 10,          # Obligatoire
        "assignment_id": 33,                 # OBLIGATOIRE (nouveau)
        "product_id": 13118,                 # Optionnel (selon le mode)
        "dlc": "2024-12-31",                # Optionnel
        "n_lot": None,                       # Optionnel (MAIS ERREUR si product.n_lot=True)
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
            print("✅ SUCCÈS: Création réussie (produit n'a pas n_lot=True)")
        else:
            print(f"❌ Statut inattendu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_api_with_auth()
