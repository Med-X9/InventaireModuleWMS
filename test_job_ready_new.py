#!/usr/bin/env python
"""
Script de test pour la nouvelle API de mise en prêt des jobs
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

def test_job_ready():
    """Test la nouvelle logique de mise en prêt des jobs"""
    
    print("=== TEST JOB READY ===")
    
    # 1. Vérifier les jobs existants et leurs statuts
    jobs = Job.objects.all()
    print(f"\n1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        if job.pret_date:
            print(f"     Date prêt: {job.pret_date}")
    
    # 2. Vérifier les affectations existantes
    assignments = Assigment.objects.all()
    print(f"\n2. Affectations existantes ({assignments.count()}):")
    for ass in assignments:
        print(f"   - {ass.reference}: job {ass.job.reference}, statut {ass.status}, comptage {ass.counting.reference}")
        if ass.pret_date:
            print(f"     Date prêt: {ass.pret_date}")
    
    # 3. Tester le use case avec les jobs AFFECTE
    affecte_jobs = Job.objects.filter(status='AFFECTE')
    if affecte_jobs.exists():
        job_ids = [job.id for job in affecte_jobs]
        print(f"\n3. Test du use case avec {len(job_ids)} jobs AFFECTE:")
        
        use_case = JobReadyUseCase()
        
        try:
            result = use_case.execute(job_ids)
            print(f"   Résultat: {result}")
            
            # 4. Vérifier les changements
            print(f"\n4. Vérification des changements:")
            
            # Recharger les jobs
            jobs_after = Job.objects.filter(id__in=job_ids)
            for job in jobs_after:
                print(f"   - {job.reference}: {job.status}")
                if job.pret_date:
                    print(f"     Date prêt: {job.pret_date}")
            
            # Recharger les affectations
            assignments_after = Assigment.objects.filter(job__in=jobs_after)
            print(f"   Affectations après mise en prêt ({assignments_after.count()}):")
            for ass in assignments_after:
                print(f"     - {ass.reference}: statut {ass.status}, comptage {ass.counting.reference}")
                if ass.pret_date:
                    print(f"       Date prêt: {ass.pret_date}")
            
        except Exception as e:
            print(f"   Erreur: {e}")
    else:
        print("\n3. Aucun job AFFECTE trouvé pour le test")
    
    # 5. Tester avec des jobs non-AFFECTE (doit échouer)
    non_affecte_jobs = Job.objects.exclude(status='AFFECTE')
    if non_affecte_jobs.exists():
        job_ids = [job.id for job in non_affecte_jobs[:2]]  # Prendre 2 jobs max
        print(f"\n5. Test avec jobs non-AFFECTE ({len(job_ids)} jobs):")
        
        use_case = JobReadyUseCase()
        
        try:
            result = use_case.execute(job_ids)
            print(f"   Résultat inattendu: {result}")
        except Exception as e:
            print(f"   Erreur attendue: {e}")

if __name__ == "__main__":
    test_job_ready() 