# Guide de Test - API CountingDetail

## 🚀 Comment tester votre API CountingDetail

J'ai créé plusieurs scripts de test pour vous aider à tester votre API `counting-detail` avec 1000 lignes ou plus. Voici comment les utiliser :

## 📋 Scripts disponibles

### 1. **`test_api_counting_detail_direct.py`** ⭐ **RECOMMANDÉ**
**Le plus simple à utiliser** - Test direct avec requests HTTP

```bash
# Démarrer votre serveur Django d'abord
python manage.py runserver

# Dans un autre terminal, lancer le test
python test_api_counting_detail_direct.py --count 50
```

### 2. **`test_counting_detail_simple.py`**
Test avec le framework Django (nécessite une configuration correcte)

```bash
python test_counting_detail_simple.py --count 20
```

### 3. **`test_counting_detail_1000_lines.py`**
Test complet avec création de toutes les données (plus complexe)

```bash
python test_counting_detail_1000_lines.py
```

## 🔧 Configuration requise

### Prérequis
1. **Serveur Django en cours d'exécution**
   ```bash
   python manage.py runserver
   ```

2. **Données existantes dans votre base** (ou le script les créera)
   - Au moins 1 comptage (Counting)
   - Au moins 1 emplacement (Location)
   - Au moins 1 assignment (Assigment)

3. **Authentification** (optionnelle)
   - Le script essaiera de s'authentifier avec `admin/admin`
   - Modifiez les identifiants dans le script si nécessaire

## 📊 Test rapide (5 minutes)

**Étape 1** : Démarrez votre serveur
```bash
python manage.py runserver
```

**Étape 2** : Dans un autre terminal, testez avec 10 éléments
```bash
python test_api_counting_detail_direct.py --count 10
```

**Résultat attendu** :
```
🚀 TEST COMPLET DE L'API COUNTING DETAIL
======================================================================
📅 Date: 2024-12-15 14:30:00
🎯 Objectif: Tester l'API avec 10 créations
🌐 URL de base: http://localhost:8000/mobile/api
======================================================================
✅ Serveur accessible
🔑 Tentative d'authentification...
✅ Authentification réussie
📦 Récupération des données existantes...
  • Comptages disponibles: [1, 2, 3]
  • Emplacements disponibles: [1, 2, 3, 4, 5]
  • Produits disponibles: [1, 2, 3, 4, 5]
  • Assignments disponibles: [1, 2, 3]

🧪 Test de création de 10 CountingDetail...
  ✅ CountingDetail 1: Créé en 0.234s
  ✅ CountingDetail 2: Créé en 0.187s
  ...

📊 RAPPORT DE TEST COMPLET
============================================================
🔧 CRÉATION (10 tests):
  • Succès: 8/10 (80.0%)
  • Temps moyen: 0.210s
  • Temps min/max: 0.156s / 0.345s

🎯 RÉSULTAT GLOBAL:
  • Tests totaux: 20
  • Succès: 16/20 (80.0%)
  ⚡ API fonctionne correctement avec quelques problèmes
```

## 🔍 Test avec 1000 lignes

**Pour le test de performance avec 1000 CountingDetail** :

```bash
python test_api_counting_detail_direct.py --count 1000
```

⚠️ **Attention** : Ce test peut prendre 5-15 minutes selon votre serveur.

## 🛠️ Personnalisation

### Modifier les données de test

Dans `test_api_counting_detail_direct.py`, ligne 45 :
```python
default_data = {
    'counting_ids': [1, 2, 3],        # ← Vos IDs de comptages
    'location_ids': [1, 2, 3, 4, 5],  # ← Vos IDs d'emplacements
    'product_ids': [1, 2, 3, 4, 5],   # ← Vos IDs de produits
    'assignment_ids': [1, 2, 3]       # ← Vos IDs d'assignments
}
```

### Modifier l'authentification

Ligne 25 :
```python
auth_data = {
    'username': 'votre_utilisateur',  # ← Votre nom d'utilisateur
    'password': 'votre_mot_de_passe'  # ← Votre mot de passe
}
```

### Changer l'URL du serveur

```bash
python test_api_counting_detail_direct.py --url http://votre-serveur:8000 --count 100
```

## 📈 Interprétation des résultats

### Temps de réponse
- **< 0.2s** : Excellent ✅
- **0.2-0.5s** : Bon ⚡
- **0.5-1.0s** : Acceptable ⚠️
- **> 1.0s** : À optimiser ❌

### Taux de succès
- **> 95%** : Excellent ✅
- **80-95%** : Bon ⚡
- **60-80%** : Acceptable ⚠️
- **< 60%** : Problématique ❌

## 🐛 Résolution des problèmes

### Erreur : "Serveur inaccessible"
```bash
# Vérifiez que Django fonctionne
python manage.py runserver

# Vérifiez l'URL
curl http://localhost:8000
```

### Erreur : "Authentification échouée"
1. Vérifiez vos identifiants dans le script
2. Ou désactivez l'authentification dans votre API temporairement

### Erreur : "counting_id n'existe pas"
1. Vérifiez vos données dans l'admin Django
2. Modifiez les IDs dans le script selon vos données

### Erreur : "Mode de comptage non supporté"
Vérifiez que vos comptages ont des modes valides : "en vrac", "par article", "image de stock"

## 📋 Vérification des données requises

**Avant de lancer le test**, vérifiez dans l'admin Django que vous avez :

1. **Au moins 1 Comptage** (`/admin/inventory/counting/`)
2. **Au moins 1 Emplacement** (`/admin/masterdata/location/`)
3. **Au moins 1 Assignment** (`/admin/inventory/assigment/`)
4. **Un utilisateur** pour l'authentification

## 🎯 Objectifs du test

- ✅ Vérifier que l'API accepte les requêtes POST
- ✅ Tester la validation des données
- ✅ Mesurer les performances (temps de réponse)
- ✅ Tester la récupération des données (GET)
- ✅ Identifier les goulots d'étranglement
- ✅ Vérifier la gestion d'erreurs

## 💡 Conseils

1. **Commencez petit** : Testez avec 5-10 éléments d'abord
2. **Vérifiez vos données** : Assurez-vous d'avoir des données valides
3. **Surveillez les logs** : Regardez les logs Django pendant le test
4. **Testez en production** : Les performances peuvent différer

## 📞 Support

Si vous rencontrez des problèmes :

1. **Vérifiez les logs Django** : `python manage.py runserver` affiche les erreurs
2. **Testez manuellement** : Utilisez Postman ou curl pour tester une requête
3. **Vérifiez la base de données** : Assurez-vous que les données existent
4. **Modifiez les IDs** : Adaptez les IDs dans le script selon vos données

---

**Bonne chance avec vos tests ! 🚀**
