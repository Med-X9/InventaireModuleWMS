#!/usr/bin/env python3
"""
Exemple de test pour la validation d'import de stock selon le type d'inventaire.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
INVENTORY_ID = 1  # À adapter selon votre environnement



def test_stock_import_with_validation():
    """
    Test d'import de stock avec validation selon le type d'inventaire.
    """
    print("=== Test d'import de stock avec validation ===")
    
    url = f"{BASE_URL}/inventory/{INVENTORY_ID}/stocks/import/"
    
    # Créer un fichier Excel de test (simulation)
    # En réalité, vous devriez créer un vrai fichier Excel
    test_file_data = {
        'article': ['PROD001', 'PROD002', 'PROD003'],
        'emplacement': ['LOC001', 'LOC002', 'LOC003'],
        'quantite': [10, 20, 30]
    }
    
    # Simuler l'upload d'un fichier
    files = {
        'file': ('test_stocks.xlsx', open('test_stocks.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Succès - Import de stock réussi")
            print(f"Type d'inventaire: {data.get('inventory_type')}")
            print(f"Message: {data.get('message')}")
            
            if 'summary' in data:
                summary = data['summary']
                print(f"Total lignes: {summary.get('total_rows')}")
                print(f"Lignes valides: {summary.get('valid_rows')}")
                print(f"Lignes invalides: {summary.get('invalid_rows')}")
                
        elif response.status_code == 400:
            data = response.json()
            print("⚠️ Import refusé - Validation échouée")
            print(f"Type d'inventaire: {data.get('inventory_type')}")
            print(f"Message: {data.get('message')}")
            print(f"Stocks existants: {data.get('existing_stocks_count')}")
            
            if data.get('action_required'):
                print(f"Action requise: {data.get('action_required')}")
                
        else:
            print("❌ Erreur lors de l'import")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_inventory_not_found():
    """
    Test avec un inventaire inexistant.
    """
    print("\n=== Test avec inventaire inexistant ===")
    
    invalid_inventory_id = 99999
    url = f"{BASE_URL}/inventory/{invalid_inventory_id}/stocks/import/status/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            print("✅ Succès - Inventaire non trouvé correctement géré")
            print(f"Message: {data.get('message')}")
        else:
            print("❌ Erreur - Gestion incorrecte de l'inventaire inexistant")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def create_test_excel_file():
    """
    Crée un fichier Excel de test pour les tests.
    """
    import pandas as pd
    
    # Données de test
    data = {
        'article': ['PROD001', 'PROD002', 'PROD003', 'PROD004', 'PROD005'],
        'emplacement': ['LOC001', 'LOC002', 'LOC003', 'LOC004', 'LOC005'],
        'quantite': [10, 20, 30, 40, 50]
    }
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Sauvegarder en Excel
    df.to_excel('test_stocks.xlsx', index=False)
    print("✅ Fichier Excel de test créé: test_stocks.xlsx")

def main():
    """
    Fonction principale pour exécuter tous les tests.
    """
    print("🚀 Démarrage des tests de validation d'import de stock")
    print("=" * 60)
    
    # Créer le fichier de test
    create_test_excel_file()
    
    # Exécuter les tests
    test_stock_import_with_validation()
    test_inventory_not_found()
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    main() 