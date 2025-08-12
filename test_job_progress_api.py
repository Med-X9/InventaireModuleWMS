#!/usr/bin/env python3
"""
Test script pour les APIs d'avancement des emplacements par job et par counting
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_job_progress_by_counting(job_id):
    """
    Test de l'API d'avancement d'un job par counting
    """
    url = f"{BASE_URL}/jobs/{job_id}/progress-by-counting/"
    
    print(f"\n=== Test de l'avancement du job {job_id} ===")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Job ID: {data['data']['job_id']}")
            print(f"Job Reference: {data['data']['job_reference']}")
            print(f"Inventory Reference: {data['data']['inventory_reference']}")
            print(f"Warehouse: {data['data']['warehouse_name']}")
            
            print("\n📊 Progression par counting:")
            for progress in data['data']['progress_by_counting']:
                print(f"  - Counting {progress['counting_order']} ({progress['counting_count_mode']}):")
                print(f"    • Emplacements terminés: {progress['completed_emplacements']}/{progress['total_emplacements']}")
                print(f"    • Progression: {progress['progress_percentage']}%")
                
                # Afficher quelques détails d'emplacements
                if progress['emplacements_details']:
                    print(f"    • Détails des emplacements:")
                    for i, emp in enumerate(progress['emplacements_details'][:3]):  # Limiter à 3 pour la lisibilité
                        print(f"      - {emp['location_reference']}: {emp['status']}")
                    if len(progress['emplacements_details']) > 3:
                        print(f"      ... et {len(progress['emplacements_details']) - 3} autres")
        else:
            print("❌ Erreur!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_inventory_progress_by_counting(inventory_id):
    """
    Test de l'API d'avancement global d'un inventaire par counting
    """
    url = f"{BASE_URL}/inventory/{inventory_id}/progress-by-counting/"
    
    print(f"\n=== Test de l'avancement global de l'inventaire {inventory_id} ===")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"Inventory ID: {data['data']['inventory_id']}")
            print(f"Inventory Reference: {data['data']['inventory_reference']}")
            print(f"Total Jobs: {data['data']['total_jobs']}")
            
            print("\n📊 Progression globale par counting:")
            for progress in data['data']['progress_by_counting']:
                print(f"  - Counting {progress['counting_order']} ({progress['counting_count_mode']}):")
                print(f"    • Emplacements terminés: {progress['completed_emplacements']}/{progress['total_emplacements']}")
                print(f"    • Progression: {progress['progress_percentage']}%")
                
                print(f"    • Progression par job:")
                for job_progress in progress['jobs_progress']:
                    print(f"      - Job {job_progress['job_reference']}: {job_progress['completed_emplacements']}/{job_progress['total_emplacements']} ({job_progress['progress_percentage']}%)")
        else:
            print("❌ Erreur!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def main():
    """
    Fonction principale pour tester les APIs
    """
    print("🚀 Test des APIs d'avancement des emplacements par job et par counting")
    print("=" * 70)
    
    # Test avec des IDs d'exemple (à adapter selon vos données)
    job_id = 1  # Remplacez par un ID de job existant
    inventory_id = 1  # Remplacez par un ID d'inventaire existant
    
    # Test de l'avancement d'un job spécifique
    test_job_progress_by_counting(job_id)
    
    # Test de l'avancement global d'un inventaire
    test_inventory_progress_by_counting(inventory_id)
    
    print("\n" + "=" * 70)
    print("✅ Tests terminés!")

if __name__ == "__main__":
    main() 