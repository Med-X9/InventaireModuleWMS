"""
Gestionnaire d'exceptions personnalisé pour DRF.
Ne pas exposer d'informations sensibles dans les erreurs.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé qui :
    - Ne expose pas les stack traces en production
    - Log les erreurs détaillées côté serveur
    - Retourne des messages d'erreur génériques aux clients
    """
    # Appeler le gestionnaire d'exceptions par défaut de DRF
    response = exception_handler(exc, context)
    
    # Si une réponse a été générée, personnaliser le message
    if response is not None:
        # Logger l'erreur complète côté serveur
        logger.error(
            f"Exception dans {context.get('view', 'Unknown')}: {str(exc)}",
            exc_info=True,
            extra={
                'request_path': context.get('request').path if context.get('request') else None,
                'request_method': context.get('request').method if context.get('request') else None,
                'user': context.get('request').user.username if context.get('request') and hasattr(context.get('request').user, 'username') else 'Anonymous',
            }
        )
        
        # En production, ne pas exposer les détails de l'erreur
        from django.conf import settings
        
        if not settings.DEBUG:
            # Messages d'erreur génériques selon le type
            if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                response.data = {
                    'error': 'Une erreur interne s\'est produite. Veuillez contacter l\'administrateur.'
                }
            elif response.status_code == status.HTTP_400_BAD_REQUEST:
                # Garder les erreurs de validation mais nettoyer les détails sensibles
                if isinstance(response.data, dict):
                    # Filtrer les champs sensibles
                    sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key']
                    cleaned_data = {}
                    for key, value in response.data.items():
                        if any(sensitive in key.lower() for sensitive in sensitive_fields):
                            cleaned_data[key] = '***'
                        else:
                            cleaned_data[key] = value
                    response.data = cleaned_data
    
    return response

