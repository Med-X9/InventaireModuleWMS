"""
Vues pour la gestion des tokens CSRF
"""
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    """
    Vue pour récupérer le token CSRF
    Nécessaire pour les applications SPA qui utilisent des cookies de session
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Retourne le token CSRF dans un cookie et en JSON
        """
        try:
            # Le décorateur ensure_csrf_cookie s'occupe de mettre le token dans les cookies
            # On peut aussi le retourner en JSON pour les applications SPA
            from django.middleware.csrf import get_token
            csrf_token = get_token(request)
            
            logger.debug(f"Token CSRF généré: {csrf_token[:10]}...")
            
            return JsonResponse({
                'success': True,
                'csrfToken': csrf_token,
                'message': 'Token CSRF généré avec succès'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du token CSRF: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors de la génération du token CSRF'
            }, status=500)

@require_http_methods(["GET"])
def csrf_token_simple(request):
    """
    Endpoint simple pour récupérer le token CSRF
    Compatible avec les applications qui ne peuvent pas utiliser les cookies
    """
    try:
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
        
        return JsonResponse({
            'csrfToken': csrf_token
        })
        
    except Exception as e:
        logger.error(f"Erreur CSRF simple: {str(e)}")
        return JsonResponse({
            'error': 'Erreur CSRF'
        }, status=500)
