#!/usr/bin/env python
"""
Test de l'appel API pour l'endpoint mobile/job/close qui cause une erreur 500
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
sys.path.append(os.path.dirname(__file__))

# Ajouter testserver aux ALLOWED_HOSTS
from django.conf import settings
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

django.setup()

# Activer le mode debug pour voir les erreurs détaillées
from django.conf import settings
settings.DEBUG = True

def test_close_job_api():
    """Test de l'appel API pour close job"""
    print("Test de l'appel API pour close job...")

    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import AccessToken
    User = get_user_model()

    # Utiliser l'utilisateur affecté à l'assignment 349 (session_id=3370)
    try:
        user = User.objects.get(id=3370)
        print(f"Utilisateur trouvé: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("Utilisateur 3370 non trouvé, création d'un utilisateur de test")
        user = User.objects.create_user(username='testuser', password='testpass')

    # Créer un token JWT
    access_token = AccessToken.for_user(user)

    client = Client()

    # URL de l'endpoint qui cause l'erreur
    url = '/mobile/api/job/189/close/349/'
    print(f"URL: {url}")

    # Données attendues par le serializer
    data = {
        'personnes': [7434]  # ID d'une personne existante
    }

    try:
        # Faire l'appel POST avec le token JWT
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        response = client.post(url, data=data, content_type='application/json', **headers)
        print(f"Status code: {response.status_code}")

        if response.status_code == 500:
            print("ERREUR 500 reproduite:")
            print(f"Response: {response.content.decode()}")
            # Essayer d'obtenir plus d'informations sur l'erreur
            import traceback
            try:
                # Forcer l'affichage de l'erreur en mode debug
                from django.conf import settings
                if settings.DEBUG:
                    # Simuler une exception pour voir la traceback
                    raise Exception("Erreur 500 capturée")
            except:
                traceback.print_exc()
        elif response.status_code == 200:
            print("SUCCES: L'appel API a fonctionné")
            print(f"Response: {response.content.decode()}")
        else:
            print(f"Autre status code: {response.status_code}")
            print(f"Response: {response.content.decode()}")

    except Exception as e:
        print(f"ERREUR lors de l'appel: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_close_job_api()
