#!/usr/bin/env python
"""
Script de test pour vérifier la nouvelle logique de reset des assignments
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, JobDetailRessource
from apps.inventory.usecases.job_reset_assignments import JobResetAssignmentsUseCase
from django.utils import timezone

def test_reset_assignments():
    """Test la nouvelle logique de reset des assignments"""
    
    print("=== TEST RESET ASSIGNMENTS ===")
    
    # 1. Vérifier les jobs existants et leurs statuts
    jobs = Job.objects.all()
    print(f"\n1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        if job.valide_date:
            print(f"     Date validation: {job.valide_date}")
        if job.affecte_date:
            print(f"     Date affectation: {job.affecte_date}")
    
    # 2. Vérifier les affectations existantes
    assignments = Assigment.objects.all()
    print(f"\n2. Affectations existantes ({assignments.count()}):")
    for ass in assignments:
        session_info = f"session {ass.session.id}" if ass.session else "pas de session"
        print(f"   - {ass.reference}: job {ass.job.reference}, statut {ass.status}, {session_info}")
    
    # 3. Vérifier les ressources affectées
    ressources = JobDetailRessource.objects.all()
    print(f"\n3. Ressources affectées ({ressources.count()}):")
    for res in ressources:
        print(f"   - {res.reference}: job {res.job.reference}, ressource {res.ressource.reference}")
    
    # 4. Tester le use case avec les jobs existants
    if jobs.exists():
        job_ids = [job.id for job in jobs]
        print(f"\n4. Test du use case avec {len(job_ids)} jobs:")
        
        use_case = JobResetAssignmentsUseCase()
        
        try:
            result = use_case.execute(job_ids)
            print(f"   Résultat: {result}")
            
            # 5. Vérifier les changements
            print(f"\n5. Vérification des changements:")
            
            # Recharger les jobs
            jobs_after = Job.objects.filter(id__in=job_ids)
            for job in jobs_after:
                print(f"   - {job.reference}: {job.status}")
                if job.valide_date:
                    print(f"     Date validation: {job.valide_date}")
                if job.affecte_date:
                    print(f"     Date affectation: {job.affecte_date}")
            
            # Recharger les affectations
            assignments_after = Assigment.objects.filter(job__in=jobs_after)
            print(f"   Affectations après reset ({assignments_after.count()}):")
            for ass in assignments_after:
                session_info = f"session {ass.session.id}" if ass.session else "pas de session"
                print(f"     - {ass.reference}: statut {ass.status}, {session_info}")
            
            # Vérifier les ressources
            ressources_after = JobDetailRessource.objects.filter(job__in=jobs_after)
            print(f"   Ressources après reset ({ressources_after.count()}):")
            for res in ressources_after:
                print(f"     - {res.reference}: job {res.job.reference}")
            
        except Exception as e:
            print(f"   Erreur: {e}")

if __name__ == "__main__":
    test_reset_assignments() 