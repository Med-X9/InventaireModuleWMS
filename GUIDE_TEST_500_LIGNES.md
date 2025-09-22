# Guide de Test - API CountingDetail Mobile avec 500 Lignes

## 📋 Vue d'ensemble

Ce guide vous explique comment tester l'API CountingDetail mobile avec 500 lignes de données en utilisant Postman et des scripts Python.

## 🗂️ Fichiers Créés

### 1. Données de Test
- **`test_data_500_lines.json`** : Fichier JSON contenant 500 enregistrements de test

### 2. Collection Postman
- **`Postman_CountingDetail_Mobile_Collection.json`** : Collection complète pour tester l'API

### 3. Scripts de Test
- **`check_database_for_test.py`** : Script pour vérifier la base de données et générer les données de test
- **`test_500_lines_performance.py`** : Script de test de performance pour 500 lignes

### 4. Documentation
- **`GUIDE_TEST_500_LIGNES.md`** : Ce guide d'utilisation

## 🚀 Étapes de Test

### Étape 1: Vérification de la Base de Données

Exécutez le script pour vérifier votre base de données :

```bash
python check_database_for_test.py
```

**Résultats attendus :**
- ✅ 27 comptages disponibles
- ✅ 347 emplacements disponibles  
- ✅ 1790 produits disponibles
- ✅ 7 assignments disponibles
- ✅ 7 utilisateurs disponibles
- ✅ Fichier `test_data_500_lines.json` créé

### Étape 2: Test avec Postman

#### 2.1 Import de la Collection

1. Ouvrez Postman
2. Cliquez sur "Import"
3. Sélectionnez le fichier `Postman_CountingDetail_Mobile_Collection.json`
4. La collection "API CountingDetail Mobile - Test 500 Lignes" sera importée

#### 2.2 Configuration

1. **Variables de Collection :**
   - `base_url` : `http://localhost:8000/mobile/api`
   - `access_token` : (sera automatiquement rempli après login)

2. **Authentification :**
   - La collection utilise l'authentification Bearer Token
   - Le token sera automatiquement récupéré après le login

#### 2.3 Tests à Exécuter

##### Test 1: Login JWT
- **Endpoint :** `POST /auth/jwt-login/`
- **Objectif :** Récupérer le token JWT
- **Résultat attendu :** Status 200, token récupéré automatiquement

##### Test 2: Validation en lot - 5 lignes
- **Endpoint :** `PUT /counting-detail/`
- **Objectif :** Valider 5 enregistrements
- **Résultat attendu :** Status 200, 5 enregistrements validés

##### Test 3: Création en lot - 5 lignes
- **Endpoint :** `POST /counting-detail/`
- **Objectif :** Créer 5 enregistrements
- **Résultat attendu :** Status 201, 5 enregistrements créés

##### Test 4: Création d'un seul enregistrement
- **Endpoint :** `POST /counting-detail/`
- **Objectif :** Créer 1 enregistrement
- **Résultat attendu :** Status 201, 1 enregistrement créé

##### Test 5: Validation en lot - 500 lignes
- **Endpoint :** `PUT /counting-detail/`
- **Objectif :** Valider 500 enregistrements (test de performance)
- **Résultat attendu :** Status 200, 500 enregistrements validés
- **Temps attendu :** < 10 secondes

##### Test 6: Création en lot - 500 lignes
- **Endpoint :** `POST /counting-detail/`
- **Objectif :** Créer 500 enregistrements (test de performance)
- **Résultat attendu :** Status 201, 500 enregistrements créés
- **Temps attendu :** < 30 secondes

##### Test 7: Consultation des données
- **Endpoint :** `GET /counting-detail/?counting_id=2`
- **Objectif :** Récupérer les CountingDetail d'un comptage
- **Résultat attendu :** Status 200, liste des CountingDetail

### Étape 3: Test avec Script Python

Exécutez le script de test de performance :

```bash
python test_500_lines_performance.py
```

**Résultats attendus :**
- ✅ Connexion réussie
- ✅ Chargement des 500 enregistrements
- ✅ Validation 500 lignes : < 10 secondes
- ✅ Création 500 lignes : < 30 secondes
- ✅ Mise à jour 10 lignes : < 5 secondes
- ✅ Rapport de performance généré

## 📊 Métriques de Performance

### Objectifs de Performance

