from django.contrib.auth import get_user_model
from apps.mobile.exceptions.auth_exceptions import UserNotFoundException

User = get_user_model()


class AuthRepository:
    """Repository pour l'authentification"""
    
    def get_user_by_username(self, username):
        """Récupère un utilisateur par son nom d'utilisateur"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFoundException(f"Utilisateur avec le nom d'utilisateur '{username}' non trouvé")
    
    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par son ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundException(f"Utilisateur avec l'ID {user_id} non trouvé")
    
    def is_user_active(self, user):
        """Vérifie si un utilisateur est actif"""
        return user.is_active
    
    def update_user_last_login(self, user):
        """Met à jour la dernière connexion de l'utilisateur"""
        user.save(update_fields=['last_login']) 