# Architecture de mise à jour d'inventaire

## Vue d'ensemble

L'`InventoryUpdateView` a été modifiée pour respecter l'architecture en couches :

```
View → Serializer → Service → UseCase → Repository → Model
```

## Modifications apportées

### 1. Interface IInventoryService

**Fichier :** `apps/inventory/interfaces/inventory_interface.py`

```python
class IInventoryService(ABC):
    @abstractmethod
    def create_inventory(self, data: Dict[str, Any]) -> models.Model:
        """Crée un nouvel inventaire."""
        pass

    @abstractmethod
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> models.Model:
        """Met à jour un inventaire existant."""
        pass

    @abstractmethod
    def validate_inventory_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'un inventaire."""
        pass
```

### 2. Service InventoryService

**Fichier :** `apps/inventory/services/inventory_service.py`

```python
class InventoryService(IInventoryService):
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel inventaire en utilisant le use case."""
        try:
            from ..usecases.inventory_usecase import InventoryUseCase
            use_case = InventoryUseCase()
            result = use_case.create_inventory(data)
            
            # Ajouter le message spécifique à la création
            result['message'] = "Inventaire créé avec succès"
            return result
        except Exception as e:
            raise InventoryValidationError(f"Erreur lors de la création: {str(e)}")

    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un inventaire en utilisant le use case."""
        try:
            from ..usecases.inventory_usecase import InventoryUseCase
            use_case = InventoryUseCase()
            result = use_case.update_inventory(inventory_id, data)
            
            # Ajouter le message spécifique à la mise à jour
            result['message'] = "Inventaire mis à jour avec succès"
            return result
        except Exception as e:
            raise InventoryValidationError(f"Erreur lors de la mise à jour: {str(e)}")
```

### 3. Serializer InventoryDataSerializer

**Fichier :** `apps/inventory/serializers/inventory_serializer.py`

```python
class InventoryDataSerializer(serializers.Serializer):
    """
    Serializer pour les données d'inventaire (création et mise à jour).
    """
    label = serializers.CharField()
    date = serializers.DateField()
    account_id = serializers.IntegerField()
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate(self, data):
        """
        Valide les données de l'inventaire selon les règles métier.
        """
        # Validation des entrepôts
        for i, warehouse_info in enumerate(data['warehouse']):
            if not warehouse_info.get('id'):
                raise serializers.ValidationError(f"L'entrepôt {i+1} doit avoir un ID")
        
        # Validation des comptages
        comptages = data.get('comptages', [])
        
        # Vérifier qu'il y a exactement 3 comptages
        if len(comptages) != 3:
            raise serializers.ValidationError("Un inventaire doit contenir exactement 3 comptages")
        
        # Trier les comptages par ordre
        comptages_sorted = sorted(comptages, key=lambda x: x.get('order', 0))
        
        # Vérifier que les ordres sont 1, 2, 3
        orders = [c.get('order') for c in comptages_sorted]
        if orders != [1, 2, 3]:
            raise serializers.ValidationError("Les comptages doivent avoir les ordres 1, 2, 3")
        
        # Validation des champs obligatoires pour chaque comptage
        for i, comptage in enumerate(comptages_sorted, 1):
            if not comptage.get('order'):
                raise serializers.ValidationError(f"Le comptage {i} doit avoir un ordre")
            if not comptage.get('count_mode'):
                raise serializers.ValidationError(f"Le comptage {i} doit avoir un mode de comptage")
        
        # Récupérer les modes de comptage par ordre
        count_modes = [c.get('count_mode') for c in comptages_sorted]
        
        # Vérifier que tous les modes sont valides
        valid_modes = ['en vrac', 'par article', 'image stock']
        for i, mode in enumerate(count_modes):
            if mode not in valid_modes:
                raise serializers.ValidationError(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
        
        # Validation des combinaisons autorisées
        first_mode = count_modes[0]
        second_mode = count_modes[1]
        third_mode = count_modes[2]
        
        # Scénario 1: Premier comptage = "image stock"
        if first_mode == "image stock":
            # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
            if second_mode != third_mode:
                raise serializers.ValidationError("Si le premier comptage est 'image stock', les 2e et 3e comptages doivent avoir le même mode")
            
            if second_mode not in ["en vrac", "par article"]:
                raise serializers.ValidationError("Si le premier comptage est 'image stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
        
        # Scénario 2: Premier comptage = "en vrac" ou "par article"
        elif first_mode in ["en vrac", "par article"]:
            # Tous les comptages doivent être "en vrac" ou "par article"
            for i, mode in enumerate(count_modes):
                if mode not in ["en vrac", "par article"]:
                    raise serializers.ValidationError(f"Si le premier comptage n'est pas 'image stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")
        
        return data
```

