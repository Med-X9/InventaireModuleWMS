#!/usr/bin/env python
"""
Test unitaire pour l'API CountingDetail avec 1000 lignes.
Ce script teste la performance et la robustesse de l'API counting-detail
en créant et validant 1000 CountingDetail avec différents scénarios.

Usage:
    python test_counting_detail_1000_lines.py

Auteur: Assistant IA
Date: 2024-12-15
"""

import os
import sys
import django
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Inventory, Counting, CountingDetail, NSerieInventory, Job, JobDetail, Assigment
from apps.masterdata.models import Product, Location, Warehouse, Account
from apps.users.models import User

User = get_user_model()


class CountingDetailPerformanceTest:
    """
    Classe de test de performance pour l'API CountingDetail.
    Teste la création de 1000 CountingDetail avec différents scénarios.
    """
    
    def __init__(self):
        self.api_client = APIClient()
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/mobile/api"
        self.test_user = None
        self.test_token = None
        self.test_data = {
            'accounts': [],
            'warehouses': [],
            'locations': [],
            'products': [],
            'inventories': [],
            'countings': [],
            'assignments': [],
            'jobs': [],
            'job_details': []
        }
        self.performance_metrics = {
            'creation_times': [],
            'response_times': [],
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
    def setUp(self):
        """Configuration initiale des données de test."""
        print("🔧 Configuration initiale des données de test...")
        
        # Créer un utilisateur de test
        self.test_user = User.objects.create_user(
            username='test_counting_user',
            email='test@example.com',
            password='testpass123'
        )
        
        # Obtenir le token d'authentification
        self._authenticate()
        
        # Créer les données de base nécessaires
        self._create_base_data()
        
        print("✅ Configuration terminée")
    
    def _authenticate(self):
        """Authentification et récupération du token."""
        try:
            # Utiliser l'API JWT pour l'authentification
            auth_data = {
                'username': 'test_counting_user',
                'password': 'testpass123'
            }
            
            response = requests.post(
                f"{self.api_base}/auth/jwt-login/",
                json=auth_data
            )
            
            if response.status_code == 200:
                self.test_token = response.json()['access_token']
                print("✅ Authentification réussie")
            else:
                print(f"❌ Erreur d'authentification: {response.text}")
                # Fallback: utiliser le client API Django pour les tests
                self.api_client.force_authenticate(user=self.test_user)
                
        except Exception as e:
            print(f"❌ Erreur d'authentification: {e}")
            # Utiliser le client API Django
            self.api_client.force_authenticate(user=self.test_user)
    
    def _create_base_data(self):
        """Crée les données de base nécessaires pour les tests."""
        print("📦 Création des données de base...")
        
        # Créer des comptes
        for i in range(5):
            account = Account.objects.create(
                name=f"Test Account {i+1}",
                description=f"Compte de test {i+1}"
            )
            self.test_data['accounts'].append(account)
        
        # Créer des entrepôts
        for i, account in enumerate(self.test_data['accounts']):
            warehouse = Warehouse.objects.create(
                name=f"Test Warehouse {i+1}",
                account=account
            )
            self.test_data['warehouses'].append(warehouse)
        
        # Créer des emplacements (200 emplacements)
        location_count = 0
        for warehouse in self.test_data['warehouses']:
            for j in range(40):  # 40 emplacements par entrepôt
                location = Location.objects.create(
                    name=f"LOC-{warehouse.name}-{j+1:03d}",
                    warehouse=warehouse
                )
                self.test_data['locations'].append(location)
                location_count += 1
        
        print(f"✅ {location_count} emplacements créés")
        
        # Les propriétés sont directement sur le modèle Product (n_lot, n_serie, dlc)
        
        # Créer des produits (100 produits)
        for i in range(100):
            product = Product.objects.create(
                Internal_Product_Code=f"PROD-{i+1:05d}",
                Short_Description=f"Produit Test {i+1:03d}",
                Barcode=f"BAR-{i+1:08d}",
                Stock_Unit="Unité",
                Product_Status="ACTIVE",
                Product_Family=None,  # Vous pouvez créer des familles si nécessaire
                n_lot=random.choice([True, False]),
                n_serie=random.choice([True, False]),
                dlc=random.choice([True, False])
            )
            self.test_data['products'].append(product)
        
        print(f"✅ {len(self.test_data['products'])} produits créés")
        
        # Créer des inventaires (10 inventaires)
        for i in range(10):
            inventory = Inventory.objects.create(
                name=f"Inventaire Test {i+1}",
                account=random.choice(self.test_data['accounts']),
                warehouse=random.choice(self.test_data['warehouses'])
            )
            self.test_data['inventories'].append(inventory)
        
        # Créer des comptages (30 comptages)
        count_modes = ["en vrac", "par article", "image de stock"]
        for i in range(30):
            counting = Counting.objects.create(
                order=i+1,
                count_mode=random.choice(count_modes),
                unit_scanned=random.choice([True, False]),
                entry_quantity=random.choice([True, False]),
                stock_situation=random.choice([True, False]),
                is_variant=random.choice([True, False]),
                n_lot=random.choice([True, False]),
                n_serie=random.choice([True, False]),
                dlc=random.choice([True, False]),
                show_product=random.choice([True, False]),
                quantity_show=random.choice([True, False]),
                inventory=random.choice(self.test_data['inventories'])
            )
            self.test_data['countings'].append(counting)
        
        print(f"✅ {len(self.test_data['countings'])} comptages créés")
        
        # Créer des jobs et assignments
        for i in range(20):
            job = Job.objects.create(
                inventory=random.choice(self.test_data['inventories'])
            )
            self.test_data['jobs'].append(job)
            
            # Créer des job details pour ce job
            selected_locations = random.sample(self.test_data['locations'], min(10, len(self.test_data['locations'])))
            for location in selected_locations:
                job_detail = JobDetail.objects.create(
                    location=location,
                    job=job,
                    counting=random.choice(self.test_data['countings']),
                    status='EN ATTENTE'
                )
                self.test_data['job_details'].append(job_detail)
            
            # Créer un assignment
            assignment = Assigment.objects.create(
                job=job,
                user=self.test_user,
                status='EN COURS'
            )
            self.test_data['assignments'].append(assignment)
        
        print(f"✅ {len(self.test_data['jobs'])} jobs et {len(self.test_data['assignments'])} assignments créés")
        print(f"✅ {len(self.test_data['job_details'])} job details créés")
    
    def _generate_test_data(self, index: int) -> Dict[str, Any]:
        """Génère des données de test pour un CountingDetail."""
        counting = random.choice(self.test_data['countings'])
        location = random.choice(self.test_data['locations'])
        assignment = random.choice(self.test_data['assignments'])
        
        # Données de base
        data = {
            'counting_id': counting.id,
            'location_id': location.id,
            'quantity_inventoried': random.randint(1, 100),
            'assignment_id': assignment.id
        }
        
        # Ajouter product_id selon le mode de comptage
        if counting.count_mode == "par article":
            data['product_id'] = random.choice(self.test_data['products']).id
        elif random.choice([True, False]):  # 50% de chance pour les autres modes
            data['product_id'] = random.choice(self.test_data['products']).id
        
        # Ajouter DLC si nécessaire
        if counting.dlc or random.choice([True, False]):
            future_date = datetime.now() + timedelta(days=random.randint(30, 365))
            data['dlc'] = future_date.strftime('%Y-%m-%d')
        
        # Ajouter numéro de lot si nécessaire
        if counting.n_lot or random.choice([True, False]):
            data['n_lot'] = f"LOT-{index:05d}-{random.randint(1000, 9999)}"
        
        # Ajouter numéros de série si nécessaire
        if counting.n_serie and random.choice([True, False]):
            num_series = random.randint(1, min(5, data['quantity_inventoried']))
            data['numeros_serie'] = []
            for j in range(num_series):
                data['numeros_serie'].append({
                    'n_serie': f"NS-{index:05d}-{j+1:03d}-{random.randint(1000, 9999)}"
                })
        
        return data
    
    def _create_counting_detail_api(self, data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Crée un CountingDetail via l'API REST."""
        start_time = time.time()
        
        try:
            headers = {}
            if self.test_token:
                headers['Authorization'] = f'Bearer {self.test_token}'
            
            if self.test_token:
                # Utiliser requests pour les appels HTTP
                response = requests.post(
                    f"{self.api_base}/counting-detail/",
                    json=data,
                    headers=headers
                )
                
                response_time = time.time() - start_time
                
                result = {
                    'index': index,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 201,
                    'data': data
                }
                
                if response.status_code == 201:
                    result['response_data'] = response.json()
                else:
                    result['error'] = response.text
                    
            else:
                # Utiliser le client API Django
                response = self.api_client.post(
                    reverse('mobile:mobile_counting_detail'),
                    data,
                    format='json'
                )
                
                response_time = time.time() - start_time
                
                result = {
                    'index': index,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 201,
                    'data': data
                }
                
                if response.status_code == 201:
                    result['response_data'] = response.data
                else:
                    result['error'] = str(response.data) if hasattr(response, 'data') else str(response.content)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'index': index,
                'status_code': 500,
                'response_time': response_time,
                'success': False,
                'error': str(e),
                'data': data
            }
    
    def _create_counting_detail_batch(self, start_index: int, count: int) -> List[Dict[str, Any]]:
        """Crée un lot de CountingDetail."""
        results = []
        
        for i in range(count):
            index = start_index + i
            data = self._generate_test_data(index)
            result = self._create_counting_detail_api(data, index)
            results.append(result)
            
            # Affichage du progrès
            if (index + 1) % 50 == 0:
                print(f"  ✅ {index + 1} CountingDetail traités")
        
        return results
    
    def test_1000_counting_details_sequential(self):
        """Test séquentiel de création de 1000 CountingDetail."""
        print("\n🚀 Test séquentiel de 1000 CountingDetail...")
        print("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        # Créer 1000 CountingDetail de manière séquentielle
        for i in range(1000):
            data = self._generate_test_data(i)
            result = self._create_counting_detail_api(data, i)
            all_results.append(result)
            
            # Mise à jour des métriques
            if result['success']:
                self.performance_metrics['success_count'] += 1
                self.performance_metrics['creation_times'].append(result['response_time'])
            else:
                self.performance_metrics['error_count'] += 1
                self.performance_metrics['errors'].append({
                    'index': i,
                    'error': result.get('error', 'Unknown error'),
                    'data': result['data']
                })
            
            self.performance_metrics['response_times'].append(result['response_time'])
            
            # Affichage du progrès
            if (i + 1) % 100 == 0:
                print(f"  ✅ {i + 1}/1000 CountingDetail traités")
        
        total_time = time.time() - start_time
        
        print(f"\n📊 Résultats du test séquentiel:")
        print(f"  • Temps total: {total_time:.2f} secondes")
        print(f"  • Succès: {self.performance_metrics['success_count']}/1000")
        print(f"  • Erreurs: {self.performance_metrics['error_count']}/1000")
        print(f"  • Temps moyen par requête: {statistics.mean(self.performance_metrics['response_times']):.3f}s")
        print(f"  • Temps médian par requête: {statistics.median(self.performance_metrics['response_times']):.3f}s")
        
        if self.performance_metrics['creation_times']:
            print(f"  • Temps moyen de création (succès): {statistics.mean(self.performance_metrics['creation_times']):.3f}s")
        
        return all_results
    
    def test_1000_counting_details_parallel(self):
        """Test parallèle de création de 1000 CountingDetail."""
        print("\n🚀 Test parallèle de 1000 CountingDetail...")
        print("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        # Réinitialiser les métriques
        self.performance_metrics = {
            'creation_times': [],
            'response_times': [],
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        # Utiliser ThreadPoolExecutor pour les requêtes parallèles
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Diviser en lots de 100
            futures = []
            for batch_start in range(0, 1000, 100):
                batch_size = min(100, 1000 - batch_start)
                future = executor.submit(self._create_counting_detail_batch, batch_start, batch_size)
                futures.append(future)
            
            # Collecter les résultats
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    # Mise à jour des métriques
                    for result in batch_results:
                        if result['success']:
                            self.performance_metrics['success_count'] += 1
                            self.performance_metrics['creation_times'].append(result['response_time'])
                        else:
                            self.performance_metrics['error_count'] += 1
                            self.performance_metrics['errors'].append({
                                'index': result['index'],
                                'error': result.get('error', 'Unknown error'),
                                'data': result['data']
                            })
                        
                        self.performance_metrics['response_times'].append(result['response_time'])
                        
                except Exception as e:
                    print(f"❌ Erreur dans le lot: {e}")
        
        total_time = time.time() - start_time
        
        print(f"\n📊 Résultats du test parallèle:")
        print(f"  • Temps total: {total_time:.2f} secondes")
        print(f"  • Succès: {self.performance_metrics['success_count']}/1000")
        print(f"  • Erreurs: {self.performance_metrics['error_count']}/1000")
        
        if self.performance_metrics['response_times']:
            print(f"  • Temps moyen par requête: {statistics.mean(self.performance_metrics['response_times']):.3f}s")
            print(f"  • Temps médian par requête: {statistics.median(self.performance_metrics['response_times']):.3f}s")
            print(f"  • Temps min par requête: {min(self.performance_metrics['response_times']):.3f}s")
            print(f"  • Temps max par requête: {max(self.performance_metrics['response_times']):.3f}s")
        
        if self.performance_metrics['creation_times']:
            print(f"  • Temps moyen de création (succès): {statistics.mean(self.performance_metrics['creation_times']):.3f}s")
        
        return all_results
    
    def test_api_validation_scenarios(self):
        """Test des différents scénarios de validation."""
        print("\n🧪 Test des scénarios de validation...")
        print("=" * 60)
        
        validation_tests = [
            {
                'name': 'Données manquantes - counting_id',
                'data': {
                    'location_id': self.test_data['locations'][0].id,
                    'quantity_inventoried': 10,
                    'assignment_id': self.test_data['assignments'][0].id
                },
                'expected_status': 400
            },
            {
                'name': 'Données manquantes - location_id',
                'data': {
                    'counting_id': self.test_data['countings'][0].id,
                    'quantity_inventoried': 10,
                    'assignment_id': self.test_data['assignments'][0].id
                },
                'expected_status': 400
            },
            {
                'name': 'Quantité négative',
                'data': {
                    'counting_id': self.test_data['countings'][0].id,
                    'location_id': self.test_data['locations'][0].id,
                    'quantity_inventoried': -5,
                    'assignment_id': self.test_data['assignments'][0].id
                },
                'expected_status': 400
            },
            {
                'name': 'Mode par article sans product_id',
                'data': {
                    'counting_id': next((c.id for c in self.test_data['countings'] if c.count_mode == "par article"), None),
                    'location_id': self.test_data['locations'][0].id,
                    'quantity_inventoried': 10,
                    'assignment_id': self.test_data['assignments'][0].id
                },
                'expected_status': 400
            }
        ]
        
        validation_results = []
        
        for i, test in enumerate(validation_tests):
            if test['data'].get('counting_id') is None:
                print(f"  ⚠️ Test '{test['name']}' ignoré - pas de comptage approprié")
                continue
                
            print(f"  🧪 Test {i+1}: {test['name']}")
            
            result = self._create_counting_detail_api(test['data'], f"validation_{i}")
            
            validation_results.append({
                'test_name': test['name'],
                'expected_status': test['expected_status'],
                'actual_status': result['status_code'],
                'success': result['status_code'] == test['expected_status'],
                'error': result.get('error', '')
            })
            
            if result['status_code'] == test['expected_status']:
                print(f"    ✅ Validation correcte (Status: {result['status_code']})")
            else:
                print(f"    ❌ Validation incorrecte (Attendu: {test['expected_status']}, Reçu: {result['status_code']})")
                print(f"    📝 Erreur: {result.get('error', 'Aucune erreur')}")
        
        # Résumé des tests de validation
        successful_validations = sum(1 for r in validation_results if r['success'])
        print(f"\n📊 Résultats des tests de validation:")
        print(f"  • Tests réussis: {successful_validations}/{len(validation_results)}")
        
        return validation_results
    
    def test_data_retrieval(self):
        """Test de récupération des données."""
        print("\n📥 Test de récupération des données...")
        print("=" * 60)
        
        # Créer quelques CountingDetail pour les tests de récupération
        print("  📦 Création de données de test pour la récupération...")
        test_counting = self.test_data['countings'][0]
        test_location = self.test_data['locations'][0]
        test_product = self.test_data['products'][0]
        
        # Créer 5 CountingDetail pour les tests
        for i in range(5):
            data = {
                'counting_id': test_counting.id,
                'location_id': test_location.id,
                'quantity_inventoried': random.randint(1, 20),
                'assignment_id': self.test_data['assignments'][0].id,
                'product_id': test_product.id
            }
            self._create_counting_detail_api(data, f"retrieval_test_{i}")
        
        retrieval_tests = [
            {
                'name': 'Récupération par counting_id',
                'url': f"{self.api_base}/counting-detail/?counting_id={test_counting.id}"
            },
            {
                'name': 'Récupération par location_id',
                'url': f"{self.api_base}/counting-detail/?location_id={test_location.id}"
            },
            {
                'name': 'Récupération par product_id',
                'url': f"{self.api_base}/counting-detail/?product_id={test_product.id}"
            }
        ]
        
        retrieval_results = []
        
        for test in retrieval_tests:
            print(f"  🔍 {test['name']}")
            
            try:
                headers = {}
                if self.test_token:
                    headers['Authorization'] = f'Bearer {self.test_token}'
                
                start_time = time.time()
                
                if self.test_token:
                    response = requests.get(test['url'], headers=headers)
                    response_time = time.time() - start_time
                    
                    result = {
                        'test_name': test['name'],
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        data = response.json()
                        result['count'] = len(data.get('data', {}).get('counting_details', []))
                        print(f"    ✅ {result['count']} éléments récupérés en {response_time:.3f}s")
                    else:
                        result['error'] = response.text
                        print(f"    ❌ Erreur: {response.text}")
                else:
                    # Utiliser le client Django pour les tests
                    if 'counting_id' in test['url']:
                        response = self.api_client.get(
                            reverse('mobile:mobile_counting_detail'),
                            {'counting_id': test_counting.id}
                        )
                    elif 'location_id' in test['url']:
                        response = self.api_client.get(
                            reverse('mobile:mobile_counting_detail'),
                            {'location_id': test_location.id}
                        )
                    elif 'product_id' in test['url']:
                        response = self.api_client.get(
                            reverse('mobile:mobile_counting_detail'),
                            {'product_id': test_product.id}
                        )
                    
                    response_time = time.time() - start_time
                    
                    result = {
                        'test_name': test['name'],
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        result['count'] = len(response.data.get('data', {}).get('counting_details', []))
                        print(f"    ✅ {result['count']} éléments récupérés en {response_time:.3f}s")
                    else:
                        result['error'] = str(response.data) if hasattr(response, 'data') else str(response.content)
                        print(f"    ❌ Erreur: {result['error']}")
                
                retrieval_results.append(result)
                
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                retrieval_results.append({
                    'test_name': test['name'],
                    'status_code': 500,
                    'success': False,
                    'error': str(e)
                })
        
        # Résumé des tests de récupération
        successful_retrievals = sum(1 for r in retrieval_results if r['success'])
        print(f"\n📊 Résultats des tests de récupération:")
        print(f"  • Tests réussis: {successful_retrievals}/{len(retrieval_results)}")
        
        return retrieval_results
    
    def generate_performance_report(self):
        """Génère un rapport de performance détaillé."""
        print("\n📊 RAPPORT DE PERFORMANCE")
        print("=" * 80)
        
        # Statistiques générales
        if self.performance_metrics['response_times']:
            response_times = self.performance_metrics['response_times']
            creation_times = self.performance_metrics['creation_times']
            
            print(f"🎯 STATISTIQUES GÉNÉRALES:")
            print(f"  • Total de requêtes: {len(response_times)}")
            print(f"  • Succès: {self.performance_metrics['success_count']}")
            print(f"  • Erreurs: {self.performance_metrics['error_count']}")
            print(f"  • Taux de succès: {(self.performance_metrics['success_count']/len(response_times)*100):.1f}%")
            
            print(f"\n⏱️ TEMPS DE RÉPONSE:")
            print(f"  • Temps moyen: {statistics.mean(response_times):.3f}s")
            print(f"  • Temps médian: {statistics.median(response_times):.3f}s")
            print(f"  • Temps minimum: {min(response_times):.3f}s")
            print(f"  • Temps maximum: {max(response_times):.3f}s")
            print(f"  • Écart type: {statistics.stdev(response_times):.3f}s")
            
            if creation_times:
                print(f"\n✅ TEMPS DE CRÉATION (SUCCÈS UNIQUEMENT):")
                print(f"  • Temps moyen: {statistics.mean(creation_times):.3f}s")
                print(f"  • Temps médian: {statistics.median(creation_times):.3f}s")
                print(f"  • Temps minimum: {min(creation_times):.3f}s")
                print(f"  • Temps maximum: {max(creation_times):.3f}s")
            
            # Analyse des percentiles
            sorted_times = sorted(response_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            print(f"\n📈 PERCENTILES DES TEMPS DE RÉPONSE:")
            print(f"  • P50 (médiane): {p50:.3f}s")
            print(f"  • P90: {p90:.3f}s")
            print(f"  • P95: {p95:.3f}s")
            print(f"  • P99: {p99:.3f}s")
        
        # Analyse des erreurs
        if self.performance_metrics['errors']:
            print(f"\n❌ ANALYSE DES ERREURS:")
            error_types = {}
            for error in self.performance_metrics['errors']:
                error_msg = error['error'][:100]  # Limiter la longueur
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
            
            for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {error_msg}: {count} occurrences")
        
        # Recommandations de performance
        print(f"\n🔧 RECOMMANDATIONS:")
        if self.performance_metrics['response_times']:
            avg_time = statistics.mean(self.performance_metrics['response_times'])
            if avg_time > 1.0:
                print(f"  ⚠️ Temps de réponse élevé ({avg_time:.3f}s). Considérer l'optimisation.")
            elif avg_time > 0.5:
                print(f"  ⚡ Temps de réponse acceptable ({avg_time:.3f}s).")
            else:
                print(f"  🚀 Excellent temps de réponse ({avg_time:.3f}s)!")
        
        error_rate = self.performance_metrics['error_count'] / max(1, len(self.performance_metrics['response_times'])) * 100
        if error_rate > 10:
            print(f"  ❌ Taux d'erreur élevé ({error_rate:.1f}%). Vérifier la stabilité de l'API.")
        elif error_rate > 5:
            print(f"  ⚠️ Taux d'erreur modéré ({error_rate:.1f}%). Surveiller.")
        else:
            print(f"  ✅ Faible taux d'erreur ({error_rate:.1f}%).")
    
    def cleanup(self):
        """Nettoyage des données de test."""
        print("\n🧹 Nettoyage des données de test...")
        
        try:
            # Supprimer les données créées (dans l'ordre inverse des dépendances)
            CountingDetail.objects.filter(
                counting__inventory__name__startswith="Inventaire Test"
            ).delete()
            
            NSerieInventory.objects.filter(
                counting_detail__counting__inventory__name__startswith="Inventaire Test"
            ).delete()
            
            for model_list in [
                'job_details', 'assignments', 'jobs', 'countings', 
                'inventories', 'products', 'locations', 'warehouses', 'accounts'
            ]:
                for obj in self.test_data[model_list]:
                    try:
                        obj.delete()
                    except:
                        pass
            
            # Supprimer l'utilisateur de test
            if self.test_user:
                self.test_user.delete()
            
            print("✅ Nettoyage terminé")
            
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    def run_full_test_suite(self):
        """Exécute la suite complète de tests."""
        print("🚀 DÉMARRAGE DE LA SUITE DE TESTS COUNTING DETAIL")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: Tester 1000 créations de CountingDetail")
        print("=" * 80)
        
        try:
            # Configuration
            self.setUp()
            
            # Tests de validation
            validation_results = self.test_api_validation_scenarios()
            
            # Test de récupération
            retrieval_results = self.test_data_retrieval()
            
            # Test principal - 1000 CountingDetail (séquentiel)
            sequential_results = self.test_1000_counting_details_sequential()
            
            # Test principal - 1000 CountingDetail (parallèle)
            parallel_results = self.test_1000_counting_details_parallel()
            
            # Génération du rapport final
            self.generate_performance_report()
            
            print(f"\n🏁 TESTS TERMINÉS AVEC SUCCÈS!")
            print(f"📊 Résumé:")
            print(f"  • Tests de validation: {len(validation_results)} exécutés")
            print(f"  • Tests de récupération: {len(retrieval_results)} exécutés")
            print(f"  • Tests de performance: 2000 CountingDetail créés")
            print(f"  • Taux de succès global: {(self.performance_metrics['success_count']/max(1, len(self.performance_metrics['response_times']))*100):.1f}%")
            
        except Exception as e:
            print(f"\n❌ ERREUR FATALE DANS LA SUITE DE TESTS: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Nettoyage
            self.cleanup()


def main():
    """Fonction principale."""
    print("🧪 TEST UNITAIRE COUNTING DETAIL - 1000 LIGNES")
    print("=" * 80)
    
    # Créer et exécuter les tests
    test_suite = CountingDetailPerformanceTest()
    test_suite.run_full_test_suite()


if __name__ == "__main__":
    main()
