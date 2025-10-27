"""
Test de l'API de synchronisation avec le filtre sur les jobs TRANSFERT et ENTAME
"""

import os
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp
from apps.inventory.models import Job


def test_sync_api_with_job_filter():
    """Test de l'API avec le nouveau filtre sur les jobs"""
    
    print("\n" + "="*80)
    print("🧪 TEST DE L'API DE SYNCHRONISATION - FILTRE JOBS TRANSFERT/ENTAME")
    print("="*80)
    
    # 1. Récupérer un utilisateur mobile
    print("\n📱 Étape 1: Récupération d'un utilisateur mobile...")
    user = UserApp.objects.filter(type='Mobile', compte__isnull=False).first()
    
    if not user:
        print("❌ Aucun utilisateur mobile trouvé avec un compte associé")
        return
    
    print(f"✓ Utilisateur trouvé: {user.username} (ID: {user.id})")
    print(f"  Compte: {user.compte.account_name}")
    
    # 2. Vérifier les jobs disponibles dans la base
    print("\n📊 Étape 2: Vérification des jobs dans la base de données...")
    all_jobs = Job.objects.all()
    print(f"\n📋 Total de jobs dans la base: {all_jobs.count()}")
    
    jobs_by_status = {}
    for job in all_jobs:
        status = job.status
        if status not in jobs_by_status:
            jobs_by_status[status] = []
        jobs_by_status[status].append(job.reference)
    
    print("\n📊 Répartition par statut:")
    for status, jobs in jobs_by_status.items():
        print(f"   • {status}: {len(jobs)} job(s)")
        for job_ref in jobs[:3]:  # Afficher max 3 refs
            print(f"     - {job_ref}")
    
    # Compter les jobs TRANSFERT et ENTAME
    expected_jobs = Job.objects.filter(status__in=['TRANSFERT', 'ENTAME']).count()
    print(f"\n✓ Jobs attendus (TRANSFERT + ENTAME): {expected_jobs}")
    
    # 3. Appeler l'API de synchronisation
    print("\n🌐 Étape 3: Appel de l'API de synchronisation...")
    
    # Créer un token de test (à adapter selon votre configuration)
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=user)
    
    api_url = f"http://localhost:8000/api/mobile/sync/data/user/{user.id}/"
    headers = {
        'Authorization': f'Token {token.key}',
        'Content-Type': 'application/json'
    }
    
    print(f"URL: {api_url}")
    print(f"Token: {token.key[:20]}...")
    
    try:
        response = requests.get(api_url, headers=headers)
        print(f"\n📡 Réponse HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Synchronisation réussie!")
            print(f"   Sync ID: {data.get('sync_id', 'N/A')}")
            
            # Analyser les jobs retournés
            jobs_data = data.get('data', {}).get('jobs', [])
            print(f"\n📦 Jobs retournés par l'API: {len(jobs_data)}")
            
            if jobs_data:
                print("\n📋 Détails des jobs:")
                for job in jobs_data:
                    status = job.get('status', 'N/A')
                    reference = job.get('reference', 'N/A')
                    print(f"   • {reference} - Statut: {status}")
                
                # Vérifier que tous les jobs sont TRANSFERT ou ENTAME
                invalid_jobs = [j for j in jobs_data if j.get('status') not in ['TRANSFERT', 'ENTAME']]
                
                if invalid_jobs:
                    print("\n⚠️  AVERTISSEMENT: Des jobs avec d'autres statuts ont été retournés:")
                    for job in invalid_jobs:
                        print(f"   ❌ {job.get('reference')} - {job.get('status')}")
                else:
                    print("\n✅ VALIDATION: Tous les jobs retournés ont le statut TRANSFERT ou ENTAME")
            else:
                print("\n⚠️  Aucun job retourné (normal s'il n'y a pas de jobs TRANSFERT/ENTAME)")
            
            # Afficher les autres données
            inventories = data.get('data', {}).get('inventories', [])
            assignments = data.get('data', {}).get('assignments', [])
            countings = data.get('data', {}).get('countings', [])
            
            print(f"\n📊 Résumé complet:")
            print(f"   • Inventaires: {len(inventories)}")
            print(f"   • Jobs: {len(jobs_data)}")
            print(f"   • Affectations: {len(assignments)}")
            print(f"   • Comptages: {len(countings)}")
            
            # Afficher la réponse complète (formatée)
            print("\n📄 Réponse JSON complète:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")
            
        else:
            print(f"\n❌ Erreur HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('error', 'N/A')}")
                print(f"   Type: {error_data.get('error_type', 'N/A')}")
            except:
                print(f"   Contenu: {response.text[:200]}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter à l'API")
        print("   Assurez-vous que le serveur Django est démarré (python manage.py runserver)")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ TEST TERMINÉ")
    print("="*80)


if __name__ == '__main__':
    test_sync_api_with_job_filter()

