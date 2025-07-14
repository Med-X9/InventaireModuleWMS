#!/usr/bin/env python3
"""
Script de test rapide pour l'API de mise en prêt des jobs
"""

import os
import sys
import django
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Inventory, Job
from apps.masterdata.models import Warehouse, Account
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_job_ready_api():
    """Test rapide de l'API de mise en prêt des jobs"""
    
    print("🧪 Test de l'API de mise en prêt des jobs...")
    
    # Créer un client de test
    client = APIClient()
    
    # Créer un utilisateur pour l'authentification
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client.force_authenticate(user=user)
    
    # Créer les données de test
    account = Account.objects.create(
        name='Test Account',
        code='TEST001'
    )
    
    warehouse = Warehouse.objects.create(
        name='Test Warehouse',
        code='WH001',
        account=account
    )
    
    inventory = Inventory.objects.create(
        label='Test Inventory',
        date=timezone.now(),
        status='EN PREPARATION'
    )
    
    # Créer des jobs avec différents statuts
    job_affecte1 = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    job_affecte2 = Job.objects.create(
        status='AFFECTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    job_en_attente = Job.objects.create(
        status='EN ATTENTE',
        warehouse=warehouse,
        inventory=inventory
    )
    
    print(f"✅ Données de test créées:")
    print(f"   - Job affecté 1: {job_affecte1.reference} (ID: {job_affecte1.id})")
    print(f"   - Job affecté 2: {job_affecte2.reference} (ID: {job_affecte2.id})")
    print(f"   - Job en attente: {job_en_attente.reference} (ID: {job_en_attente.id})")
    
    # Test 1: Mise en prêt de jobs affectés
    print("\n📋 Test 1: Mise en prêt de jobs affectés...")
    url = reverse('jobs-ready')
    data = {
        'job_ids': [job_affecte1.id, job_affecte2.id]
    }
    
    response = client.post(url, data, format='json')
    
    if response.status_code == status.HTTP_200_OK:
        print("✅ Succès!")
        result = response.json()
        print(f"   - {result['data']['ready_jobs_count']} jobs mis au statut PRET")
        for job in result['data']['ready_jobs']:
            print(f"   - Job {job['job_reference']} (ID: {job['job_id']})")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Réponse: {response.json()}")
    
    # Test 2: Tentative de mise en prêt de jobs non affectés
    print("\n📋 Test 2: Tentative de mise en prêt de jobs non affectés...")
    data = {
        'job_ids': [job_en_attente.id]
    }
    
    response = client.post(url, data, format='json')
    
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        print("✅ Erreur attendue (jobs non affectés)!")
        result = response.json()
        print(f"   - Message: {result['message']}")
    else:
        print(f"❌ Erreur inattendue: {response.status_code}")
        print(f"   Réponse: {response.json()}")
    
    # Test 3: Tentative avec des jobs inexistants
    print("\n📋 Test 3: Tentative avec des jobs inexistants...")
    data = {
        'job_ids': [99999, 88888]
    }
    
    response = client.post(url, data, format='json')
    
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        print("✅ Erreur attendue (jobs inexistants)!")
        result = response.json()
        print(f"   - Message: {result['message']}")
    else:
        print(f"❌ Erreur inattendue: {response.status_code}")
        print(f"   Réponse: {response.json()}")
    
    # Vérifier les statuts finaux
    print("\n📊 Vérification des statuts finaux:")
    job_affecte1.refresh_from_db()
    job_affecte2.refresh_from_db()
    job_en_attente.refresh_from_db()
    
    print(f"   - Job 1: {job_affecte1.status} (attendu: PRET)")
    print(f"   - Job 2: {job_affecte2.status} (attendu: PRET)")
    print(f"   - Job 3: {job_en_attente.status} (attendu: EN ATTENTE)")
    
    # Nettoyage
    print("\n🧹 Nettoyage des données de test...")
    job_affecte1.delete()
    job_affecte2.delete()
    job_en_attente.delete()
    inventory.delete()
    warehouse.delete()
    account.delete()
    user.delete()
    
    print("✅ Test terminé!")

if __name__ == "__main__":
    test_job_ready_api() 