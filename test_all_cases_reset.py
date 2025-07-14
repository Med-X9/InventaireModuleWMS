#!/usr/bin/env python
"""
Script de test complet pour vérifier tous les cas de reset
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment
from apps.inventory.usecases.job_reset_assignments import JobResetAssignmentsUseCase
from django.utils import timezone

def test_all_cases_reset():
    """Test tous les cas de reset"""
    
    print("=== TEST TOUS LES CAS DE RESET ===\n")
    
    # 1. Vérifier les jobs existants
    jobs = Job.objects.all()
    print(f"1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        if job.pret_date:
            print(f"     Date prêt: {job.pret_date}")
        if job.affecte_date:
            print(f"     Date affecté: {job.affecte_date}")
        if job.valide_date:
            print(f"     Date validé: {job.valide_date}")
        if job.en_attente_date:
            print(f"     Date en attente: {job.en_attente_date}")
    
    # 2. Tester avec tous les jobs
    if jobs.exists():
        print(f"\n2. Test du use case avec tous les jobs...")
        
        job_ids = [job.id for job in jobs]
        use_case = JobResetAssignmentsUseCase()
        
        try:
            result = use_case.execute(job_ids)
            print(f"   ✅ Succès: {result['message']}")
            
            # 3. Vérifier les changements pour tous les jobs
            print(f"\n3. Vérification des changements:")
            
            for job in jobs:
                job.refresh_from_db()
                print(f"   - {job.reference}:")
                print(f"     * Statut: {job.status}")
                print(f"     * Date prêt: {job.pret_date}")
                print(f"     * Date affecté: {job.affecte_date}")
                print(f"     * Date validé: {job.valide_date}")
                print(f"     * Date en attente: {job.en_attente_date}")
                
                # Vérifier les assignments
                assignments = Assigment.objects.filter(job=job)
                if assignments.exists():
                    print(f"     * Assignments ({assignments.count()}):")
                    for ass in assignments:
                        print(f"       - {ass.reference}: statut {ass.status}")
                        print(f"         * Date prêt: {ass.pret_date}")
                        print(f"         * Date affecté: {ass.affecte_date}")
                else:
                    print(f"     * Aucun assignment")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print("❌ Aucun job trouvé pour le test")

if __name__ == "__main__":
    test_all_cases_reset() 