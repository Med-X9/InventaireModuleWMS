#!/usr/bin/env python3
"""
Script de test pour l'API des stocks
Teste l'API pour récupérer les stocks du même compte qu'un utilisateur
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/mobile/user/3/stocks/"  # Test avec user_id=3

def test_stocks_api():
    """Test de l'API des stocks"""
    print("=== Test de l'API des stocks ===")
    print(f"URL: {API_URL}")
    print()
    
    try:
        # Faire la requête GET
        response = requests.get(API_URL)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        # Afficher la réponse
        if response.status_code == 200:
            data = response.json()
            print("✅ Réponse réussie:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Analyser les données
            if data.get('success'):
                stocks = data.get('data', {}).get('stocks', [])
                print(f"\n📊 Nombre de stocks trouvés: {len(stocks)}")
                
                if stocks:
                    print("\n📋 Détails des stocks:")
                    for i, stock in enumerate(stocks[:3], 1):  # Afficher les 3 premiers
                        print(f"  Stock {i}:")
                        print(f"    - ID: {stock.get('web_id')}")
                        print(f"    - Référence: {stock.get('reference')}")
                        print(f"    - Location: {stock.get('location_reference')}")
                        print(f"    - Produit: {stock.get('product_name')}")
                        print(f"    - Quantité disponible: {stock.get('quantity_available')}")
                        print(f"    - Unité: {stock.get('unit_name')}")
                        print()
                    
                    if len(stocks) > 3:
                        print(f"  ... et {len(stocks) - 3} autres stocks")
                else:
                    print("ℹ️  Aucun stock trouvé pour cet utilisateur")
            else:
                print("❌ Erreur dans la réponse:")
                print(f"   - Message: {data.get('error')}")
                print(f"   - Type: {data.get('error_type')}")
        else:
            print("❌ Erreur HTTP:")
            print(f"   - Status: {response.status_code}")
            print(f"   - Contenu: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion: Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Django est démarré sur http://localhost:8000")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de décodage JSON: {e}")
        print(f"   Réponse brute: {response.text}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    test_stocks_api() 