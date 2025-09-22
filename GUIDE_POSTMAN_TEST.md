# 🚀 Guide Postman - Test API CountingDetail

## 📋 Vue d'ensemble

Cette collection Postman vous permet de tester complètement votre API `counting-detail` avec tous les cas de test possibles, y compris les tests de performance pour 1000 lignes.

## 🔧 Installation et Configuration

### 1️⃣ **Importer la Collection**
1. Ouvrez **Postman**
2. Cliquez sur **Import**
3. Sélectionnez le fichier `Postman_CountingDetail_Collection.json`
4. Cliquez sur **Import**

### 2️⃣ **Configurer les Variables**
Avant de lancer les tests, configurez ces variables dans la collection :

| Variable | Valeur par défaut | Description |
|----------|------------------|-------------|
| `base_url` | `http://localhost:8000` | URL de votre serveur Django |
| `counting_id_vrac` | `1` | ID d'un comptage "en vrac" |
| `counting_id_article` | `2` | ID d'un comptage "par article" |
| `counting_id_stock` | `3` | ID d'un comptage "image de stock" |
| `location_id` | `1` | ID d'un emplacement valide |
| `product_id` | `1` | ID d'un produit valide |
| `assignment_id` | `1` | ID d'un assignment valide |

**Pour modifier les variables :**
1. Clic droit sur la collection → **Edit**
2. Onglet **Variables**
3. Modifiez les valeurs selon vos données

## 🧪 Tests Disponibles

### **1. Authentification** 🔑
- **Login JWT** : Récupère automatiquement le token d'authentification

### **2. Tests de Création** ✅
- **Test 1** : Mode "en vrac" sans produit
- **Test 2** : Mode "par article" avec produit obligatoire
- **Test 3** : Avec numéros de série
- **Test 4** : Cas complet avec toutes les propriétés

### **3. Tests de Validation** ⚠️
- Données manquantes (counting_id)
- Quantité négative
- Mode "par article" sans produit

### **4. Tests de Récupération** 📥
- Récupérer par comptage
- Récupérer par emplacement
- Récupérer par produit

### **5. Tests de Performance** 🚀
- Test de performance avec lot de 10 requêtes

## 🚀 Comment Utiliser

### **Méthode 1 : Tests Individuels**
1. **Lancez d'abord** "Login JWT" pour vous authentifier
2. **Exécutez** chaque test individuellement
3. **Vérifiez** les résultats dans l'onglet "Test Results"

### **Méthode 2 : Exécution Complète** ⭐ **RECOMMANDÉ**
1. Cliquez sur la collection "CountingDetail API - Test Complet"
2. Cliquez sur **"Run collection"**
3. **Configurez l'exécution** :
   - Iterations : `1` (pour test simple) ou `100` (pour test de performance)
   - Delay : `100ms` (entre les requêtes)
4. Cliquez sur **"Run CountingDetail API"**

### **Méthode 3 : Test de Performance (1000 lignes)**
1. Sélectionnez seulement les tests de création (Tests 1-4)
2. Configurez **Iterations : 250** (250 × 4 tests = 1000 requêtes)
3. **Delay : 50ms**
4. Lancez la collection

## 📊 Résultats Attendus

### **Tests de Création Réussis :**
```json
{
    "success": true,
    "data": {
        "counting_detail": {
            "id": 123,
            "reference": "CD-123-20241215-ABC123",
            "quantity_inventoried": 25,
            "product_id": 1,
            "location_id": 1,
            "counting_id": 1,
            "created_at": "2024-12-15T10:30:00Z"
        },
        "numeros_serie": [...],
        "message": "CountingDetail créé avec succès"
    }
}
```

### **Tests de Validation (Erreurs) :**
```json
{
    "success": false,
    "error": "Le produit est obligatoire pour le mode de comptage 'par article'",
    "error_type": "counting_mode_error"
}
```

## 📈 Analyse des Performances

### **Métriques à Surveiller :**
- **Temps de réponse** : < 500ms excellent, < 1s bon
- **Taux de succès** : > 95% excellent
- **Débit** : Nombre de requêtes/seconde

### **Dans Postman :**
1. Après l'exécution, consultez l'onglet **"Run Results"**
2. Vérifiez les **graphiques de performance**
3. Analysez les **temps de réponse moyens**

## 🔧 Configuration Avancée

### **Variables d'Environnement**
Créez un environnement Postman avec :
```json
{
    "base_url": "http://localhost:8000",
    "username": "admin",
    "password": "admin"
}
```

### **Scripts de Test Personnalisés**
Ajoutez dans l'onglet "Tests" de chaque requête :
```javascript
// Test personnalisé
pm.test("Custom validation", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.data.counting_detail.quantity_inventoried).to.be.above(0);
});

// Mesure de performance
pm.test("Response time under 1s", function () {
    pm.expect(pm.response.responseTime).to.be.below(1000);
});
```

## 🎯 Scénarios de Test Recommandés

### **Test Rapide (5 minutes)**
1. Authentification
2. Un test de chaque type (4 tests)
3. Un test de validation

### **Test Complet (15 minutes)**
1. Tous les tests individuels
2. Tests de performance (50 iterations)

### **Test de Charge (30 minutes)**
1. Tests de performance avec 1000 iterations
2. Analyse des métriques détaillées

## 🐛 Dépannage

### **Erreur 401 - Unauthorized**
- Vérifiez que l'authentification JWT fonctionne
- Le token est automatiquement ajouté aux requêtes

### **Erreur 400 - Bad Request**
- Vérifiez les IDs dans les variables de collection
- Assurez-vous que les données existent dans votre base

### **Erreur 500 - Internal Server Error**
- Vérifiez les logs Django
- Vérifiez que le serveur fonctionne

### **Variables Non Définies**
- Configurez toutes les variables de collection
- Vérifiez que les IDs correspondent à vos données

## 📊 Exemple de Rapport

Après 1000 requêtes, vous devriez voir :
```
✅ 987/1000 tests passed (98.7%)
⏱️ Average response time: 245ms
🚀 Peak performance: 4.2 requests/second
❌ 13 failures (mostly validation tests - expected)
```

## 💡 Conseils

1. **Commencez petit** : Testez d'abord avec 10 iterations
2. **Vérifiez vos données** : Assurez-vous que les IDs existent
3. **Surveillez le serveur** : Regardez les logs Django pendant les tests
4. **Sauvegardez vos résultats** : Exportez les rapports Postman

---

**Votre collection Postman est prête !** 🎉

**Importez le fichier JSON et commencez à tester votre API avec tous les cas possibles !**
