#!/usr/bin/env python
"""
Script pour analyser spécifiquement le job JOB0D00368F
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.usecases.job_ready import JobReadyUseCase
from django.utils import timezone

def debug_job_specific():
    """Debug spécifiquement le job JOB0D00368F"""
    
    print("=== DEBUG JOB SPÉCIFIQUE ===")
    
    # Récupérer le job spécifique
    job = Job.objects.filter(reference='JOB0D00368F').first()
    if not job:
        print("Job JOB0D00368F non trouvé")
        return
    
    print(f"\n1. Job JOB0D00368F:")
    print(f"   - ID: {job.id}")
    print(f"   - Statut: {job.status}")
    print(f"   - Inventaire: {job.inventory.reference}")
    
    # Récupérer tous les comptages de l'inventaire
    inventory_countings = Counting.objects.filter(inventory=job.inventory)
    print(f"\n2. Comptages de l'inventaire {job.inventory.reference} ({inventory_countings.count()}):")
    for cnt in inventory_countings:
        print(f"   - {cnt.reference}: ordre {cnt.order}, mode {cnt.count_mode}")
    
    # Récupérer les assignments du job
    job_assignments = Assigment.objects.filter(job=job)
    print(f"\n3. Assignments du job ({job_assignments.count()}):")
    for ass in job_assignments:
        session_info = f"session {ass.session.id}" if ass.session else "pas de session"
        print(f"   - {ass.reference}: comptage {ass.counting.reference} (ordre {ass.counting.order}), {session_info}, statut {ass.status}")
    
    # Analyser la validation
    print(f"\n4. Analyse de validation:")
    
    # Vérifier le statut
    if job.status != 'AFFECTE':
        print(f"   ❌ Statut invalide: {job.status}")
    else:
        print(f"   ✅ Statut valide: {job.status}")
    
    # Vérifier les assignments
    if not job_assignments.exists():
        print(f"   ❌ Aucun comptage affecté")
    else:
        print(f"   ✅ {job_assignments.count()} comptages affectés")
    
    # Vérifier que tous les comptages de l'inventaire sont affectés
    job_counting_ids = set(job_assignments.values_list('counting_id', flat=True))
    inventory_counting_ids = set(inventory_countings.values_list('id', flat=True))
    
    print(f"\n   Comptages de l'inventaire: {list(inventory_counting_ids)}")
    print(f"   Comptages affectés au job: {list(job_counting_ids)}")
    
    missing_countings = inventory_counting_ids - job_counting_ids
    if missing_countings:
        missing_counting_refs = [f"{cnt.reference}" for cnt in inventory_countings.filter(id__in=missing_countings)]
        print(f"   ❌ Comptages non affectés: {', '.join(missing_counting_refs)}")
    else:
        print(f"   ✅ Tous les comptages sont affectés")
    
    # Tester le use case
    print(f"\n5. Test du use case:")
    use_case = JobReadyUseCase()
    try:
        result = use_case.execute([job.id])
        print(f"   ✅ Succès: {result['message']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    debug_job_specific() 