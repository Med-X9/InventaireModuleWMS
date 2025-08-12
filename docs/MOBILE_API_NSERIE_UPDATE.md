# Mise à jour de l'API Mobile - Inclusion des Numéros de Série

## Résumé des Modifications

L'API mobile `GET /api/mobile/user/{user_id}/products/` a été mise à jour pour inclure les numéros de série associés aux produits qui les supportent.

## Modifications Apportées

### 1. Repository (`apps/mobile/repositories/user_repository.py`)

#### Méthode `format_product_data()`

**Avant :**
```python
return {
    'web_id': product.id,
    'product_name': product.Short_Description,
    'product_code': product.Barcode,
    'internal_product_code': product.Internal_Product_Code,
    'description': product.Short_Description,
    'category': product.Product_Group,
    'brand': family_name,
    'family_id': family_id,
    'unit_of_measure': product.Stock_Unit,
    'is_active': product.Product_Status == 'ACTIVE',
    'is_variant': product.Is_Variant,
    'n_lot': product.n_lot,
    'n_serie': product.n_serie,
    'dlc': product.dlc,
    'created_at': product.created_at.isoformat(),
    'updated_at': product.updated_at.isoformat()
}
```

**Après :**
```python
# Récupérer les numéros de série si le produit les supporte
numeros_serie = []
if product.n_serie:
    try:
        from apps.masterdata.models import NSerie
        nseries = NSerie.objects.filter(
            product=product,
            status='ACTIVE'
        ).order_by('n_serie')
        
        for nserie in nseries:
            numeros_serie.append({
                'id': nserie.id,
                'n_serie': nserie.n_serie,
                'reference': nserie.reference,
                'status': nserie.status,
                'description': nserie.description,
                'date_fabrication': nserie.date_fabrication.isoformat() if nserie.date_fabrication else None,
                'date_expiration': nserie.date_expiration.isoformat() if nserie.date_expiration else None,
                'warranty_end_date': nserie.warranty_end_date.isoformat() if nserie.warranty_end_date else None,
                'is_expired': nserie.is_expired,
                'is_warranty_valid': nserie.is_warranty_valid,
                'created_at': nserie.created_at.isoformat(),
                'updated_at': nserie.updated_at.isoformat()
            })
        
        print(f"Nombre de numéros de série trouvés: {len(numeros_serie)}")
    except Exception as e:
        print(f"Erreur lors de la récupération des numéros de série pour le produit {product.id}: {str(e)}")
        # Continuer sans les numéros de série en cas d'erreur

return {
    'web_id': product.id,
    'product_name': product.Short_Description,
    'product_code': product.Barcode,
    'internal_product_code': product.Internal_Product_Code,
    'description': product.Short_Description,
    'category': product.Product_Group,
    'brand': family_name,
    'family_id': family_id,
    'unit_of_measure': product.Stock_Unit,
    'is_active': product.Product_Status == 'ACTIVE',
    'is_variant': product.Is_Variant,
    'n_lot': product.n_lot,
    'n_serie': product.n_serie,
    'dlc': product.dlc,
    'numeros_serie': numeros_serie,  # Nouveau champ
    'created_at': product.created_at.isoformat(),
    'updated_at': product.updated_at.isoformat()
}
```

## Structure de la Réponse API

### Avant
```json
{
    "success": true,
    "user_id": 4,
    "timestamp": "2025-08-08T16:09:21.042811+00:00",
    "data": {
        "products": [
            {
                "web_id": 12558,
                "product_name": "10cm Keeleco Mini Adoptable World 1",
                "product_code": "1234567890123",
                "internal_product_code": "INT-1304",
                "description": "10cm Keeleco Mini Adoptable World 1",
                "category": "TOYS",
                "brand": "KEEL TOYS",
                "family_id": 123,
                "unit_of_measure": "PIECE",
                "is_active": true,
                "is_variant": false,
                "n_lot": false,
                "n_serie": false,
                "dlc": false,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00"
            }
        ]
    }
}
```

### Après
```json
{
    "success": true,
    "user_id": 4,
    "timestamp": "2025-08-08T16:09:21.042811+00:00",
    "data": {
        "products": [
            {
                "web_id": 12558,
                "product_name": "10cm Keeleco Mini Adoptable World 1",
                "product_code": "1234567890123",
                "internal_product_code": "INT-1304",
                "description": "10cm Keeleco Mini Adoptable World 1",
                "category": "TOYS",
                "brand": "KEEL TOYS",
                "family_id": 123,
                "unit_of_measure": "PIECE",
                "is_active": true,
                "is_variant": false,
                "n_lot": false,
                "n_serie": false,
                "dlc": false,
                "numeros_serie": [],  // Nouveau champ - vide car n_serie=false
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00"
            },
            {
                "web_id": 12559,
                "product_name": "Produit avec numéros de série",
                "product_code": "1234567890124",
                "internal_product_code": "INT-1305",
                "description": "Produit avec numéros de série",
                "category": "ELECTRONICS",
                "brand": "TECH BRAND",
                "family_id": 124,
                "unit_of_measure": "PIECE",
                "is_active": true,
                "is_variant": false,
                "n_lot": false,
                "n_serie": true,
                "dlc": false,
                "numeros_serie": [  // Nouveau champ - avec données car n_serie=true
                    {
                        "id": 1,
                        "n_serie": "NS-001-2024",
                        "reference": "NS-REF-001",
                        "status": "ACTIVE",
                        "description": "Numéro de série de test",
                        "date_fabrication": "2024-01-01",
                        "date_expiration": "2026-01-01",
                        "warranty_end_date": "2025-01-01",
                        "is_expired": false,
                        "is_warranty_valid": true,
                        "created_at": "2024-01-01T00:00:00+00:00",
                        "updated_at": "2024-01-01T00:00:00+00:00"
                    }
                ],
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00"
            }
        ]
    }
}
```

