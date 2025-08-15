#!/usr/bin/env python3
"""
Test de l'API CountingDetail avec authentification
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/mobile/api"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_counting_detail_api():
    """Test de l'API CountingDetail"""
    
    print("🧪 Test de l'API CountingDetail")
    print("=" * 50)
    
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
    
    # 2. Test de création de CountingDetail (mode en vrac - article non obligatoire)
    print("\n2. Test de création de CountingDetail (mode en vrac)...")
    
    data_en_vrac = {
        "counting_id": 1,           # Remplacez par un ID valide
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 10,
        "assignment_id": 1,         # Remplacez par un ID valide
        "dlc": "2024-12-31",
        "n_lot": "LOT123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_en_vrac,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ CountingDetail créé en mode vrac")
        else:
            print("❌ Erreur de création en mode vrac")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Test de création de CountingDetail (mode par article - article obligatoire)
    print("\n3. Test de création de CountingDetail (mode par article)...")
    
    data_par_article = {
        "counting_id": 2,           # Remplacez par un ID de comptage en mode "par article"
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 5,
        "assignment_id": 1,         # Remplacez par un ID valide
        "product_id": 1,            # Obligatoire pour ce mode
        "dlc": "2024-12-31"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_par_article,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ CountingDetail créé en mode par article")
        else:
            print("❌ Erreur de création en mode par article")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 4. Test de création avec numéros de série
    print("\n4. Test de création avec numéros de série...")
    
    data_avec_numeros_serie = {
        "counting_id": 3,           # Remplacez par un ID de comptage avec n_serie=True
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 3,
        "assignment_id": 1,         # Remplacez par un ID valide
        "product_id": 1,            # Remplacez par un ID valide
        "numeros_serie": [
            {"n_serie": "NS001-2024"},
            {"n_serie": "NS002-2024"},
            {"n_serie": "NS003-2024"}
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_avec_numeros_serie,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ CountingDetail créé avec numéros de série")
        else:
            print("❌ Erreur de création avec numéros de série")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 5. Test de récupération des CountingDetail
    print("\n5. Test de récupération des CountingDetail...")
    
    try:
        response = requests.get(
            f"{API_BASE}/counting-detail/?counting_id=1",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Récupération des CountingDetail réussie")
        else:
            print("❌ Erreur de récupération")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 6. Test de validation des propriétés du produit
    print("\n6. Test de validation des propriétés du produit...")
    
    # Test avec produit nécessitant DLC mais sans DLC fournie
    data_produit_dlc_requise = {
        "counting_id": 4,           # Remplacez par un ID de comptage en mode "par article"
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 5,
        "assignment_id": 1,         # Remplacez par un ID valide
        "product_id": 2             # Remplacez par un produit avec dlc=True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_produit_dlc_requise,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Validation DLC fonctionne (erreur attendue)")
        else:
            print("❌ Validation DLC ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec produit nécessitant numéro de lot mais sans n_lot fourni
    data_produit_nlot_requis = {
        "counting_id": 4,           # Remplacez par un ID de comptage en mode "par article"
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 5,
        "assignment_id": 1,         # Remplacez par un ID valide
        "product_id": 3,            # Remplacez par un produit avec n_lot=True
        "dlc": "2024-12-31"        # DLC fournie
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_produit_nlot_requis,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Validation n_lot fonctionne (erreur attendue)")
        else:
            print("❌ Validation n_lot ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec produit nécessitant numéros de série mais sans numeros_serie fournis
    data_produit_nserie_requis = {
        "counting_id": 4,           # Remplacez par un ID de comptage en mode "par article"
        "location_id": 1,           # Remplacez par un ID valide
        "quantity_inventoried": 5,
        "assignment_id": 1,         # Remplacez par un ID valide
        "product_id": 4,            # Remplacez par un produit avec n_serie=True
        "dlc": "2024-12-31",       # DLC fournie
        "n_lot": "LOT456"          # n_lot fourni
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/counting-detail/",
            json=data_produit_nserie_requis,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Validation n_serie fonctionne (erreur attendue)")
        else:
            print("❌ Validation n_serie ne fonctionne pas")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Tests terminés")
    print("\nNote: Assurez-vous d'avoir remplacé les IDs par des valeurs valides dans votre base de données")

if __name__ == "__main__":
    test_counting_detail_api()
