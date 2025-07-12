#!/usr/bin/env python
"""
Script de test pour vérifier la validation des comptages dans l'API job ready
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.usecases.job_ready import JobReadyUseCase
from apps.masterdata.models import Warehouse
from django.utils import timezone

def test_job_ready_validation():
    """Test la validation des comptages dans job ready"""
    
    print("=== TEST JOB READY VALIDATION ===")
    
    # 1. Vérifier les jobs existants et leurs statuts
    jobs = Job.objects.all()
    print(f"\n1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        
        # Vérifier les assignments du job
        assignments = Assigment.objects.filter(job=job)
        print(f"     Assignments: {assignments.count()}")
        for ass in assignments:
            print(f"       - {ass.reference}: comptage {ass.counting.reference} (ordre {ass.counting.order})")
        
        # Vérifier les comptages de l'inventaire
        inventory_countings = Counting.objects.filter(inventory=job.inventory)
        print(f"     Comptages de l'inventaire: {inventory_countings.count()}")
        for cnt in inventory_countings:
            print(f"       - {cnt.reference}: ordre {cnt.order}")
    
    # 2. Analyser chaque job pour la validation
    print(f"\n2. Analyse de validation pour chaque job:")
    
    for job in jobs:
        print(f"\n   Job {job.reference} (statut: {job.status}):")
        
        # Vérifier le statut
        if job.status != 'AFFECTE':
            print(f"     ❌ Statut invalide: {job.status}")
            continue
        
        # Vérifier les assignments
        job_assignments = Assigment.objects.filter(job=job)
        if not job_assignments.exists():
            print(f"     ❌ Aucun comptage affecté")
            continue
        
        # Vérifier que tous les comptages de l'inventaire sont affectés
        inventory_countings = Counting.objects.filter(inventory=job.inventory)
        job_counting_ids = set(job_assignments.values_list('counting_id', flat=True))
        inventory_counting_ids = set(inventory_countings.values_list('id', flat=True))
        
        missing_countings = inventory_counting_ids - job_counting_ids
        if missing_countings:
            missing_refs = [f"{cnt.reference}" for cnt in inventory_countings.filter(id__in=missing_countings)]
            print(f"     ❌ Comptages non affectés: {', '.join(missing_refs)}")
        else:
            print(f"     ✅ Tous les comptages sont affectés")
    
    # 3. Tester le use case avec les jobs valides
    affecte_jobs = Job.objects.filter(status='AFFECTE')
    if affecte_jobs.exists():
        print(f"\n3. Test du use case avec jobs AFFECTE:")
        
        use_case = JobReadyUseCase()
        
        # Tester chaque job individuellement pour voir les erreurs
        for job in affecte_jobs:
            print(f"\n   Test du job {job.reference}:")
            try:
                result = use_case.execute([job.id])
                print(f"     ✅ Succès: {result['message']}")
            except Exception as e:
                print(f"     ❌ Erreur: {e}")
        
        # Tester tous les jobs ensemble
        job_ids = [job.id for job in affecte_jobs]
        print(f"\n   Test de tous les jobs ensemble ({len(job_ids)} jobs):")
        try:
            result = use_case.execute(job_ids)
            print(f"     ✅ Succès: {result['message']}")
        except Exception as e:
            print(f"     ❌ Erreur: {e}")

if __name__ == "__main__":
    test_job_ready_validation() 