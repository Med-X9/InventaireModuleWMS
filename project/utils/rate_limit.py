"""
Utilitaires pour le rate limiting.
Utilise django-ratelimit si disponible, sinon implémentation basique.
"""
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
import time


def rate_limit(key_func, rate='5/m', method='GET'):
    """
    Décorateur pour limiter le taux de requêtes.
    
    Args:
        key_func: Fonction qui retourne la clé unique pour identifier le client
        rate: Taux limite (ex: '5/m' = 5 requêtes par minute, '10/h' = 10 par heure)
        method: Méthode HTTP à limiter
    
    Usage:
        @rate_limit(key_func=lambda request: request.user.id or request.META.get('REMOTE_ADDR'))
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Vérifier la méthode HTTP
            if request.method != method:
                return view_func(request, *args, **kwargs)
            
            # Obtenir la clé unique
            try:
                cache_key = f"rate_limit:{key_func(request)}"
            except Exception:
                # En cas d'erreur, utiliser l'adresse IP
                cache_key = f"rate_limit:{request.META.get('REMOTE_ADDR', 'unknown')}"
            
            # Parser le taux
            limit, period = rate.split('/')
            limit = int(limit)
            
            # Déterminer la durée en secondes
            period_map = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400
            }
            duration = period_map.get(period.lower(), 60)
            
            # Vérifier le nombre de requêtes
            current = cache.get(cache_key, 0)
            
            if current >= limit:
                # Trop de requêtes
                if hasattr(request, 'user') and request.user.is_authenticated:
                    # Pour les utilisateurs authentifiés, retourner une erreur DRF
                    return Response(
                        {'error': 'Trop de requêtes. Veuillez réessayer plus tard.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                else:
                    # Pour les requêtes non authentifiées
                    return JsonResponse(
                        {'error': 'Trop de requêtes. Veuillez réessayer plus tard.'},
                        status=429
                    )
            
            # Incrémenter le compteur
            cache.set(cache_key, current + 1, duration)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_client_ip(request):
    """
    Récupère l'adresse IP réelle du client, même derrière un proxy.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_rate_limit_key(request):
    """
    Génère une clé unique pour le rate limiting.
    Priorité: user.id > IP address
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{get_client_ip(request)}"

