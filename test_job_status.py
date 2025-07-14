#!/usr/bin/env python
"""
Script de test pour vérifier le changement de statut des jobs
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting
from apps.inventory.services.assignment_service import AssignmentService
from django.utils import timezone

def test_job_status_update():
    """Test le changement de statut des jobs"""
    
    # Récupérer un job en attente
    job = Job.objects.filter(status='EN ATTENTE').first()
    
    if not job:
        print("Aucun job en attente trouvé")
        return
    
    print(f"Job trouvé: {job.reference} (statut: {job.status})")
    
    # Récupérer un comptage
    counting = Counting.objects.filter(inventory=job.inventory).first()
    
    if not counting:
        print("Aucun comptage trouvé pour cet inventaire")
        return
    
    print(f"Comptage trouvé: {counting.reference} (ordre: {counting.order})")
    
    # Créer une affectation de test
    assignment_data = {
        'job_ids': [job.id],
        'counting_order': counting.order,
        'session_id': None,  # Pas de session pour le test
        'date_start': timezone.now()
    }
    
    # Tester l'affectation
    service = AssignmentService()
    
    try:
        result = service.assign_jobs(assignment_data)
        print(f"Résultat de l'affectation: {result}")
        
        # Vérifier le nouveau statut du job
        job.refresh_from_db()
        print(f"Nouveau statut du job: {job.status}")
        
    except Exception as e:
        print(f"Erreur lors de l'affectation: {e}")

if __name__ == "__main__":
    test_job_status_update() 