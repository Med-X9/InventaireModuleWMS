# Test de Performance - API CountingDetail (1000 lignes)

## 📋 Description

Ce test unitaire évalue la performance et la robustesse de l'API `counting-detail` en créant et validant **1000 CountingDetail** avec différents scénarios de test.

## 🚀 Utilisation

### Test complet (recommandé)
```bash
python run_counting_detail_test.py
```

### Test rapide (100 éléments)
```bash
python run_counting_detail_test.py --quick
```

### Test personnalisé
```bash
# Test avec 500 éléments
python run_counting_detail_test.py --count 500

# Test séquentiel avec 200 éléments
python run_counting_detail_test.py --count 200 --sequential

# Test sans validation
python run_counting_detail_test.py --count 300 --no-validation
```

### Test avancé (script complet)
```bash
python test_counting_detail_1000_lines.py
```

## 📊 Fonctionnalités

### 🧪 Tests inclus
- **Tests de validation** : Vérification des règles de validation de l'API
- **Tests de performance** : Création de 1000 CountingDetail
- **Tests de récupération** : Récupération des données par différents critères
- **Tests parallèles** : Exécution simultanée pour mesurer la charge
- **Tests séquentiels** : Exécution séquentielle pour mesurer la latence

### 📈 Métriques collectées
- Temps de réponse (moyen, médian, min, max)
- Taux de succès/erreur
- Débit (requêtes/seconde)
- Percentiles (P50, P90, P95, P99)
- Analyse des erreurs

### 🎯 Scénarios testés
- **Mode "en vrac"** : Sans produit obligatoire
- **Mode "par article"** : Avec produit obligatoire
- **Mode "image de stock"** : Configuration mixte
- **Numéros de série** : Création avec numéros de série
- **Propriétés produits** : DLC, numéros de lot
- **Validation des données** : Données manquantes, invalides

## 🏗️ Structure des données générées

### Données de base créées
- **5 comptes** (Account)
- **5 entrepôts** (Warehouse)
- **200 emplacements** (Location)
- **100 produits** (Product)
- **10 inventaires** (Inventory)
- **30 comptages** (Counting)
- **20 jobs et assignments**

### Données de test générées
- **1000 CountingDetail** avec propriétés variées
- **Numéros de série** aléatoires
- **DLC et lots** selon les règles métier
- **Quantités** aléatoires (1-100)

## 📋 Exemple de données générées

```json
{
    "counting_id": 15,
    "location_id": 87,
    "quantity_inventoried": 25,
    "assignment_id": 12,
    "product_id": 43,
    "dlc": "2024-08-15",
    "n_lot": "LOT-00234-7891",
    "numeros_serie": [
        {"n_serie": "NS-00234-001-4567"},
        {"n_serie": "NS-00234-002-4568"}
    ]
}
```

## 📊 Exemple de rapport

```
📊 RAPPORT DE PERFORMANCE
================================================================================
🎯 STATISTIQUES GÉNÉRALES:
  • Total de requêtes: 1000
  • Succès: 987
  • Erreurs: 13
  • Taux de succès: 98.7%

⏱️ TEMPS DE RÉPONSE:
  • Temps moyen: 0.245s
  • Temps médian: 0.198s
  • Temps minimum: 0.089s
  • Temps maximum: 1.234s
  • Écart type: 0.156s

📈 PERCENTILES DES TEMPS DE RÉPONSE:
  • P50 (médiane): 0.198s
  • P90: 0.456s
  • P95: 0.678s
  • P99: 0.987s

🔧 RECOMMANDATIONS:
  ⚡ Temps de réponse acceptable (0.245s).
  ✅ Faible taux d'erreur (1.3%).
```

## 🔧 Configuration

### Prérequis
- Django configuré
- Base de données accessible
- API CountingDetail fonctionnelle
- Authentification JWT (optionnelle)

### Variables d'environnement
```bash
DJANGO_SETTINGS_MODULE=project.settings
```

### Dépendances Python
- `django`
- `djangorestframework`
- `requests`
- `concurrent.futures`
- `statistics`

## 🧹 Nettoyage automatique

Le test effectue un nettoyage automatique :
- Suppression des CountingDetail créés
- Suppression des données de test
- Suppression de l'utilisateur de test
- Nettoyage des numéros de série

## ⚡ Optimisations

### Performance
- **Requêtes parallèles** : Utilisation de ThreadPoolExecutor
- **Lots optimisés** : Traitement par lots de 100 éléments
- **Gestion mémoire** : Nettoyage automatique des données

### Monitoring
- **Temps réel** : Affichage du progrès en temps réel
- **Métriques détaillées** : Collecte de toutes les métriques importantes
- **Gestion d'erreurs** : Capture et analyse des erreurs

## 🐛 Dépannage

### Erreurs communes

#### Erreur d'authentification
```bash
# Vérifier que l'API JWT fonctionne
curl -X POST http://localhost:8000/mobile/api/auth/jwt-login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

#### Erreur de base de données
```bash
# Vérifier les migrations
python manage.py showmigrations
python manage.py migrate
```

#### Erreur de permissions
```bash
# Vérifier les permissions de l'API
python manage.py shell
>>> from apps.mobile.views.counting.counting_detail_view import CountingDetailView
>>> print(CountingDetailView.permission_classes)
```

### Logs de débogage

Le test génère des logs détaillés pour le débogage :
- Temps de réponse de chaque requête
- Détails des erreurs rencontrées
- Statistiques en temps réel

## 📈 Interprétation des résultats

### Temps de réponse
- **< 0.2s** : Excellent
- **0.2-0.5s** : Bon
- **0.5-1.0s** : Acceptable
- **> 1.0s** : À optimiser

### Taux d'erreur
- **< 1%** : Excellent
- **1-5%** : Acceptable
- **5-10%** : Attention
- **> 10%** : Problématique

### Débit
- **> 10 req/s** : Excellent
- **5-10 req/s** : Bon
- **2-5 req/s** : Acceptable
- **< 2 req/s** : À optimiser

## 🔄 Évolutions possibles

1. **Tests de charge** : Augmenter à 10 000 éléments
2. **Tests de stress** : Tester les limites du système
3. **Tests de régression** : Comparer les performances dans le temps
4. **Monitoring continu** : Intégration avec des outils de monitoring
5. **Tests multi-utilisateurs** : Simulation de plusieurs utilisateurs simultanés

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs Django
2. Consulter la documentation de l'API
3. Tester l'API manuellement avec cURL
4. Vérifier la configuration de la base de données
