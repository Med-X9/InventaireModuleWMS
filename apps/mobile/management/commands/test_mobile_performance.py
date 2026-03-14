"""
Commande Django pour tester la performance des APIs mobiles.

Ce script mesure les temps de réponse, le débit et les statistiques
de performance pour les principales APIs de l'application mobile.
"""
import time
import statistics
from typing import Dict
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Teste la performance des APIs mobiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur pour l\'authentification',
            required=True,
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe pour l\'authentification',
            required=True,
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='URL de base de l\'API (défaut: http://localhost:8000)',
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Nombre d\'itérations pour chaque test (défaut: 10)',
        )
        parser.add_argument(
            '--assignment-id',
            type=int,
            help='ID d\'assignment pour tester l\'endpoint de statut (optionnel)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        base_url = options['base_url']
        iterations = options['iterations']
        assignment_id = options.get('assignment_id')

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('TEST DE PERFORMANCE - APIs MOBILES'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Authentification
        token, user = self.authenticate(base_url, username, password)
        if not token or not user:
            self.stdout.write(self.style.ERROR('Échec de l\'authentification'))
            return

        self.stdout.write(self.style.SUCCESS(f'[OK] Authentification reussie pour {username}'))
        self.stdout.write('')

        # Tests de performance
        results = {}

        # Test 1: Synchronisation des données
        self.stdout.write(self.style.WARNING('Test 1: Synchronisation des données (sync/data/)'))
        results['sync_data'] = self.test_endpoint(
            token, user, 'GET', 'sync/data', iterations
        )

        # Test 2: Produits
        self.stdout.write(self.style.WARNING('Test 2: Produits (products/)'))
        results['products'] = self.test_endpoint(
            token, user, 'GET', 'products', iterations
        )

        # Test 3: Emplacements
        self.stdout.write(self.style.WARNING('Test 3: Emplacements (locations/)'))
        results['locations'] = self.test_endpoint(
            token, user, 'GET', 'locations', iterations
        )

        # Test 4: Stocks
        self.stdout.write(self.style.WARNING('Test 4: Stocks (stocks/)'))
        results['stocks'] = self.test_endpoint(
            token, user, 'GET', 'stocks', iterations
        )

        # Test 5: Personnes
        self.stdout.write(self.style.WARNING('Test 5: Personnes (persons/)'))
        results['persons'] = self.test_endpoint(
            token, user, 'GET', 'persons', iterations
        )

        # Test 6: Statut d'assignment (si assignment_id fourni)
        if assignment_id:
            self.stdout.write(
                self.style.WARNING(f'Test 6: Statut d\'assignment (assignment/{assignment_id}/status/)')
            )
            results['assignment_status'] = self.test_endpoint(
                token, user, 'POST', f'assignment/{assignment_id}/status', iterations
            )

        # Affichage du rapport
        self.print_report(results, iterations)

    def authenticate(self, base_url: str, username: str, password: str) -> tuple:
        """
        Authentifie l'utilisateur et retourne le token JWT et l'utilisateur.
        
        Args:
            base_url: URL de base de l'API (non utilisé, conservé pour compatibilité)
            username: Nom d'utilisateur
            password: Mot de passe
            
        Returns:
            Tuple (token, user) ou (None, None) si l'authentification échoue
        """
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                self.stdout.write(self.style.ERROR('Mot de passe incorrect'))
                return None, None
            
            if not user.is_active:
                self.stdout.write(self.style.ERROR('Utilisateur inactif'))
                return None, None
            
            # Générer le token JWT
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            
            return token, user
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Utilisateur "{username}" non trouvé'))
            return None, None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception lors de l\'authentification: {str(e)}'))
            return None, None

    def test_endpoint(
        self,
        token: str,
        user,
        method: str,
        endpoint_name: str,
        iterations: int
    ) -> Dict:
        """
        Teste un endpoint et mesure ses performances.
        
        Args:
            token: Token JWT
            user: Utilisateur authentifié
            method: Méthode HTTP (GET, POST, etc.)
            endpoint_name: Nom de l'endpoint (sans préfixe /mobile/api/)
            iterations: Nombre d'itérations
            
        Returns:
            Dictionnaire avec les statistiques de performance
        """
        from apps.mobile.views import (
            SyncDataView, UserProductsView, UserLocationsView,
            UserStocksView, PersonListView, AssignmentStatusView
        )
        
        # Mapping des endpoints vers les vues
        view_mapping = {
            'sync/data': SyncDataView,
            'products': UserProductsView,
            'locations': UserLocationsView,
            'stocks': UserStocksView,
            'persons': PersonListView,
        }
        
        # Gestion spéciale pour assignment
        if endpoint_name.startswith('assignment/'):
            assignment_id = int(endpoint_name.split('/')[1])
            view_class = AssignmentStatusView
        else:
            view_class = view_mapping.get(endpoint_name)
            assignment_id = None
        
        if not view_class:
            self.stdout.write(self.style.ERROR(f'  ✗ Endpoint "{endpoint_name}" non trouvé'))
            return {
                'endpoint': endpoint_name,
                'method': method,
                'iterations': iterations,
                'successful_requests': 0,
                'failed_requests': iterations,
                'errors': [{'error': f'Endpoint non trouvé: {endpoint_name}'}],
            }
        
        factory = APIRequestFactory()
        view = view_class.as_view()
        
        times = []
        status_codes = []
        response_sizes = []
        errors = []

        for i in range(iterations):
            try:
                start_time = time.time()
                
                # Créer la requête
                if method == 'GET':
                    request = factory.get(f'/mobile/api/{endpoint_name}/')
                elif method == 'POST':
                    request = factory.post(f'/mobile/api/{endpoint_name}/')
                else:
                    request = factory.request(method=method, path=f'/mobile/api/{endpoint_name}/')
                
                # Authentifier la requête
                force_authenticate(request, user=user, token=token)
                
                # Appeler la vue
                if assignment_id:
                    response = view(request, assignment_id=assignment_id)
                else:
                    response = view(request)
                
                elapsed_time = (time.time() - start_time) * 1000  # en millisecondes
                
                times.append(elapsed_time)
                status_codes.append(response.status_code)
                
                # Taille de la réponse en bytes
                if hasattr(response, 'data'):
                    import json
                    response_sizes.append(len(json.dumps(response.data).encode('utf-8')))
                elif hasattr(response, 'content'):
                    response_sizes.append(len(response.content))
                
                # Vérifier les erreurs
                if response.status_code >= 400:
                    try:
                        error_data = response.data if hasattr(response, 'data') else {}
                        errors.append({
                            'iteration': i + 1,
                            'status': response.status_code,
                            'error': error_data
                        })
                    except:
                        errors.append({
                            'iteration': i + 1,
                            'status': response.status_code,
                            'error': 'Erreur non JSON'
                        })
                
            except Exception as e:
                errors.append({
                    'iteration': i + 1,
                    'error': str(e)
                })
                times.append(None)

        # Calcul des statistiques
        valid_times = [t for t in times if t is not None]
        
        stats = {
            'endpoint': endpoint_name,
            'method': method,
            'iterations': iterations,
            'successful_requests': len(valid_times),
            'failed_requests': len([t for t in times if t is None]),
            'errors': errors,
            'status_codes': status_codes,
        }
        
        if valid_times:
            stats.update({
                'min_time': min(valid_times),
                'max_time': max(valid_times),
                'avg_time': statistics.mean(valid_times),
                'median_time': statistics.median(valid_times),
                'std_dev': statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            })
            
            # Taux de requêtes par seconde
            stats['requests_per_second'] = 1000 / stats['avg_time'] if stats['avg_time'] > 0 else 0
        else:
            stats.update({
                'min_time': 0,
                'max_time': 0,
                'avg_time': 0,
                'median_time': 0,
                'std_dev': 0,
                'requests_per_second': 0,
            })
        
        if response_sizes:
            stats.update({
                'avg_response_size': statistics.mean(response_sizes),
                'total_response_size': sum(response_sizes),
            })
        else:
            stats.update({
                'avg_response_size': 0,
                'total_response_size': 0,
            })
        
        # Affichage des résultats
        self.stdout.write(f'  [OK] Requetes reussies: {stats["successful_requests"]}/{iterations}')
        if stats['successful_requests'] > 0:
            self.stdout.write(f'  [OK] Temps moyen: {stats["avg_time"]:.2f} ms')
            self.stdout.write(f'  [OK] Temps median: {stats["median_time"]:.2f} ms')
            self.stdout.write(f'  [OK] Temps min: {stats["min_time"]:.2f} ms')
            self.stdout.write(f'  [OK] Temps max: {stats["max_time"]:.2f} ms')
            self.stdout.write(f'  [OK] Debit: {stats["requests_per_second"]:.2f} req/s')
            if stats.get('avg_response_size'):
                self.stdout.write(f'  [OK] Taille moyenne reponse: {stats["avg_response_size"]/1024:.2f} KB')
        if errors:
            self.stdout.write(self.style.ERROR(f'  [ERREUR] Erreurs: {len(errors)}'))
        self.stdout.write('')
        
        return stats

    def print_report(self, results: Dict, iterations: int):
        """
        Affiche un rapport récapitulatif des performances.
        
        Args:
            results: Dictionnaire avec les résultats de tous les tests
            iterations: Nombre d'itérations
        """
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('RAPPORT DE PERFORMANCE'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # Tableau récapitulatif
        self.stdout.write(f'{"Endpoint":<40} {"Moyenne (ms)":<15} {"Médiane (ms)":<15} {"Débit (req/s)":<15}')
        self.stdout.write('-' * 85)
        
        for name, stats in results.items():
            if stats['successful_requests'] > 0:
                endpoint = stats['endpoint']
                avg = f"{stats['avg_time']:.2f}"
                median = f"{stats['median_time']:.2f}"
                rps = f"{stats['requests_per_second']:.2f}"
                self.stdout.write(f'{endpoint:<40} {avg:<15} {median:<15} {rps:<15}')
            else:
                endpoint = stats['endpoint']
                self.stdout.write(
                    self.style.ERROR(f'{endpoint:<40} {"ÉCHEC":<15} {"ÉCHEC":<15} {"0.00":<15}')
                )
        
        self.stdout.write('')
        
        # Détails des erreurs
        has_errors = any(stats.get('errors') for stats in results.values())
        if has_errors:
            self.stdout.write(self.style.WARNING('ERREURS DÉTECTÉES:'))
            self.stdout.write('-' * 80)
            for name, stats in results.items():
                if stats.get('errors'):
                    self.stdout.write(f'\n{name.upper()}:')
                    for error in stats['errors'][:5]:  # Limiter à 5 erreurs
                        self.stdout.write(f"  Itération {error.get('iteration', '?')}: {error.get('error', 'Erreur inconnue')}")
            self.stdout.write('')
        
        # Recommandations
        self.stdout.write(self.style.SUCCESS('RECOMMANDATIONS:'))
        self.stdout.write('-' * 80)
        
        for name, stats in results.items():
            if stats['successful_requests'] > 0:
                avg_time = stats['avg_time']
                if avg_time > 1000:
                    self.stdout.write(
                        self.style.WARNING(f'[ATTENTION] {name}: Temps de reponse eleve ({avg_time:.2f} ms)')
                    )
                elif avg_time > 500:
                    self.stdout.write(
                        f'[INFO] {name}: Temps de reponse modere ({avg_time:.2f} ms)'
                    )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))

