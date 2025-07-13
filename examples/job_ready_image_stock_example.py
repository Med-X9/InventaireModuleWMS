#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API de mise en prêt des jobs avec image de stock
"""

import requests
import json
from typing import List, Dict, Any

class JobReadyImageStockAPI:
    """Classe pour interagir avec l'API de mise en prêt des jobs avec image de stock"""
    
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
    
    def get_job_details(self, job_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un job
        
        Args:
            job_id: ID du job
            
        Returns:
            Détails du job
        """
        url = f"{self.base_url}/api/inventory/jobs/{job_id}/"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des détails du job: {e}")
            return None
    
    def get_inventory_countings(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère les comptages d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Liste des comptages
        """
        url = f"{self.base_url}/api/inventory/{inventory_id}/countings/"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des comptages: {e}")
            return None

def main():
    """Exemple d'utilisation de l'API avec image de stock"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    TOKEN = "your_token_here"  # Remplacez par votre token d'authentification
    
    # Initialiser l'API
    api = JobReadyImageStockAPI(BASE_URL, TOKEN)
    
    print("=== Exemple d'utilisation de l'API de mise en prêt avec image de stock ===\n")
    
    # Exemple 1: Configuration avec image de stock
    print("1. Configuration avec image de stock:")
    print("   - 1er comptage: image de stock (pas de session)")
    print("   - 2ème comptage: en vrac (avec session)")
    print("   → Job peut être mis en PRET")
    
    # IDs des jobs avec configuration image de stock
    image_stock_job_ids = [1, 2, 3]  # Remplacez par vos IDs de jobs
    
    result = api.make_jobs_ready(image_stock_job_ids)
    
    if result and result.get('success'):
        print(f"✅ Succès: {result['data']['ready_jobs_count']} jobs mis au statut PRET")
        for job in result['data']['ready_jobs']:
            print(f"   - Job {job['job_reference']} (ID: {job['job_id']})")
        
        # Afficher les assignments mis à jour
        if 'updated_assignments' in result['data']:
            print(f"   Assignments mis en PRET:")
            for assignment in result['data']['updated_assignments']:
                print(f"     - Comptage {assignment['counting_reference']} (ordre {assignment['counting_order']})")
    else:
        print(f"❌ Erreur: {result.get('message', 'Erreur inconnue')}")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 2: Configuration normale
    print("2. Configuration normale:")
    print("   - 1er comptage: en vrac (avec session)")
    print("   - 2ème comptage: par article (avec session)")
    print("   → Job peut être mis en PRET")
    
    # IDs des jobs avec configuration normale
    normal_job_ids = [4, 5, 6]  # Remplacez par vos IDs de jobs
    
    result = api.make_jobs_ready(normal_job_ids)
    
    if result and result.get('success'):
        print(f"✅ Succès: {result['data']['ready_jobs_count']} jobs mis au statut PRET")
        for job in result['data']['ready_jobs']:
            print(f"   - Job {job['job_reference']} (ID: {job['job_id']})")
    else:
        print(f"❌ Erreur: {result.get('message', 'Erreur inconnue')}")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 3: Configuration mixte
    print("3. Configuration mixte (jobs avec différentes configurations):")
    
    # Mélanger les jobs avec différentes configurations
    mixed_job_ids = [1, 4, 7]  # Jobs avec image de stock + jobs normaux
    
    result = api.make_jobs_ready(mixed_job_ids)
    
    if result and result.get('success'):
        print(f"✅ Succès: {result['data']['ready_jobs_count']} jobs mis au statut PRET")
        print(f"📅 Date de mise en prêt: {result['data']['ready_date']}")
        
        # Afficher les détails
        for job in result['data']['ready_jobs']:
            job_details = api.get_job_details(job['job_id'])
            if job_details:
                print(f"   - Job {job['job_reference']}: {job_details.get('status', 'N/A')}")
    else:
        print(f"❌ Erreur: {result.get('message', 'Erreur inconnue')}")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 4: Vérification des configurations
    print("4. Vérification des configurations d'inventaire:")
    
    # Vérifier les comptages d'un inventaire
    inventory_id = 1  # Remplacez par l'ID de votre inventaire
    countings = api.get_inventory_countings(inventory_id)
    
    if countings:
        print(f"📋 Comptages de l'inventaire {inventory_id}:")
        for counting in countings.get('data', []):
            mode = counting.get('count_mode', 'N/A')
            order = counting.get('order', 'N/A')
            print(f"   - Comptage {order}: {mode}")
            
            # Déterminer si c'est une configuration image de stock
            if order == 1 and mode == 'image de stock':
                print(f"     → Configuration image de stock détectée")
                print(f"     → Seul le 2ème comptage doit être affecté")
            elif order == 1 and mode != 'image de stock':
                print(f"     → Configuration normale détectée")
                print(f"     → Les deux comptages doivent être affectés")
    else:
        print(f"❌ Erreur lors de la récupération des comptages")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 5: Gestion des erreurs
    print("5. Gestion des erreurs:")
    
    # Test avec des jobs invalides
    invalid_job_ids = [999, 888]  # Jobs inexistants
    
    result = api.make_jobs_ready(invalid_job_ids)
    
    if result and not result.get('success'):
        print(f"❌ Erreur attendue: {result.get('message', 'Erreur inconnue')}")
    else:
        print("⚠️  Aucune erreur retournée (inattendu)")
    
    print("\n" + "="*50 + "\n")
    
    # Exemple 6: Traitement par lots
    print("6. Traitement par lots:")
    
    # Simuler une liste de jobs à traiter par lots
    all_job_ids = list(range(1, 101))  # 100 jobs
    batch_size = 20
    
    total_processed = 0
    total_success = 0
    
    for i in range(0, len(all_job_ids), batch_size):
        batch = all_job_ids[i:i + batch_size]
        print(f"   Traitement du lot {i//batch_size + 1} ({len(batch)} jobs)...")
        
        result = api.make_jobs_ready(batch)
        
        if result and result.get('success'):
            batch_success = result['data']['ready_jobs_count']
            total_success += batch_success
            print(f"   ✅ Lot {i//batch_size + 1} traité: {batch_success} jobs")
        else:
            print(f"   ❌ Erreur dans le lot {i//batch_size + 1}: {result.get('message', 'Erreur inconnue')}")
        
        total_processed += len(batch)
    
    print(f"\n📊 Résumé du traitement par lots:")
    print(f"   - Total traité: {total_processed} jobs")
    print(f"   - Succès: {total_success} jobs")
    print(f"   - Échecs: {total_processed - total_success} jobs")

if __name__ == "__main__":
    main() 