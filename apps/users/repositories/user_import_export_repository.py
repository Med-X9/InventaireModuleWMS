"""
Repository pour l'import/export des utilisateurs
Contient uniquement les opérations d'accès aux données
"""
from typing import List, Optional
from django.contrib.auth import get_user_model
from ..models import UserApp


User = get_user_model()


class UserImportExportRepository:
    """
    Repository pour l'import/export des utilisateurs
    Contient uniquement les opérations d'accès aux données
    """
    
    def get_all_users(self) -> List[UserApp]:
        """
        Récupère tous les utilisateurs actifs avec leurs relations préchargées
        
        Returns:
            Liste des utilisateurs avec leurs relations préchargées
        """
        return list(
            UserApp.objects.filter(
                is_active=True
            ).select_related(
                'compte'
            ).prefetch_related(
                'groups',
                'user_permissions'
            ).order_by('nom', 'prenom')
        )
    
    def get_users_by_account(self, account_id: int) -> List[UserApp]:
        """
        Récupère tous les utilisateurs d'un compte spécifique
        
        Args:
            account_id: ID du compte
            
        Returns:
            Liste des utilisateurs du compte
        """
        return list(
            UserApp.objects.filter(
                compte_id=account_id,
                is_active=True
            ).select_related(
                'compte'
            ).prefetch_related(
                'groups',
                'user_permissions'
            ).order_by('nom', 'prenom')
        )
    
    def get_user_by_username(self, username: str) -> Optional[UserApp]:
        """
        Récupère un utilisateur par son nom d'utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Utilisateur ou None
        """
        try:
            return UserApp.objects.get(username=username)
        except UserApp.DoesNotExist:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserApp]:
        """
        Récupère un utilisateur par son ID
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Utilisateur ou None
        """
        try:
            return UserApp.objects.select_related('compte').get(id=user_id)
        except UserApp.DoesNotExist:
            return None
    
    def create_user(self, user_data: dict) -> UserApp:
        """
        Crée un nouvel utilisateur
        
        Args:
            user_data: Dictionnaire contenant les données de l'utilisateur
            
        Returns:
            Utilisateur créé
        """
        password = user_data.pop('password', None)
        user = UserApp(**user_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update_user(self, user: UserApp, user_data: dict) -> UserApp:
        """
        Met à jour un utilisateur existant
        
        Args:
            user: Instance de l'utilisateur à mettre à jour
            user_data: Dictionnaire contenant les données à mettre à jour
            
        Returns:
            Utilisateur mis à jour
        """
        password = user_data.pop('password', None)
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        if password:
            user.set_password(password)
        
        user.save()
        return user
    
    def user_exists(self, username: str) -> bool:
        """
        Vérifie si un utilisateur existe déjà par son nom d'utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            True si l'utilisateur existe, False sinon
        """
        return UserApp.objects.filter(username=username).exists()

