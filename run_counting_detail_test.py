#!/usr/bin/env python
"""
Script simple pour exécuter le test de 1000 CountingDetail.
Ce script configure l'environnement et lance les tests de performance.

Usage:
    python run_counting_detail_test.py

Ou pour un test rapide (100 éléments):
    python run_counting_detail_test.py --quick

Ou pour un test personnalisé:
    python run_counting_detail_test.py --count 500
"""

import os
import sys
import argparse
import django
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from test_counting_detail_1000_lines import CountingDetailPerformanceTest


class SimpleTestRunner:
    """Runner simplifié pour les tests de performance."""
    
    def __init__(self, count=1000, parallel=True, validation=True):
        self.count = count
        self.parallel = parallel
        self.validation = validation
        self.test_suite = CountingDetailPerformanceTest()
    
    def run_quick_test(self):
        """Exécute un test rapide avec moins d'éléments."""
        print(f"🚀 TEST RAPIDE - {self.count} COUNTING DETAIL")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Configuration
            self.test_suite.setUp()
            
            if self.validation:
                # Tests de validation rapides
                print("\n🧪 Tests de validation...")
                validation_results = self.test_suite.test_api_validation_scenarios()
                print(f"✅ {len(validation_results)} tests de validation exécutés")
            
            # Test de performance adapté
            print(f"\n🚀 Test de performance - {self.count} éléments...")
            
            if self.count <= 100:
                # Test séquentiel pour les petits nombres
                results = self._run_sequential_test(self.count)
            else:
                # Test parallèle pour les grands nombres
                if self.parallel:
                    results = self._run_parallel_test(self.count)
                else:
                    results = self._run_sequential_test(self.count)
            
            # Rapport simplifié
            self._generate_simple_report()
            
            print(f"\n🏁 TEST TERMINÉ!")
            print(f"📊 Résumé: {self.test_suite.performance_metrics['success_count']}/{self.count} succès")
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.test_suite.cleanup()
    
    def _run_sequential_test(self, count):
        """Exécute un test séquentiel avec un nombre personnalisé."""
        import time
        import random
        
        start_time = time.time()
        results = []
        
        for i in range(count):
            data = self.test_suite._generate_test_data(i)
            result = self.test_suite._create_counting_detail_api(data, i)
            results.append(result)
            
            # Mise à jour des métriques
            if result['success']:
                self.test_suite.performance_metrics['success_count'] += 1
                self.test_suite.performance_metrics['creation_times'].append(result['response_time'])
            else:
                self.test_suite.performance_metrics['error_count'] += 1
                self.test_suite.performance_metrics['errors'].append({
                    'index': i,
                    'error': result.get('error', 'Unknown error'),
                    'data': result['data']
                })
            
            self.test_suite.performance_metrics['response_times'].append(result['response_time'])
            
            # Affichage du progrès
            if (i + 1) % max(1, count // 10) == 0:
                print(f"  ✅ {i + 1}/{count} CountingDetail traités")
        
        total_time = time.time() - start_time
        print(f"⏱️ Temps total: {total_time:.2f} secondes")
        
        return results
    
    def _run_parallel_test(self, count):
        """Exécute un test parallèle avec un nombre personnalisé."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        start_time = time.time()
        results = []
        
        # Adapter le nombre de workers selon le nombre d'éléments
        max_workers = min(10, max(2, count // 50))
        batch_size = max(10, count // max_workers)
        
        print(f"🔧 Configuration parallèle: {max_workers} workers, lots de {batch_size}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for batch_start in range(0, count, batch_size):
                current_batch_size = min(batch_size, count - batch_start)
                future = executor.submit(
                    self.test_suite._create_counting_detail_batch, 
                    batch_start, 
                    current_batch_size
                )
                futures.append(future)
            
            # Collecter les résultats
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    
                    # Mise à jour des métriques
                    for result in batch_results:
                        if result['success']:
                            self.test_suite.performance_metrics['success_count'] += 1
                            self.test_suite.performance_metrics['creation_times'].append(result['response_time'])
                        else:
                            self.test_suite.performance_metrics['error_count'] += 1
                            self.test_suite.performance_metrics['errors'].append({
                                'index': result['index'],
                                'error': result.get('error', 'Unknown error'),
                                'data': result['data']
                            })
                        
                        self.test_suite.performance_metrics['response_times'].append(result['response_time'])
                        
                except Exception as e:
                    print(f"❌ Erreur dans le lot: {e}")
        
        total_time = time.time() - start_time
        print(f"⏱️ Temps total: {total_time:.2f} secondes")
        
        return results
    
    def _generate_simple_report(self):
        """Génère un rapport simplifié."""
        import statistics
        
        if not self.test_suite.performance_metrics['response_times']:
            print("❌ Aucune donnée de performance disponible")
            return
        
        response_times = self.test_suite.performance_metrics['response_times']
        success_count = self.test_suite.performance_metrics['success_count']
        error_count = self.test_suite.performance_metrics['error_count']
        
        print(f"\n📊 RAPPORT DE PERFORMANCE")
        print("-" * 40)
        print(f"✅ Succès: {success_count}/{len(response_times)} ({success_count/len(response_times)*100:.1f}%)")
        print(f"❌ Erreurs: {error_count}")
        print(f"⏱️ Temps moyen: {statistics.mean(response_times):.3f}s")
        print(f"⚡ Temps médian: {statistics.median(response_times):.3f}s")
        print(f"🐌 Temps max: {max(response_times):.3f}s")
        print(f"🚀 Temps min: {min(response_times):.3f}s")
        
        # Throughput
        total_time = sum(response_times)
        if total_time > 0:
            throughput = len(response_times) / total_time
            print(f"📈 Débit: {throughput:.1f} requêtes/seconde")


def main():
    """Fonction principale avec gestion des arguments."""
    parser = argparse.ArgumentParser(
        description="Test de performance pour l'API CountingDetail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python run_counting_detail_test.py                 # Test complet (1000 éléments)
  python run_counting_detail_test.py --quick         # Test rapide (100 éléments)
  python run_counting_detail_test.py --count 500     # Test personnalisé (500 éléments)
  python run_counting_detail_test.py --count 50 --sequential  # 50 éléments en séquentiel
        """
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true', 
        help='Test rapide avec 100 éléments'
    )
    
    parser.add_argument(
        '--count', 
        type=int, 
        default=1000, 
        help='Nombre de CountingDetail à créer (défaut: 1000)'
    )
    
    parser.add_argument(
        '--sequential', 
        action='store_true', 
        help='Forcer le mode séquentiel'
    )
    
    parser.add_argument(
        '--no-validation', 
        action='store_true', 
        help='Ignorer les tests de validation'
    )
    
    args = parser.parse_args()
    
    # Déterminer les paramètres du test
    if args.quick:
        count = 100
    else:
        count = args.count
    
    parallel = not args.sequential and count > 50
    validation = not args.no_validation
    
    print(f"🎯 Configuration du test:")
    print(f"  • Nombre d'éléments: {count}")
    print(f"  • Mode: {'Parallèle' if parallel else 'Séquentiel'}")
    print(f"  • Tests de validation: {'Oui' if validation else 'Non'}")
    print()
    
    # Exécuter le test
    runner = SimpleTestRunner(count=count, parallel=parallel, validation=validation)
    
    if count == 1000 and parallel and validation:
        # Test complet
        print("🚀 Exécution du test complet...")
        runner.test_suite.run_full_test_suite()
    else:
        # Test personnalisé
        runner.run_quick_test()


if __name__ == "__main__":
    main()
