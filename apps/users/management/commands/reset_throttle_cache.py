"""
Commande Django pour réinitialiser le cache de throttling (rate limiting).

Usage:
    python manage.py reset_throttle_cache
    python manage.py reset_throttle_cache --user-id 123
    python manage.py reset_throttle_cache --ip 192.168.1.1
    python manage.py reset_throttle_cache --all
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Réinitialise le cache de throttling (rate limiting) de Django REST Framework'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID de l\'utilisateur spécifique à réinitialiser',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur à réinitialiser',
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Adresse IP spécifique à réinitialiser',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Réinitialiser tous les caches de throttling',
        )
        parser.add_argument(
            '--scope',
            type=str,
            help='Scope spécifique à réinitialiser (login, refresh, verify, user, anon)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        username = options.get('username')
        ip = options.get('ip')
        all_cache = options.get('all', False)
        scope = options.get('scope')

        if all_cache:
            self.reset_all_throttle_cache()
        elif user_id:
            self.reset_user_throttle_cache(user_id, scope)
        elif username:
            try:
                user = User.objects.get(username=username)
                self.reset_user_throttle_cache(user.id, scope)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Utilisateur "{username}" introuvable'))
        elif ip:
            self.reset_ip_throttle_cache(ip, scope)
        elif scope:
            self.reset_scope_throttle_cache(scope)
        else:
            self.stdout.write(self.style.WARNING('Aucune option spécifiée. Utilisez --help pour voir les options disponibles.'))
            self.stdout.write(self.style.WARNING('Pour réinitialiser tout le cache: python manage.py reset_throttle_cache --all'))

    def reset_user_throttle_cache(self, user_id, scope=None):
        """Réinitialise le cache de throttling pour un utilisateur spécifique"""
        scopes = [scope] if scope else ['user', 'login', 'refresh', 'verify']
        count = 0
        
        for s in scopes:
            # Format de clé de cache DRF pour UserRateThrottle
            cache_key = f'throttle_user_{user_id}'
            if cache.get(cache_key):
                cache.delete(cache_key)
                count += 1
            
            # Format de clé de cache pour ScopedRateThrottle
            cache_key_scoped = f'throttle_scope_{s}_{user_id}'
            if cache.get(cache_key_scoped):
                cache.delete(cache_key_scoped)
                count += 1
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Cache de throttling réinitialisé pour l\'utilisateur ID {user_id} ({count} clés)'))
        else:
            self.stdout.write(self.style.WARNING(f'Aucun cache trouvé pour l\'utilisateur ID {user_id}'))

    def reset_ip_throttle_cache(self, ip, scope=None):
        """Réinitialise le cache de throttling pour une IP spécifique"""
        scopes = [scope] if scope else ['anon', 'login', 'refresh', 'verify']
        count = 0
        
        # Identifier l'IP (peut être extraite de différentes façons selon le cache backend)
        # DRF utilise généralement l'IP comme identifiant pour AnonRateThrottle
        
        # Chercher toutes les clés de cache qui contiennent l'IP
        # Note: Cette méthode dépend du backend de cache utilisé
        # Pour un cache simple (local memory), on ne peut pas lister les clés
        # Cette méthode fonctionne mieux avec Redis ou un cache avec support des patterns
        
        try:
            # Tenter de supprimer les clés courantes
            for s in scopes:
                # Format possible pour AnonRateThrottle
                cache_key = f'throttle_anon_{ip}'
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    count += 1
                
                # Format pour ScopedRateThrottle
                cache_key_scoped = f'throttle_scope_{s}_{ip}'
                if cache.get(cache_key_scoped):
                    cache.delete(cache_key_scoped)
                    count += 1
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Impossible de réinitialiser le cache pour IP {ip}: {str(e)}'))
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Cache de throttling réinitialisé pour l\'IP {ip} ({count} clés)'))
        else:
            self.stdout.write(self.style.WARNING(f'Aucun cache trouvé pour l\'IP {ip}. Note: Le backend de cache peut ne pas supporter la recherche par IP.'))

    def reset_scope_throttle_cache(self, scope):
        """Réinitialise le cache de throttling pour un scope spécifique"""
        self.stdout.write(self.style.WARNING(f'La réinitialisation par scope seul n\'est pas supportée avec le cache par défaut.'))
        self.stdout.write(self.style.WARNING(f'Utilisez --all pour tout réinitialiser ou spécifiez un utilisateur ou IP.'))

    def reset_all_throttle_cache(self):
        """Réinitialise tout le cache de throttling"""
        # Note: Cette méthode fonctionne mieux avec Redis ou un cache qui supporte les patterns
        # Pour le cache local, on ne peut pas lister toutes les clés facilement
        
        self.stdout.write(self.style.WARNING('Réinitialisation de tout le cache de throttling...'))
        
        try:
            # Méthode 1: Si on utilise un cache Redis
            if hasattr(cache, 'delete_pattern') or hasattr(cache, 'clear'):
                # Essayer de vider tout le cache
                cache.clear()
                self.stdout.write(self.style.SUCCESS('Tout le cache a été réinitialisé (y compris le cache de throttling)'))
            else:
                # Méthode 2: Pour les caches sans pattern matching
                self.stdout.write(self.style.WARNING('Le backend de cache ne supporte pas la réinitialisation globale.'))
                self.stdout.write(self.style.WARNING('Utilisez une des méthodes suivantes:'))
                self.stdout.write('  1. Réinitialiser le cache via le backend (Redis: FLUSHDB, etc.)')
                self.stdout.write('  2. Spécifier un utilisateur ou IP avec --user-id ou --ip')
                self.stdout.write('  3. Redémarrer le serveur Django (si cache local)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la réinitialisation: {str(e)}'))

