#!/usr/bin/env python3
"""
Créer un utilisateur de test simple
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.users.models import UserApp

def create_test_user():
    """Créer un utilisateur de test"""
    
    print("👤 Création d'un utilisateur de test")
    print("=" * 40)
    
    username = "testuser"
    password = "testpass123"
    
    try:
        # Vérifier si l'utilisateur existe déjà
        if UserApp.objects.filter(username=username).exists():
            print(f"✅ Utilisateur '{username}' existe déjà")
            user = UserApp.objects.get(username=username)
        else:
            # Créer l'utilisateur
            user = UserApp.objects.create_user(
                username=username,
                type='Web',  # Champ requis
                password=password,
                nom="Test",  # Champ requis
                prenom="User",  # Champ requis
                is_staff=True,
                is_superuser=True
            )
            print(f"✅ Utilisateur '{username}' créé avec succès")
        
        print(f"   Username: {user.username}")
        print(f"   Password: {password}")
        print(f"   ID: {user.id}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        
        return user
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return None

if __name__ == "__main__":
    create_test_user()
