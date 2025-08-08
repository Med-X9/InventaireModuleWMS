from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    """Service pour l'authentification"""
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur"""
        if not username or not password:
            return None, "Username et password requis"
        
        user = authenticate(username=username, password=password)
        if user is None:
            return None, "Identifiants invalides"
        
        return user, None
    
    def generate_tokens(self, user):
        """Génère les tokens JWT pour un utilisateur"""
        refresh = RefreshToken.for_user(user)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    
    def get_user_info(self, user):
        """Récupère les informations de l'utilisateur"""
        return {
            'user_id': user.id,
            'nom': user.last_name or '',
            'prenom': user.first_name or ''
        }
    
    def login(self, username, password):
        """Effectue la connexion d'un utilisateur"""
        user, error = self.authenticate_user(username, password)
        if error:
            return None, error
        
        tokens = self.generate_tokens(user)
        user_info = self.get_user_info(user)
        
        return {
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user_info
        }, None
    
    def refresh_token(self, refresh_token):
        """Rafraîchit un token d'accès"""
        if not refresh_token:
            return None, "Token invalide"
        
        try:
            refresh = RefreshToken(refresh_token)
            return {
                'success': True,
                'token': str(refresh.access_token)
            }, None
        except Exception:
            return None, "Token invalide"
    
    def logout(self):
        """Effectue la déconnexion"""
        return {
            'success': True
        } 