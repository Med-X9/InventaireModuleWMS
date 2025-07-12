#!/usr/bin/env python
"""
Script de test simple pour vérifier la logique de reset
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

def test_simple_reset():
    """Test simple de la logique de reset"""
    
    print("=== TEST SIMPLE RESET ===\n")
    
    # 1. Vérifier les jobs existants
    jobs = Job.objects.all()
    print(f"1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
        if job.pret_date:
            print(f"     Date prêt: {job.pret_date}")
        if job.affecte_date:
            print(f"     Date affecté: {job.affecte_date}")
        if job.en_attente_date:
            print(f"     Date en attente: {job.en_attente_date}")
    
    # 2. Trouver un job à tester
    test_job = Job.objects.first()
    if not test_job:
        print("❌ Aucun job trouvé pour le test")
        return
    
    print(f"\n2. Job à tester: {test_job.reference}")
    print(f"   - Statut actuel: {test_job.status}")
    print(f"   - Date prêt: {test_job.pret_date}")
    print(f"   - Date affecté: {test_job.affecte_date}")
    print(f"   - Date en attente: {test_job.en_attente_date}")
    
    # 3. Tester le use case
    print(f"\n3. Test du use case de reset...")
    
    use_case = JobResetAssignmentsUseCase()
    
    try:
        result = use_case.execute([test_job.id])
        print(f"   ✅ Succès: {result['message']}")
        
        # 4. Vérifier les changements
        print(f"\n4. Vérification des changements:")
        
        # Recharger le job
        test_job.refresh_from_db()
        print(f"   - Nouveau statut: {test_job.status}")
        print(f"   - Date prêt après reset: {test_job.pret_date}")
        print(f"   - Date affecté après reset: {test_job.affecte_date}")
        print(f"   - Date en attente après reset: {test_job.en_attente_date}")
        
        # Vérifier que les assignments ont été reset
        assignments = Assigment.objects.filter(job=test_job)
        print(f"   - Assignments après reset ({assignments.count()}):")
        for ass in assignments:
            print(f"     * {ass.reference}: statut {ass.status}")
            print(f"       - Date prêt: {ass.pret_date}")
            print(f"       - Date affecté: {ass.affecte_date}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_simple_reset() 