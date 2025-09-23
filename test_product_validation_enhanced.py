#!/usr/bin/env python3
"""
Test des validations améliorées des propriétés du produit
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/mobile/api"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_enhanced_product_validation():
    """Test des validations améliorées des propriétés du produit"""
    
    print("🧪 Test des validations améliorées des propriétés du produit")
    print("=" * 70)
    
    # 1. Test de connexion
    print("\n1. Test de connexion...")
    
    login_data = {
        "username": "admin",  # Remplacez par un utilisateur valide
        "password": "admin"   # Remplacez par le mot de passe valide
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access_token')
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
    
    # 2. Test produit avec n_lot=True mais n_lot=null (ERREUR ATTENDUE)
    print("\n2. Test produit avec n_lot=True mais n_lot=null...")
    
    data_nlot_null = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Produit avec n_lot=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": None               # n_lot=null (ERREUR ATTENDUE)
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nlot_null,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                if "null n'est pas accepté" in response_data.get('error', ''):
                    print("✅ Validation n_lot=null fonctionne correctement")
                else:
                    print("❌ Message d'erreur incorrect")
            else:
                print("❌ Type d'erreur incorrect")
        else:
            print("❌ Validation n_lot=null ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Test produit avec n_lot=True et n_lot="" (ERREUR ATTENDUE)
    print("\n3. Test produit avec n_lot=True mais n_lot=''...")
    
    data_nlot_empty = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Produit avec n_lot=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": ""                 # n_lot vide (ERREUR ATTENDUE)
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nlot_empty,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                if "null n'est pas accepté" in response_data.get('error', ''):
                    print("✅ Validation n_lot='' fonctionne correctement")
                else:
                    print("❌ Message d'erreur incorrect")
            else:
                print("❌ Type d'erreur incorrect")
        else:
            print("❌ Validation n_lot='' ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 4. Test produit avec n_lot=True et n_lot valide (SUCCÈS ATTENDU)
    print("\n4. Test produit avec n_lot=True et n_lot valide...")
    
    data_nlot_valid = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Produit avec n_lot=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": "LOT123"          # n_lot valide
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nlot_valid,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Création réussie avec n_lot valide")
        else:
            print("❌ Erreur lors de la création avec n_lot valide")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 5. Test avec numéro de série dupliqué (ERREUR ATTENDUE)
    print("\n5. Test avec numéro de série dupliqué...")
    
    data_nserie_duplicate = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 3942,
        "quantity_inventoried": 10,
        "assignment_id": 33,
        "product_id": 13118,        # Produit avec n_lot=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": "LOT456",         # n_lot valide
        "numeros_serie": [          # Numéro de série qui pourrait être dupliqué
            {"n_serie": "NS001-2024"}
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nserie_duplicate,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                if "déjà utilisé" in response_data.get('error', ''):
                    print("✅ Validation numéro de série dupliqué fonctionne")
                else:
                    print("❌ Message d'erreur incorrect")
            else:
                print("❌ Type d'erreur incorrect")
        elif response.status_code == 201:
            print("✅ Création réussie (numéro de série non dupliqué)")
        else:
            print("❌ Statut inattendu")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Tests de validation améliorée terminés")
    print("\nNote: Ces tests vérifient que null et chaînes vides ne sont pas acceptés")

if __name__ == "__main__":
    test_enhanced_product_validation()
