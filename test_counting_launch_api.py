"""
Script de test pour l'API de lancement de comptage avec le nouveau format jobs[]
Usage: python test_counting_launch_api.py
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/inventory"  # Ajustez selon votre configuration
API_ENDPOINT = f"{BASE_URL}/jobs/launch-counting/"

# Vous devrez obtenir un token d'authentification
# Remplacez par votre token ou utilisez les credentials
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"  # À remplacer

def test_old_format():
    """Test de l'ancien format (job_id, location_id, session_id)"""
    print("\n=== Test de l'ancien format ===")
    
    payload = {
        "job_id": 1,  # Remplacez par un ID de job valide
        "location_id": 1,  # Remplacez par un ID d'emplacement valide
        "session_id": 1,  # Remplacez par un ID de session valide
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200 or response.status_code == 201
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def test_new_format_success():
    """Test du nouveau format avec jobs[] - cas de succès"""
    print("\n=== Test du nouveau format (jobs[]) - Cas de succès ===")
    
    payload = {
        "jobs": [1, 2],  # Remplacez par des IDs de jobs valides qui ont des emplacements avec écart
        "session_id": 1,  # Remplacez par un ID de session valide
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # Si c'est un fichier Excel (succès)
        if response.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            print("✓ Succès! Fichier Excel reçu")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            # Optionnel: sauvegarder le fichier
            # with open('export_test.xlsx', 'wb') as f:
            #     f.write(response.content)
            return True
        else:
            # Si c'est une réponse JSON (erreur ou autre)
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return False
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def test_new_format_no_ecart():
    """Test du nouveau format avec jobs[] - aucun écart trouvé"""
    print("\n=== Test du nouveau format (jobs[]) - Aucun écart ===")
    
    payload = {
        "jobs": [999],  # Remplacez par un ID de job qui n'a pas d'emplacements avec écart
        "session_id": 1,
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 400  # Devrait retourner une erreur
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def test_validation_error():
    """Test de validation - format invalide"""
    print("\n=== Test de validation - Format invalide ===")
    
    payload = {
        "jobs": [],  # Liste vide
        "session_id": 1,
    }
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 400  # Devrait retourner une erreur de validation
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def main():
    """Fonction principale pour exécuter tous les tests"""
    print("=" * 60)
    print("Tests de l'API de lancement de comptage")
    print("=" * 60)
    
    if AUTH_TOKEN == "YOUR_AUTH_TOKEN_HERE":
        print("\n⚠️  ATTENTION: Vous devez configurer AUTH_TOKEN dans le script")
        print("   ou utiliser une autre méthode d'authentification")
        sys.exit(1)
    
    results = []
    
    # Tests
    # results.append(("Ancien format", test_old_format()))
    # results.append(("Nouveau format - Succès", test_new_format_success()))
    # results.append(("Nouveau format - Aucun écart", test_new_format_no_ecart()))
    results.append(("Validation - Format invalide", test_validation_error()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("Résumé des tests:")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print("Pour tester avec vos propres données:")
    print("1. Modifiez les IDs dans les fonctions de test")
    print("2. Configurez AUTH_TOKEN avec votre token d'authentification")
    print("3. Ajustez BASE_URL si nécessaire")
    print("=" * 60)

if __name__ == "__main__":
    main()

