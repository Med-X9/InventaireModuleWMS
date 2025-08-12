#!/usr/bin/env python3
"""
Script de test simple pour les APIs Mobile
Usage: python test_mobile_apis_simple.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/mobile"

def print_response(response, title=""):
    """Affiche la réponse de l'API de manière formatée"""
    print(f"\n{'='*50}")
    print(f"📡 {title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print(f"{'='*50}\n")

def test_login():
    """Test de connexion"""
    print("🔐 Test de connexion...")
    
    login_data = {
        "username": "admin",  # Remplacez par un utilisateur existant
        "password": "admin123"  # Remplacez par le mot de passe correct
    }
    
    response = requests.post(f"{API_BASE}/auth/login/", 
                           json=login_data, 
                           headers={'Content-Type': 'application/json'})
    print_response(response, "Login")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Login réussi!")
            return data.get('access')
        else:
            print("❌ Login échoué!")
            return None
    else:
        print("❌ Erreur de connexion!")
        return None

def test_sync_data(token):
    """Test de synchronisation des données"""
    print("📥 Test de synchronisation des données...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{API_BASE}/sync/data/", headers=headers)
    print_response(response, "Sync Data")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Synchronisation réussie!")
            print(f"📊 Données récupérées:")
            print(f"   - Inventaires: {len(data['data'].get('inventories', []))}")
            print(f"   - Jobs: {len(data['data'].get('jobs', []))}")
            print(f"   - Assignations: {len(data['data'].get('assignments', []))}")
            print(f"   - Comptages: {len(data['data'].get('countings', []))}")
            print(f"   - Produits: {len(data['data'].get('products', []))}")
            print(f"   - Emplacements: {len(data['data'].get('locations', []))}")
            print(f"   - Stocks: {len(data['data'].get('stocks', []))}")
            return data['data']
        else:
            print("❌ Synchronisation échouée!")
            return None
    else:
        print("❌ Erreur de synchronisation!")
        return None

def test_upload_data(token):
    """Test d'upload des données"""
    print("📤 Test d'upload des données...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    upload_data = {
        "sync_id": f"test_sync_{int(time.time())}",
        "countings": [
            {
                "detail_id": f"detail_{int(time.time())}",
                "quantite_comptee": 25,
                "product_web_id": 1,  # Remplacez par un ID de produit existant
                "location_web_id": 1,  # Remplacez par un ID d'emplacement existant
                "numero_lot": "LOT-TEST-2024",
                "numero_serie": None,
                "dlc": "2024-12-31",
                "compte_par_web_id": 1,  # Remplacez par un ID de personne existant
                "date_comptage": datetime.now().isoformat()
            }
        ],
        "assignments": [
            {
                "assignment_web_id": 1,  # Remplacez par un ID d'assignation existant
                "status": "ENTAME",
                "entame_date": datetime.now().isoformat(),
                "date_start": datetime.now().isoformat()
            }
        ]
    }
    
    response = requests.post(f"{API_BASE}/sync/upload/", 
                           json=upload_data, 
                           headers=headers)
    print_response(response, "Upload Data")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Upload réussi!")
            print(f"📊 Éléments uploadés: {data.get('uploaded_count', 0)}")
            if data.get('errors'):
                print(f"⚠️ Erreurs: {data['errors']}")
            if data.get('conflicts'):
                print(f"⚠️ Conflits: {data['conflicts']}")
            return True
        else:
            print("❌ Upload échoué!")
            return False
    else:
        print("❌ Erreur d'upload!")
        return False

def test_logout(token):
    """Test de déconnexion"""
    print("🚪 Test de déconnexion...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{API_BASE}/auth/logout/", headers=headers)
    print_response(response, "Logout")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Déconnexion réussie!")
            return True
        else:
            print("❌ Déconnexion échouée!")
            return False
    else:
        print("❌ Erreur de déconnexion!")
        return False

def run_tests():
    """Exécute tous les tests"""
    print("🚀 Démarrage des tests des APIs Mobile")
    print(f"📍 URL de base: {BASE_URL}")
    print(f"📡 API Mobile: {API_BASE}")
    
    # Test 1: Authentification
    token = test_login()
    if not token:
        print("❌ Échec de l'authentification. Arrêt des tests.")
        return
    
    # Test 2: Synchronisation des données
    sync_data = test_sync_data(token)
    if not sync_data:
        print("❌ Échec de la synchronisation. Arrêt des tests.")
        return
    
    # Test 3: Upload des données
    test_upload_data(token)
    
    # Test 4: Déconnexion
    test_logout(token)
    
    print("🎉 Tests terminés!")

if __name__ == "__main__":
    run_tests() 