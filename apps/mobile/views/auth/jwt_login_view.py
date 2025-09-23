from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.users.models import UserApp


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé qui étend TokenObtainPairSerializer
    pour inclure les informations utilisateur personnalisées
    """
    
    def validate(self, attrs):
        """
        Valide les données et retourne les tokens + infos utilisateur
        """
        # Appeler la validation parent pour obtenir les tokens
        data = super().validate(attrs)
        
        # Récupérer l'utilisateur authentifié
        user = self.user
        
        # Formater la réponse selon le format demandé
        response_data = {
            'success': True,
            'access': str(data['access']),
            'refresh': str(data['refresh']),
            'user': {
                'user_id': user.id,
                'nom': user.nom if hasattr(user, 'nom') else '',
                'prenom': user.prenom if hasattr(user, 'prenom') else ''
            }
        }
        
        return response_data


class JWTLoginView(TokenObtainPairView):
    """
    API de connexion qui hérite de SIMPLE_JWT et retourne la réponse formatée
    """
    
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Gère la requête POST de connexion
        """
        try:
            # Utiliser le serializer parent pour la validation et la génération des tokens
            serializer = self.get_serializer(data=request.data)
            
            if serializer.is_valid():
                # Le serializer retourne déjà la réponse formatée
                return Response(serializer.validated_data, status=status.HTTP_200_OK)
            else:
                # En cas d'erreur de validation
                return Response({
                    'success': False,
                    'error': 'Identifiants invalides',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Gestion des erreurs inattendues
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
