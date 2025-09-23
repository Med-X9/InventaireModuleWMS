#!/usr/bin/env python3
"""
Test spécifique pour la validation des propriétés du produit
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/mobile/api"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_product_properties_validation():
    """Test de la validation des propriétés du produit"""
    
    print("🧪 Test de validation des propriétés du produit")
    print("=" * 60)
    
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
    
    # 2. Test produit avec DLC requise
    print("\n2. Test produit avec DLC requise...")
    
    data_dlc_requise = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 1,
        "quantity_inventoried": 5,
        "assignment_id": 1,
        "product_id": 2             # Produit avec dlc=True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_dlc_requise,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                print("✅ Validation DLC fonctionne correctement")
            else:
                print("❌ Type d'erreur incorrect")
        else:
            print("❌ Validation DLC ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Test produit avec numéro de lot requis
    print("\n3. Test produit avec numéro de lot requis...")
    
    data_nlot_requis = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 1,
        "quantity_inventoried": 5,
        "assignment_id": 1,
        "product_id": 3,            # Produit avec n_lot=True
        "dlc": "2024-12-31"        # DLC fournie
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nlot_requis,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                print("✅ Validation n_lot fonctionne correctement")
            else:
                print("❌ Type d'erreur incorrect")
        else:
            print("❌ Validation n_lot ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 4. Test produit avec numéros de série requis
    print("\n4. Test produit avec numéros de série requis...")
    
    data_nserie_requis = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 1,
        "quantity_inventoried": 5,
        "assignment_id": 1,
        "product_id": 4,            # Produit avec n_serie=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": "LOT456"          # n_lot fourni
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_nserie_requis,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if response_data.get('error_type') == 'product_property_error':
                print("✅ Validation n_serie fonctionne correctement")
            else:
                print("❌ Type d'erreur incorrect")
        else:
            print("❌ Validation n_serie ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 5. Test produit avec toutes les propriétés remplies
    print("\n5. Test produit avec toutes les propriétés remplies...")
    
    data_complet = {
        "counting_id": 1,           # Comptage en mode "par article"
        "location_id": 1,
        "quantity_inventoried": 5,
        "assignment_id": 1,
        "product_id": 5,            # Produit avec dlc=True, n_lot=True, n_serie=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": "LOT789",         # n_lot fourni
        "numeros_serie": [          # numéros de série fournis
            {"n_serie": "NS001-2024"},
            {"n_serie": "NS002-2024"}
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_complet,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Création réussie avec toutes les propriétés")
        else:
            print("❌ Erreur lors de la création")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Tests de validation des propriétés terminés")
    print("\nNote: Assurez-vous d'avoir des produits avec les bonnes propriétés dans votre base de données")

if __name__ == "__main__":
    test_product_properties_validation()
