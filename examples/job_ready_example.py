#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API de mise en prêt des jobs affectés
"""

import requests
import json
from typing import List, Dict, Any

class JobReadyAPI:
    """Classe pour interagir avec l'API de mise en prêt des jobs"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    
    def make_jobs_ready(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Met plusieurs jobs au statut PRET
        
        Args:
            job_ids: Liste des IDs des jobs à mettre au statut PRET
            
        Returns:
            Réponse de l'API
        """
        url = f"{self.base_url}/api/inventory/jobs/ready/"
        data = {
            'job_ids': job_ids
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Réponse d'erreur: {e.response.text}")
            return None
    
    def get_jobs_by_warehouse_and_status(self, warehouse_id: int, status: str) -> List[int]:
        """
        Récupère les IDs des jobs d'un warehouse avec un statut spécifique
        
        Args:
            warehouse_id: ID du warehouse
            status: Statut des jobs à récupérer
            
        Returns:
            Liste des IDs des jobs
        """
        url = f"{self.base_url}/api/inventory/warehouse/{warehouse_id}/jobs/"
        params = {'status': status}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extraire les IDs des jobs
            job_ids = [job['id'] for job in data.get('results', [])]
            return job_ids
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des jobs: {e}")
            return []

def main():
    """Exemple d'utilisation de l'API"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    TOKEN = "your_token_here"  # Remplacez par votre token d'authentification
    WAREHOUSE_ID = 1  # Remplacez par l'ID de votre warehouse
    
    # Initialiser l'API
    api = JobReadyAPI(BASE_URL, TOKEN)
    
    print("=== Exemple d'utilisation de l'API de mise en prêt des jobs ===\n")
    
    # Exemple 1: Mise en prêt de jobs spécifiques
    print("1. Mise en prêt de jobs spécifiques:")
    specific_job_ids = [1, 2, 3, 4, 5]  # Remplacez par vos IDs de jobs
    result = api.make_jobs_ready(specific_job_ids)
    
    if result and result.get('success'):
        print(f"✅ Succès: {result['data']['ready_jobs_count']} jobs mis au statut PRET")
        for job in result['data']['ready_jobs']:
            print(f"   - Job {job['job_reference']} (ID: {job['job_id']})")
    else:
        print(f"❌ Erreur: {result.get('message', 'Erreur inconnue')}")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 2: Mise en prêt de tous les jobs affectés d'un warehouse
    print("2. Mise en prêt de tous les jobs affectés d'un warehouse:")
    
    # Récupérer tous les jobs affectés du warehouse
    affected_job_ids = api.get_jobs_by_warehouse_and_status(WAREHOUSE_ID, 'AFFECTE')
    
    if affected_job_ids:
        print(f"📋 {len(affected_job_ids)} jobs affectés trouvés dans le warehouse {WAREHOUSE_ID}")
        
        # Les mettre au statut PRET
        result = api.make_jobs_ready(affected_job_ids)
        
        if result and result.get('success'):
            print(f"✅ Succès: {result['data']['ready_jobs_count']} jobs mis au statut PRET")
            print(f"📅 Date de mise en prêt: {result['data']['ready_date']}")
        else:
            print(f"❌ Erreur: {result.get('message', 'Erreur inconnue')}")
    else:
        print(f"ℹ️  Aucun job affecté trouvé dans le warehouse {WAREHOUSE_ID}")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 3: Mise en prêt par lots
    print("3. Mise en prêt par lots (pour de gros volumes):")
    
    # Simuler une liste de jobs à traiter par lots
    all_job_ids = list(range(1, 101))  # 100 jobs
    batch_size = 20
    
    for i in range(0, len(all_job_ids), batch_size):
        batch = all_job_ids[i:i + batch_size]
        print(f"   Traitement du lot {i//batch_size + 1} ({len(batch)} jobs)...")
        
        result = api.make_jobs_ready(batch)
        
        if result and result.get('success'):
            print(f"   ✅ Lot {i//batch_size + 1} traité: {result['data']['ready_jobs_count']} jobs")
        else:
            print(f"   ❌ Erreur dans le lot {i//batch_size + 1}: {result.get('message', 'Erreur inconnue')}")

if __name__ == "__main__":
    main() 