### 4. Vue InventoryUpdateView

**Fichier :** `apps/inventory/views/inventory_views.py`

```python
class InventoryUpdateView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def put(self, request, pk, *args, **kwargs):
        """Met à jour un inventaire."""
        try:
            # 1. Validation du serializer
            serializer = InventoryDataSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Mise à jour via le service (qui utilise le use case)
            result = self.service.update_inventory(pk, serializer.validated_data)
            
            return Response({
                "message": result.get('message', "Inventaire mis à jour avec succès"),
                "data": result
            }, status=status.HTTP_200_OK)
            
        except InventoryValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except InventoryNotFoundError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
```

### 5. Vue InventoryCreateView

**Fichier :** `apps/inventory/views/inventory_views.py`

```python
class InventoryCreateView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, *args, **kwargs):
        """Crée un nouvel inventaire."""
        try:
            # 1. Validation du serializer
            serializer = InventoryDataSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Création via le service (qui utilise le use case)
            result = self.service.create_inventory(serializer.validated_data)
            
            return Response({
                "message": result.get('message', "Inventaire créé avec succès"),
                "data": result
            }, status=status.HTTP_201_CREATED)
            
        except InventoryValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

### 6. Vue InventoryListView

**Fichier :** `apps/inventory/views/inventory_views.py`

```python
class InventoryListView(APIView):
    """
    Vue pour lister les inventaires avec pagination et filtres.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def get(self, request, *args, **kwargs):
        """
        Récupère la liste des inventaires avec filtres, tri et pagination.
        
        Paramètres de requête supportés :
        - Filtres : reference, label, status, date_gte, date_lte, etc.
        - Tri : ordering (ex: -date, label, status)
        - Pagination : page, page_size
        - Recherche : search (recherche dans label et reference)
        """
        try:
            # Récupérer les paramètres de requête
            filters_dict = request.query_params.dict()
            
            # Extraire les paramètres de pagination et tri
            page = int(filters_dict.pop('page', 1))
            page_size = int(filters_dict.pop('page_size', 10))
            ordering = filters_dict.pop('ordering', '-date')
            search = filters_dict.pop('search', None)
            
            # Ajouter la recherche aux filtres si fournie
            if search:
                filters_dict['label__icontains'] = search
                filters_dict['reference__icontains'] = search
            
            # Récupérer la liste via le service
            result = self.service.get_inventory_list(
                filters_dict=filters_dict,
                ordering=ordering,
                page=page,
                page_size=page_size
            )
            
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                "success": False,
                "message": "Paramètres de requête invalides"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 7. Filtres améliorés

**Fichier :** `apps/inventory/filters/inventory_filters.py`

```python
class InventoryFilter(filters.FilterSet):
    """
    Filtres pour l'inventaire - Tous les champs disponibles
    """
    # Filtres de base
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    label = filters.CharFilter(field_name='label', lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=Inventory.STATUS_CHOICES)
    
    # Filtres de date
    date_gte = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    date_exact = filters.DateTimeFilter(field_name='date', lookup_expr='exact')
    
    # Filtres de dates de statut
    en_preparation_status_date_gte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='gte')
    en_preparation_status_date_lte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='lte')
    
    # Filtres pour les relations (account et warehouse)
    account_name = filters.CharFilter(field_name='awi_links__account__account_name', lookup_expr='icontains')
    account_id = filters.NumberFilter(field_name='awi_links__account__id', lookup_expr='exact')
    warehouse_name = filters.CharFilter(field_name='awi_links__warehouse__warehouse_name', lookup_expr='icontains')
    warehouse_id = filters.NumberFilter(field_name='awi_links__warehouse__id', lookup_expr='exact')
    
    # Filtres pour les comptages
    count_mode = filters.CharFilter(field_name='countings__count_mode', lookup_expr='icontains')
    count_mode_exact = filters.CharFilter(field_name='countings__count_mode', lookup_expr='exact')
    counting_order = filters.NumberFilter(field_name='countings__order', lookup_expr='exact')
    
    # Filtres pour les champs de création/modification
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Filtres pour les champs booléens des comptages
    unit_scanned = filters.BooleanFilter(field_name='countings__unit_scanned', lookup_expr='exact')
    entry_quantity = filters.BooleanFilter(field_name='countings__entry_quantity', lookup_expr='exact')
    is_variant = filters.BooleanFilter(field_name='countings__is_variant', lookup_expr='exact')
    n_lot = filters.BooleanFilter(field_name='countings__n_lot', lookup_expr='exact')
    n_serie = filters.BooleanFilter(field_name='countings__n_serie', lookup_expr='exact')
    dlc = filters.BooleanFilter(field_name='countings__dlc', lookup_expr='exact')
    show_product = filters.BooleanFilter(field_name='countings__show_product', lookup_expr='exact')
    stock_situation = filters.BooleanFilter(field_name='countings__stock_situation', lookup_expr='exact')
    quantity_show = filters.BooleanFilter(field_name='countings__quantity_show', lookup_expr='exact')

    class Meta:
        model = Inventory
        fields = {
            'reference': ['exact', 'icontains'],
            'label': ['exact', 'icontains'],
            'status': ['exact'],
            'date': ['exact', 'gte', 'lte'],
            'en_preparation_status_date': ['exact', 'gte', 'lte'],
            'en_realisation_status_date': ['exact', 'gte', 'lte'],
            'ternime_status_date': ['exact', 'gte', 'lte'],
            'cloture_status_date': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
        }
```

## Champs de filtrage disponibles

### Champs de base
- `reference` : Référence de l'inventaire (icontains, exact)
- `label` : Label de l'inventaire (icontains, exact)
- `status` : Statut de l'inventaire (exact)
- `date` : Date de l'inventaire (exact, gte, lte)

### Dates de statut
- `en_preparation_status_date` : Date de préparation (exact, gte, lte)
- `en_realisation_status_date` : Date de réalisation (exact, gte, lte)
- `ternime_status_date` : Date de terminaison (exact, gte, lte)
- `cloture_status_date` : Date de clôture (exact, gte, lte)

### Relations
- `account_name` : Nom du compte (icontains)
- `account_id` : ID du compte (exact)
- `warehouse_name` : Nom de l'entrepôt (icontains)
- `warehouse_id` : ID de l'entrepôt (exact)

### Comptages
- `count_mode` : Mode de comptage (icontains, exact)
- `counting_order` : Ordre du comptage (exact)

### Champs booléens des comptages
- `unit_scanned` : Unité scannée (exact)
- `entry_quantity` : Saisie de quantité (exact)
- `is_variant` : Est une variante (exact)
- `n_lot` : N° lot (exact)
- `n_serie` : N° série (exact)
- `dlc` : DLC (exact)
- `show_product` : Afficher le produit (exact)
- `stock_situation` : Situation de stock (exact)
- `quantity_show` : Afficher la quantité (exact)

### Champs de création/modification
- `created_at` : Date de création (exact, gte, lte)
- `updated_at` : Date de modification (exact, gte, lte)

## Homogénéisation des serializers

### Serializer unifié

- **Ancien nom** : `InventoryCreateSerializer`
- **Nouveau nom** : `InventoryDataSerializer`
- **Usage** : Création et mise à jour d'inventaire

### Avantages de l'homogénéisation

1. **Cohérence** : Un seul serializer pour les deux opérations
2. **Maintenance** : Une seule validation à maintenir
3. **Réutilisabilité** : Le même serializer peut être utilisé partout
4. **Clarté** : Le nom reflète mieux l'usage (données d'inventaire)

## Séparation des messages

### Messages spécifiques par opération

- **Création** : `"Inventaire créé avec succès"`
- **Mise à jour** : `"Inventaire mis à jour avec succès"`

### Gestion des messages

1. **UseCase** : Ne définit pas de message, retourne seulement les données
2. **Service** : Ajoute le message spécifique selon l'opération
3. **View** : Utilise le message du service avec fallback

## Flux de données

### Mise à jour d'inventaire

1. **View (InventoryUpdateView)**
   - Reçoit la requête HTTP PUT
   - Valide les données avec le serializer
   - Appelle le service

2. **Serializer (InventoryDataSerializer)**
   - Valide le format des données
   - Retourne les données validées

3. **Service (InventoryService)**
   - Implémente l'interface IInventoryService
   - Appelle le use case pour la logique métier
   - Ajoute le message spécifique à la mise à jour
   - Gère les exceptions

4. **UseCase (InventoryUseCase)**
   - Implémente l'interface IInventoryUseCase
   - Contient la logique métier unifiée (création/mise à jour)
   - Valide les règles métier
   - Appelle le repository
   - Retourne les données sans message

5. **Repository (InventoryRepository)**
   - Implémente l'interface IInventoryRepository
   - Gère l'accès aux données
   - Effectue les opérations CRUD

6. **Model (Inventory)**
   - Définit la structure des données
   - Contient les contraintes de base de données

## Avantages de cette architecture

1. **Séparation des responsabilités** : Chaque couche a un rôle spécifique
2. **Testabilité** : Chaque couche peut être testée indépendamment
3. **Maintenabilité** : Modifications isolées par couche
4. **Réutilisabilité** : Services et use cases réutilisables
5. **Interface contractuelle** : Interfaces définissent les contrats
6. **Inversion de dépendance** : Dépendances vers les abstractions
7. **Messages spécifiques** : Messages adaptés à chaque opération
8. **Serializer unifié** : Cohérence entre création et mise à jour

## Tests

Des tests ont été ajoutés pour vérifier :

- L'implémentation des interfaces
- L'utilisation correcte des couches
- Le flux de données entre les couches
- La gestion des erreurs
- **La séparation des messages** de création et mise à jour
- **L'utilisation du serializer unifié**

## Utilisation

### Création d'inventaire
```python
POST /api/inventory/create/
{
    "label": "Nouvel inventaire",
    "date": "2024-01-15",
    "account_id": 1,
    "warehouse": [{"id": 1}],
    "comptages": [...]
}

# Réponse
{
    "message": "Inventaire créé avec succès",
    "data": {...}
}
```

### Mise à jour d'inventaire
```python
PUT /api/inventory/123/update/
{
    "label": "Inventaire mis à jour",
    "date": "2024-01-15",
    "account_id": 1,
    "warehouse": [{"id": 1}],
    "comptages": [...]
}

# Réponse
{
    "message": "Inventaire mis à jour avec succès",
    "data": {...}
}
```

### Liste des inventaires

#### Filtrage de base
```python
GET /api/inventory/list/?status=EN_PREPARATION&label__icontains=Inventaire

# Réponse
{
    "success": true,
    "message": "Liste des inventaires récupérée avec succès",
    "data": [...],
    "pagination": {
        "count": 10,
        "num_pages": 1,
        "current_page": 1,
        "has_next": false,
        "has_previous": false
    }
}
```

#### Filtrage par date
```python
GET /api/inventory/list/?date_gte=2024-01-01&date_lte=2024-12-31

# Filtre les inventaires entre le 1er janvier et le 31 décembre 2024
```

#### Filtrage par relations
```python
GET /api/inventory/list/?account_name__icontains=Compte&warehouse_id=1

# Filtre par nom de compte contenant "Compte" et ID d'entrepôt = 1
```

#### Filtrage par comptages
```python
GET /api/inventory/list/?count_mode=en_vrac&unit_scanned=true

# Filtre les inventaires avec comptage "en vrac" et unité scannée activée
```

#### Tri et pagination
```python
GET /api/inventory/list/?ordering=-date&page=2&page_size=5

# Trie par date décroissante, page 2, 5 éléments par page
```

#### Recherche globale
```python
GET /api/inventory/list/?search=Inventaire2024

# Recherche dans label et reference contenant "Inventaire2024"
```

#### Combinaison de filtres
```python
GET /api/inventory/list/?status=EN_PREPARATION&date_gte=2024-01-01&account_name__icontains=Compte&ordering=-created_at&page=1&page_size=10

# Combinaison de plusieurs filtres avec tri et pagination
```

## Structure des serializers

```python
# Serializers disponibles
InventoryDataSerializer      # Création et mise à jour
InventoryDetailSerializer    # Détails d'un inventaire
InventoryGetByIdSerializer   # Récupération par ID
InventoryTeamSerializer      # Équipe d'un inventaire
```

Cette architecture respecte les principes SOLID et facilite l'évolution du code. 