| Test | Temps Maximum | Vitesse Minimum |
|------|---------------|-----------------|
| Validation 500 lignes | 10 secondes | 50 enregistrements/s |
| Création 500 lignes | 30 secondes | 17 enregistrements/s |
| Mise à jour 10 lignes | 5 secondes | 2 enregistrements/s |

### Exemple de Résultats Attendus

```
📊 RAPPORT DE PERFORMANCE
==================================================
Tests exécutés: 3
Tests réussis: 3
Taux de réussite: 100.0%

📋 Validation 500 lignes:
   - Temps: 8.45s
   - Vitesse: 59.17 enregistrements/s
   - Valides: 500
   - Invalides: 0

📝 Création 500 lignes:
   - Temps: 25.32s
   - Vitesse: 19.75 enregistrements/s
   - Réussis: 500
   - Échecs: 0
   - Actions: {'created': 500}

🔄 Mise à jour 10 lignes:
   - Temps: 2.15s
   - Vitesse: 4.65 enregistrements/s
   - Réussis: 10
   - Échecs: 0
   - Actions: {'updated': 10}
```

## 🔧 Configuration Requise

### Prérequis
- ✅ Serveur Django en cours d'exécution sur `http://localhost:8000`
- ✅ Base de données avec des enregistrements de test
- ✅ Utilisateur `testuser_api` avec mot de passe `testpass123`

### Vérification du Serveur

```bash
# Vérifier que le serveur fonctionne
curl http://localhost:8000/mobile/api/auth/jwt-login/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser_api", "password": "testpass123"}'
```

## 📝 Structure des Données de Test

### Exemple d'Enregistrement

```json
{
  "counting_id": 2,
  "location_id": 3596,
  "quantity_inventoried": 1,
  "assignment_id": 52,
  "product_id": 11329,
  "dlc": "2024-12-31",
  "n_lot": "LOT000000",
  "numeros_serie": [
    {
      "n_serie": "NS000000A"
    },
    {
      "n_serie": "NS000000B"
    }
  ]
}
```

### Distribution des Données

- **500 enregistrements** avec des combinaisons différentes
- **Quantités** : Entre 1 et 50 unités
- **DLC** : 1/3 des enregistrements
- **Numéros de lot** : 1/4 des enregistrements
- **Numéros de série** : 1/5 des enregistrements

## 🚨 Dépannage

### Erreurs Courantes

#### 1. Erreur de Connexion
```
❌ Erreur de connexion: HTTPConnectionPool(host='localhost', port=8000)
```
**Solution :** Vérifiez que le serveur Django est démarré :
```bash
python manage.py runserver 8000
```

#### 2. Erreur d'Authentification
```
❌ Erreur de connexion: 'No active account found with the given credentials'
```
**Solution :** Vérifiez que l'utilisateur `testuser_api` existe :
```bash
python create_test_user.py
```

#### 3. Erreur de Fichier
```
❌ Fichier test_data_500_lines.json non trouvé
```
**Solution :** Exécutez d'abord le script de génération :
```bash
python check_database_for_test.py
```

#### 4. Erreurs de Validation
```
❌ Emplacement avec l'ID X non trouvé
```
**Solution :** Normal si les IDs n'existent pas dans votre base de données. Les tests continueront avec les erreurs gérées.

### Logs de Debug

Pour activer les logs détaillés dans Django, ajoutez dans `settings.py` :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.mobile': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 📈 Optimisations

### Pour Améliorer les Performances

1. **Base de Données :**
   - Index sur les champs de recherche
   - Optimisation des requêtes

2. **API :**
   - Mise en cache des objets liés
   - Traitement asynchrone pour de gros volumes

3. **Tests :**
   - Utilisation de données mockées
   - Tests unitaires pour les composants individuels

## ✅ Checklist de Validation

- [ ] Serveur Django démarré
- [ ] Utilisateur de test créé
- [ ] Données de test générées (500 lignes)
- [ ] Collection Postman importée
- [ ] Tests Postman exécutés avec succès
- [ ] Script Python exécuté avec succès
- [ ] Rapport de performance généré
- [ ] Métriques de performance conformes

## 🎯 Résultats Attendus

Après avoir suivi ce guide, vous devriez avoir :

1. ✅ **API fonctionnelle** avec support des lots
2. ✅ **Tests automatisés** pour 500 lignes
3. ✅ **Collection Postman** prête pour les tests manuels
4. ✅ **Rapport de performance** détaillé
5. ✅ **Validation** que l'API est prête pour la production

**L'API CountingDetail mobile est maintenant testée et validée pour la production ! 🚀**