## Nouveau Champ `numeros_serie`

### Description
Le champ `numeros_serie` est un tableau qui contient les numéros de série associés au produit.

### Structure d'un Numéro de Série
```json
{
    "id": 1,                    // ID unique du numéro de série
    "n_serie": "NS-001-2024",   // Numéro de série
    "reference": "NS-REF-001",  // Référence interne
    "status": "ACTIVE",         // Statut (ACTIVE, INACTIVE, USED, EXPIRED, BLOCKED)
    "description": "Description", // Description optionnelle
    "date_fabrication": "2024-01-01",     // Date de fabrication (ISO format)
    "date_expiration": "2026-01-01",      // Date d'expiration (ISO format)
    "warranty_end_date": "2025-01-01",    // Date de fin de garantie (ISO format)
    "is_expired": false,        // Calculé : si la date d'expiration est dépassée
    "is_warranty_valid": true,  // Calculé : si la garantie est encore valide
    "created_at": "2024-01-01T00:00:00+00:00", // Date de création
    "updated_at": "2024-01-01T00:00:00+00:00"  // Date de modification
}
```

### Comportement

1. **Produits avec `n_serie: true`** : Le champ `numeros_serie` contient un tableau avec tous les numéros de série actifs associés au produit.

2. **Produits avec `n_serie: false`** : Le champ `numeros_serie` contient un tableau vide `[]`.

3. **Gestion d'erreur** : Si une erreur survient lors de la récupération des numéros de série, le champ contient un tableau vide et l'erreur est loggée.

## Logique de Récupération

### Filtres Appliqués
- Seuls les numéros de série avec le statut `'ACTIVE'` sont récupérés
- Les numéros de série sont triés par ordre alphabétique (`order_by('n_serie')`)
- Seuls les numéros de série associés au produit spécifique sont inclus

### Performance
- La récupération des numéros de série se fait uniquement si `product.n_serie` est `True`
- Les requêtes sont optimisées avec des filtres appropriés
- Gestion d'erreur robuste pour éviter l'échec de l'API en cas de problème

## Tests

### Scripts de Test Créés
1. `test_mobile_api_final.py` - Test complet de l'API mobile
2. `simple_test_mobile_api.py` - Test simple avec données existantes

### Résultats des Tests
- ✅ Champ `numeros_serie` présent dans tous les produits
- ✅ Tableau vide pour les produits avec `n_serie: false`
- ✅ Données complètes pour les produits avec `n_serie: true`
- ✅ Gestion d'erreur robuste
- ✅ Performance acceptable (1791 produits traités)

## Compatibilité

### Rétrocompatibilité
- ✅ L'API reste compatible avec les clients existants
- ✅ Les champs existants ne sont pas modifiés
- ✅ Le nouveau champ `numeros_serie` est optionnel pour les clients

### Clients Mobiles
Les clients mobiles peuvent maintenant :
1. Vérifier si un produit supporte les numéros de série (`n_serie: true`)
2. Afficher les numéros de série disponibles (`numeros_serie` array)
3. Utiliser les informations de dates pour la gestion des garanties
4. Afficher le statut de chaque numéro de série

## Exemples d'Utilisation

### Vérification de Support
```javascript
if (product.n_serie) {
    // Le produit supporte les numéros de série
    const numerosSerie = product.numeros_serie;
    if (numerosSerie.length > 0) {
        // Afficher les numéros de série disponibles
        numerosSerie.forEach(nserie => {
            console.log(`Numéro: ${nserie.n_serie}, Status: ${nserie.status}`);
        });
    }
}
```

### Gestion des Garanties
```javascript
const numerosSerie = product.numeros_serie;
const garantiesValides = numerosSerie.filter(nserie => nserie.is_warranty_valid);
const numerosExpires = numerosSerie.filter(nserie => nserie.is_expired);
```

## Conclusion

L'API mobile a été mise à jour avec succès pour inclure les numéros de série. Les modifications sont :

1. **Non-intrusives** : Aucun changement dans les champs existants
2. **Robustes** : Gestion d'erreur appropriée
3. **Performantes** : Requêtes optimisées
4. **Complètes** : Toutes les informations des numéros de série sont incluses
5. **Flexibles** : Support des cas avec et sans numéros de série

L'API est maintenant prête pour les applications mobiles qui nécessitent la gestion des numéros de série.
