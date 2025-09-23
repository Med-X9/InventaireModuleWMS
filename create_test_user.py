#!/usr/bin/env python3
"""
Script pour créer un utilisateur de test pour l'API.
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp

def create_test_user():
    """Crée un utilisateur de test."""
    username = "testuser_api"
    password = "testpass123"
    email = "test@example.com"
    
    # Supprimer l'utilisateur s'il existe déjà
    try:
        existing_user = UserApp.objects.get(username=username)
        existing_user.delete()
        print(f"✅ Utilisateur existant '{username}' supprimé")
    except UserApp.DoesNotExist:
        pass
    
    # Créer le nouvel utilisateur
    user = UserApp.objects.create_user(
        username=username,
        password=password,
        email=email,
        nom="Test",
        prenom="User",
        type="Web",
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    
    print(f"✅ Utilisateur de test créé:")
    print(f"   - Username: {username}")
    print(f"   - Password: {password}")
    print(f"   - Email: {email}")
    print(f"   - Actif: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Superuser: {user.is_superuser}")
    
    return user

if __name__ == "__main__":
    create_test_user()