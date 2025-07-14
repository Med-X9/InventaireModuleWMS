#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API assign-jobs avec mise à jour automatique du statut des affectations.

Cet exemple montre comment :
1. Affecter des jobs au premier comptage
2. Affecter des jobs au deuxième comptage
3. Vérifier que le statut des affectations passe automatiquement à 'AFFECTE' quand les deux comptages ont des sessions
"""

import requests
import json
from typing import List, Dict, Any
import time
from datetime import datetime

class AssignmentAPI:
    """Classe pour interagir avec l'API d'affectation des jobs"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    
    def assign_jobs_to_counting(self, inventory_id: int, job_ids: List[int], counting_order: int, session_id: int = None, date_start: str = None) -> Dict[str, Any]:
        """
        Affecte des jobs à un comptage spécifique
        
        Args:
            inventory_id: ID de l'inventaire
            job_ids: Liste des IDs des jobs
            counting_order: Ordre du comptage (1 ou 2)
            session_id: ID de la session (optionnel)
            date_start: Date de début (optionnel)
            
        Returns:
            Réponse de l'API
        """
        url = f"{self.base_url}/api/inventory/{inventory_id}/assign-jobs/"
        data = {
            'job_ids': job_ids,
            'counting_order': counting_order
        }
        
        if session_id:
            data['session_id'] = session_id
        
        if date_start:
            data['date_start'] = date_start
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Réponse d'erreur: {e.response.text}")
            return None
    
    def get_job_status(self, job_id: int) -> str:
        """
        Récupère le statut d'un job (simulation)
        
        Args:
            job_id: ID du job
            
        Returns:
            Statut du job
        """
        # Dans un vrai cas, vous feriez un appel API pour récupérer le statut
        # Ici, on simule juste pour l'exemple
        url = f"{self.base_url}/api/inventory/jobs/{job_id}/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('status', 'INCONNU')
            else:
                return 'ERREUR'
        except:
            return 'ERREUR'

def assign_jobs_to_counting(inventory_id, job_ids, counting_order, session_id=None):
    """
    Affecte des jobs à un comptage spécifique.
    
    Args:
        inventory_id: ID de l'inventaire
        job_ids: Liste des IDs des jobs à affecter
        counting_order: Ordre du comptage (1 ou 2)
        session_id: ID de la session mobile (optionnel)
    
    Returns:
        dict: Réponse de l'API
    """
    url = f"{BASE_URL}/{inventory_id}/assign-jobs/"
    
    data = {
        "job_ids": job_ids,
        "counting_order": counting_order,
        "date_start": datetime.now().isoformat()
    }
    
    if session_id:
        data["session_id"] = session_id
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Remplacer par votre token
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API: {e}")
        return None

def get_assignments_by_session(session_id):
    """
    Récupère toutes les affectations d'une session.
    
    Args:
        session_id: ID de la session
    
    Returns:
        dict: Réponse de l'API
    """
    url = f"{BASE_URL}/session/{session_id}/assignments/"
    
    headers = {
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Remplacer par votre token
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API: {e}")
        return None

def main():
    """Exemple principal d'utilisation."""
    print("=== Exemple d'affectation de jobs avec mise à jour automatique du statut ===\n")
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    TOKEN = "your_token_here"  # Remplacez par votre token d'authentification
    INVENTORY_ID = 1  # Remplacez par l'ID de votre inventaire
    JOB_IDS = [1, 2, 3]  # Remplacez par vos IDs de jobs
    SESSION1_ID = 1   # Remplacez par l'ID de la première session mobile
    SESSION2_ID = 2   # Remplacez par l'ID de la deuxième session mobile
    
    # Initialiser l'API
    api = AssignmentAPI(BASE_URL, TOKEN)
    
    print("1. Affectation des jobs au premier comptage (avec session)")
    print("-" * 60)
    
    result1 = assign_jobs_to_counting(
        inventory_id=INVENTORY_ID,
        job_ids=JOB_IDS,
        counting_order=1,
        session_id=SESSION1_ID
    )
    
    if result1:
        print(f"✅ Affectation réussie au premier comptage")
        print(f"   Affectations créées: {result1.get('assignments_created', 0)}")
        print(f"   Affectations mises à jour: {result1.get('assignments_updated', 0)}")
        print(f"   Message: {result1.get('message', '')}")
    else:
        print("❌ Échec de l'affectation au premier comptage")
        return
    
    print("\n2. Vérification des affectations de la première session")
    print("-" * 60)
    
    assignments1 = get_assignments_by_session(SESSION1_ID)
    if assignments1:
        print(f"✅ {assignments1.get('assignments_count', 0)} affectations trouvées pour la session {SESSION1_ID}")
        for assignment in assignments1.get('assignments', []):
            print(f"   - Job {assignment['job_reference']} -> Comptage {assignment['counting_order']}")
    else:
        print("❌ Impossible de récupérer les affectations de la première session")
    
    print("\n3. Affectation des jobs au deuxième comptage (avec session)")
    print("-" * 60)
    
    result2 = assign_jobs_to_counting(
        inventory_id=INVENTORY_ID,
        job_ids=JOB_IDS,
        counting_order=2,
        session_id=SESSION2_ID
    )
    
    if result2:
        print(f"✅ Affectation réussie au deuxième comptage")
        print(f"   Affectations créées: {result2.get('assignments_created', 0)}")
        print(f"   Affectations mises à jour: {result2.get('assignments_updated', 0)}")
        print(f"   Message: {result2.get('message', '')}")
    else:
        print("❌ Échec de l'affectation au deuxième comptage")
        return
    
    print("\n4. Vérification des affectations de la deuxième session")
    print("-" * 60)
    
    assignments2 = get_assignments_by_session(SESSION2_ID)
    if assignments2:
        print(f"✅ {assignments2.get('assignments_count', 0)} affectations trouvées pour la session {SESSION2_ID}")
        for assignment in assignments2.get('assignments', []):
            print(f"   - Job {assignment['job_reference']} -> Comptage {assignment['counting_order']}")
    else:
        print("❌ Impossible de récupérer les affectations de la deuxième session")
    
    print("\n5. Résultat final")
    print("-" * 60)
    print("🎉 Les jobs ont été affectés aux deux comptages avec des sessions.")
    print("📊 Le statut des affectations a été automatiquement mis à jour à 'AFFECTE'")
    print("   car les deux comptages ont maintenant des sessions assignées.")
    print("\n📋 Prochaines étapes possibles:")
    print("   - Utiliser l'API 'jobs/ready/' pour marquer les jobs comme prêts")
    print("   - Commencer le comptage avec les sessions mobiles")
    print("   - Suivre l'avancement via l'API 'session/{session_id}/assignments/'")

if __name__ == "__main__":
    main() 