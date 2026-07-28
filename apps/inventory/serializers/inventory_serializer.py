"""
Serializers pour l'application inventory.
"""
from rest_framework import serializers
from ..models import Inventory, Counting, Setting, Assigment
from ..services.inventory_service import InventoryService
from ..exceptions import InventoryValidationError
from apps.masterdata.models import Account, Warehouse
from .counting_serializer import CountingCreateSerializer, CountingDetailSerializer, CountingSerializer, CountingModeFieldsSerializer
from apps.users.serializers import UserAppSerializer
from apps.masterdata.serializers.warehouse_serializer import WarehouseSerializer
from .inventory_prefetch import (
    get_first_inventory_setting,
    get_inventory_assignments,
    get_inventory_countings,
    get_inventory_settings,
)
from ..constants import CountMode, InventoryType


class InventoryCreateSerializer(serializers.Serializer):
    """
    Création inventaire (tous types) : sans comptages.
    Les comptages se configurent via POST /inventory/<id>/countings/.
    """
    label = serializers.CharField()
    date = serializers.DateField()
    account_id = serializers.IntegerField()
    inventory_type = serializers.ChoiceField(
        choices=[(t, t) for t in InventoryType.ALL],
        default=InventoryType.GENERAL,
    )
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    # Ignoré / refusé à la création (configuration séparée)
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )

    def validate(self, data):
        """Création minimale : label, type, date, compte, magasin(+date). Pas de comptages."""
        inventory_type = data.get('inventory_type', InventoryType.GENERAL)

        for i, warehouse_info in enumerate(data['warehouse']):
            if not warehouse_info.get('id'):
                raise serializers.ValidationError(f"L'entrepôt {i+1} doit avoir un ID")
            if not warehouse_info.get('date'):
                raise serializers.ValidationError(
                    f"L'entrepôt {i+1} doit avoir une date (date magasin)"
                )

        if data.get('comptages'):
            raise serializers.ValidationError(
                f"Pour un inventaire {inventory_type}, les comptages se configurent après la création "
                "(POST /inventory/<id>/countings/)."
            )
        data['comptages'] = []
        return data


class InventoryDuplicateSerializer(serializers.Serializer):
    """
    Serializer pour la duplication d'un inventaire.
    """
    label = serializers.CharField()
    date = serializers.DateField()
    inventory_type = serializers.ChoiceField(
        choices=[(t, t) for t in InventoryType.ALL],
        default=InventoryType.GENERAL
    )
    account_id = serializers.IntegerField()
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_warehouse(self, warehouses):
        """
        Valide la liste des entrepôts fournie.
        """
        if not warehouses:
            raise serializers.ValidationError("Au moins un entrepôt est obligatoire")

        for index, warehouse_info in enumerate(warehouses, start=1):
            if not isinstance(warehouse_info, dict):
                raise serializers.ValidationError(f"L'entrepôt {index} doit être un objet avec un identifiant")
            if not warehouse_info.get('id'):
                raise serializers.ValidationError(f"L'entrepôt {index} doit avoir un identifiant 'id'")

        return warehouses

class InventoryGetByIdSerializer(serializers.ModelSerializer):
    """Serializer pour récupérer un inventaire par son ID avec le format spécifique."""
    account_reference = serializers.SerializerMethodField()
    warehouse_references = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = ['reference', 'label', 'date', 'account_reference', 'warehouse_references', 'comptages']

    def get_account_reference(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.reference if setting and hasattr(setting.account, 'reference') else None

    def get_warehouse_references(self, obj):
        settings = get_inventory_settings(obj)
        return [setting.warehouse.reference for setting in settings if hasattr(setting.warehouse, 'reference')]

    def get_comptages(self, obj):
        countings = get_inventory_countings(obj)
        return CountingDetailSerializer(countings, many=True).data

class PdaTeamSerializer(serializers.ModelSerializer):
    """Serializer pour les membres de l'équipe PDA"""
    user = UserAppSerializer(source='session', read_only=True)

    class Meta:
        model = Assigment
        fields = ['reference', 'user']

class InventoryDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les détails d'un inventaire.
    """
    account_name = serializers.SerializerMethodField()
    account_reference = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    warehouse_references = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id','reference', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date',
            'en_realisation_status_date', 'termine_status_date',
            'cloture_status_date', 'account_name', 'account_reference', 
            'warehouse_name', 'warehouse_references', 'created_at',
            'comptages', 'equipe'
        ]

    def get_account_name(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.account_name if setting else None

    def get_account_reference(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.reference if setting and hasattr(setting.account, 'reference') else None

    def get_warehouse_name(self, obj):
        settings = get_inventory_settings(obj)
        return [setting.warehouse.warehouse_name for setting in settings]

    def get_warehouse_references(self, obj):
        settings = get_inventory_settings(obj)
        return [setting.warehouse.reference for setting in settings if hasattr(setting.warehouse, 'reference')]

    def get_comptages(self, obj):
        countings = get_inventory_countings(obj)
        return CountingDetailSerializer(countings, many=True).data

    def get_equipe(self, obj):
        pdas = get_inventory_assignments(obj)
        return PdaTeamSerializer(pdas, many=True).data


class InventorySerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()
    account_reference = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    warehouse_references = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'reference', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date', 'en_realisation_status_date',
            'termine_status_date', 'cloture_status_date',
            'account_name', 'account_reference', 'warehouse_name', 
            'warehouse_references', 'comptages', 'equipe'
        ]

    def get_account_name(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.account_name if setting else None

    def get_account_reference(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.reference if setting and hasattr(setting.account, 'reference') else None

    def get_warehouse_name(self, obj):
        settings = get_inventory_settings(obj)
        return [setting.warehouse.warehouse_name for setting in settings]

    def get_warehouse_references(self, obj):
        settings = get_inventory_settings(obj)
        return [setting.warehouse.reference for setting in settings if hasattr(setting.warehouse, 'reference')]

    def get_comptages(self, obj):
        countings = get_inventory_countings(obj)
        return CountingSerializer(countings, many=True).data

    def get_equipe(self, obj):
        pdas = get_inventory_assignments(obj)
        return PdaTeamSerializer(pdas, many=True).data

class InventoryTeamSerializer(serializers.ModelSerializer):
    """Serializer pour récupérer l'équipe d'un inventaire"""
    user = UserAppSerializer(source='session', read_only=True)

    class Meta:
        model = Assigment
        fields = ['reference', 'user']

class InventoryWarehouseStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des warehouses d'un inventaire"""
    warehouse_reference = serializers.CharField()
    warehouse_name = serializers.CharField()
    jobs_count = serializers.IntegerField()
    teams_count = serializers.IntegerField()
    
    class Meta:
        fields = ['warehouse_reference', 'warehouse_name', 'jobs_count', 'teams_count'] 

class InventoryUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour d'inventaire."""
    label = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    account_id = serializers.IntegerField(required=False)
    inventory_type = serializers.ChoiceField(
        choices=[(t, t) for t in InventoryType.ALL],
        required=False
    )
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def validate(self, data):
        """
        Valide les données de mise à jour selon les règles métier.
        """
        errors = []
        
        # Validation des entrepôts si fournis
        warehouse = data.get('warehouse', [])
        if warehouse:
            for i, warehouse_info in enumerate(warehouse):
                if not warehouse_info.get('id'):
                    raise serializers.ValidationError(f"L'entrepôt {i+1} doit avoir un ID")
        
        # Validation des comptages si fournis
        comptages = data.get('comptages', [])
        if comptages:
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
            valid_modes = ['en vrac', 'par article', 'image de stock']
            for i, mode in enumerate(count_modes):
                if mode not in valid_modes:
                    raise serializers.ValidationError(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
            
            # Validation des combinaisons autorisées
            first_mode = count_modes[0]
            second_mode = count_modes[1]
            third_mode = count_modes[2]
            
            # Scénario 1: Premier comptage = "image de stock"
            if first_mode == "image de stock":
                # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
                if second_mode != third_mode:
                    raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent avoir le même mode")
                
                if second_mode not in ["en vrac", "par article"]:
                    raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
            
            # Scénario 2: Premier comptage = "en vrac" ou "par article"
            elif first_mode in ["en vrac", "par article"]:
                # Tous les comptages doivent être "en vrac" ou "par article"
                for i, mode in enumerate(count_modes):
                    if mode not in ["en vrac", "par article"]:
                        raise serializers.ValidationError(f"Si le premier comptage n'est pas 'image de stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")
        
        return data 

class InventoryDetailModeFieldsSerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()
    account_reference = serializers.SerializerMethodField()
    magasins = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()
    ressources = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'reference', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date',
            'en_realisation_status_date', 'termine_status_date',
            'cloture_status_date', 'account_name', 'account_reference', 'magasins',
            'comptages', 'equipe', 'ressources'
        ]
    
    def get_account_name(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.account_name if setting else None

    def get_account_reference(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.reference if setting and hasattr(setting.account, 'reference') else None
    
    def get_magasins(self, obj):
        settings = get_inventory_settings(obj)
        magasins = []
        for setting in settings:
            magasins.append({
                'id': setting.warehouse.id,
                'setting_id': setting.id,
                'reference': setting.warehouse.reference or '',
                'nom': setting.warehouse.warehouse_name,
                'date': (
                    setting.warehouse_date
                    if getattr(setting, 'warehouse_date', None)
                    else (setting.created_at.date() if setting.created_at else None)
                ),
                'status': setting.status,
                'status_date_lancement': (
                    setting.status_date_lancement.isoformat()
                    if setting.status_date_lancement
                    else None
                ),
                'status_date_cloture': (
                    setting.status_date_cloture.isoformat()
                    if setting.status_date_cloture
                    else None
                ),
            })
        return magasins
    
    def get_comptages(self, obj):
        countings = get_inventory_countings(obj)
        return CountingModeFieldsSerializer(countings, many=True).data
    
    def get_equipe(self, obj):
        """
        Récupère l'équipe de l'inventaire groupée par session avec le nombre de comptages.
        Pour chaque session unique, on compte le nombre d'assignments (comptages) affectés.
        """
        from collections import defaultdict
        
        # Préfère le prefetch assignments ; sinon requête unique select_related
        assignments = [
            a for a in get_inventory_assignments(obj) if a.session_id
        ]
        
        # Grouper par session et compter les assignments
        session_data = defaultdict(lambda: {
            'reference': None,
            'user': None,
            'nombre_comptage': 0
        })
        
        for assignment in assignments:
            session = assignment.session
            if session:
                session_id = session.id
                if session_data[session_id]['reference'] is None:
                    # Première fois qu'on rencontre cette session, initialiser les données
                    session_data[session_id]['reference'] = assignment.reference
                    session_data[session_id]['user'] = UserAppSerializer(session).data
                
                # Compter les assignments pour cette session
                session_data[session_id]['nombre_comptage'] += 1
        
        # Convertir en liste et trier par référence
        result = [
            {
                'reference': data['reference'],
                'user': data['user'],
                'nombre_comptage': data['nombre_comptage']
            }
            for data in session_data.values()
        ]
        
        # Trier par référence pour avoir un ordre cohérent
        result.sort(key=lambda x: x['reference'] or '')
        
        return result
    
    def get_ressources(self, obj):
        from ..models import InventoryDetailRessource
        # Prefer prefetched inventorydetailressource_set when available
        cache = getattr(obj, "_prefetched_objects_cache", None)
        if cache is not None and "inventorydetailressource_set" in cache:
            ressources = list(obj.inventorydetailressource_set.all())
        else:
            ressources = list(
                InventoryDetailRessource.objects.filter(inventory=obj).select_related(
                    "ressource"
                )
            )
        return [{
            'reference': ressource.reference,
            'ressource_reference': ressource.ressource.reference if ressource.ressource and hasattr(ressource.ressource, 'reference') else None,
            'ressource_nom': ressource.ressource.libelle if ressource.ressource else None,
            'quantity': ressource.quantity
        } for ressource in ressources] 

class InventoryDetailWithWarehouseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les détails d'un inventaire avec informations complètes des warehouses
    """
    account_id = serializers.SerializerMethodField()
    account_reference = serializers.SerializerMethodField()
    warehouses = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()
    inventory_duration = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = ['id',
            'reference', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date', 'en_realisation_status_date', 
            'termine_status_date', 'cloture_status_date', 'created_at', 'updated_at',
            'account_id', 'account_reference', 'warehouses', 'comptages', 'equipe', 'inventory_duration'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_account_id(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.id if setting and setting.account else None

    def get_account_reference(self, obj):
        setting = get_first_inventory_setting(obj)
        return setting.account.reference if setting and hasattr(setting.account, 'reference') else None

    def get_warehouses(self, obj):
        """Récupère les informations détaillées des warehouses avec dates d'inventaire"""
        settings = get_inventory_settings(obj)
        warehouses_data = []
        
        for setting in settings:
            warehouse_data = WarehouseSerializer(setting.warehouse).data
            
            # Ajouter les informations spécifiques à l'inventaire pour ce warehouse
            warehouse_data.update({
                'setting_reference': setting.reference,
                'setting_created_at': setting.created_at,
                'setting_updated_at': setting.updated_at,
                'inventory_start_date': setting.created_at,  # Date de début d'inventaire pour ce warehouse
                'inventory_end_date': setting.updated_at,    # Date de fin d'inventaire pour ce warehouse
            })
            
            warehouses_data.append(warehouse_data)
        
        return warehouses_data

    def get_comptages(self, obj):
        countings = get_inventory_countings(obj)
        return CountingDetailSerializer(countings, many=True).data

    def get_equipe(self, obj):
        pdas = get_inventory_assignments(obj)
        return PdaTeamSerializer(pdas, many=True).data

    def get_inventory_duration(self, obj):
        """Calcule la durée totale de l'inventaire"""
        if obj.cloture_status_date and obj.en_preparation_status_date:
            duration = obj.cloture_status_date - obj.en_preparation_status_date
            return {
                'total_days': duration.days,
                'total_hours': duration.total_seconds() / 3600,
                'start_date': obj.en_preparation_status_date,
                'end_date': obj.cloture_status_date
            }
        return None


# ========================================
# Serializers séparés pour les endpoints décomposés
# Ces serializers ne font que du formatage, la logique métier est dans le service
# ========================================

class InventoryBasicInfoSerializer(serializers.Serializer):
    """
    Serializer pour les informations de base d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    """
    reference = serializers.CharField()
    label = serializers.CharField()
    date = serializers.DateField()
    status = serializers.CharField()
    inventory_type = serializers.CharField()
    en_preparation_status_date = serializers.DateTimeField(allow_null=True)
    en_realisation_status_date = serializers.DateTimeField(allow_null=True)
    termine_status_date = serializers.DateTimeField(allow_null=True)
    cloture_status_date = serializers.DateTimeField(allow_null=True)


class InventoryAccountSerializer(serializers.Serializer):
    """
    Serializer pour les informations du compte d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    """
    account_name = serializers.CharField(allow_null=True)
    account_reference = serializers.CharField(allow_null=True)


class InventoryWarehousesSerializer(serializers.Serializer):
    """
    Serializer pour la liste des magasins d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    Chaque magasin contient : id, setting_id, reference, nom, date,
    status (Setting), status_date_lancement, status_date_cloture.
    """
    magasins = serializers.ListField(
        child=serializers.DictField()
    )


class InventoryCountingsSerializer(serializers.Serializer):
    """
    Serializer pour la liste des comptages d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    """
    comptages = serializers.ListField(
        child=serializers.DictField()
    )


class MagasinCountingConfigSerializer(serializers.Serializer):
    """
    Configuration du comptage unique pour un inventaire MAGASIN / TOURNANT.

    Accepte les alias API has_article / has_quantity (mappés vers show_product / quantity_show).
    Modes autorisés : en vrac, par article.
    """
    count_mode = serializers.ChoiceField(
        choices=[
            (CountMode.IN_BULK, CountMode.IN_BULK),
            (CountMode.BY_ARTICLE, CountMode.BY_ARTICLE),
        ]
    )
    order = serializers.IntegerField(required=False, default=1, min_value=1)
    n_lot = serializers.BooleanField(required=False, default=False)
    n_serie = serializers.BooleanField(required=False, default=False)
    dlc = serializers.BooleanField(required=False, default=False)
    has_article = serializers.BooleanField(required=False, default=False)
    has_quantity = serializers.BooleanField(required=False, default=False)
    # Champs techniques existants (optionnels — pour en vrac)
    unit_scanned = serializers.BooleanField(required=False, default=False)
    entry_quantity = serializers.BooleanField(required=False, default=False)
    # Alias historiques éventuels
    show_product = serializers.BooleanField(required=False)
    quantity_show = serializers.BooleanField(required=False)

    def validate(self, data):
        """Normalise les alias API vers les champs modèle Counting."""
        if data.get('show_product') is None:
            data['show_product'] = data.get('has_article', False)
        if data.get('quantity_show') is None:
            data['quantity_show'] = data.get('has_quantity', False)

        # Pour en vrac : au moins une saisie (règle CountingByInBulk)
        if data['count_mode'] == CountMode.IN_BULK:
            if not data.get('unit_scanned') and not data.get('entry_quantity'):
                data['entry_quantity'] = True

        # Pour par article : forcer les contraintes habituelles
        if data['count_mode'] == CountMode.BY_ARTICLE:
            data['unit_scanned'] = False
            data['entry_quantity'] = False
            data['stock_situation'] = False
            if data.get('n_serie') and data.get('n_lot'):
                raise serializers.ValidationError(
                    "Pour le mode 'par article', n_serie et n_lot ne peuvent pas être true simultanément."
                )

        data['order'] = data.get('order') or 1
        data['stock_situation'] = data.get('stock_situation', False)
        data['is_variant'] = data.get('is_variant', False)
        return data


class GeneralCountingConfigSerializer(serializers.Serializer):
    """
    Configuration des 3 comptages initiaux pour un inventaire GENERAL.

    Exactement 3 comptages (ordres 1, 2, 3). Les 4e, 5e, n-ième se lancent au déroulement
    via l'API jobs/launch-counting/ (pas de plafond fixe à 5).
    """
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        allow_empty=False,
    )

    def validate_comptages(self, comptages):
        """Valide exactement 3 comptages et les règles de cohérence de modes."""
        if len(comptages) != 3:
            raise serializers.ValidationError(
                "Un inventaire GENERAL doit être configuré avec exactement 3 comptages."
            )

        normalized = []
        for raw in comptages:
            item = dict(raw)
            # Alias API
            if 'show_product' not in item and 'has_article' in item:
                item['show_product'] = item.get('has_article', False)
            if 'quantity_show' not in item and 'has_quantity' in item:
                item['quantity_show'] = item.get('has_quantity', False)
            item.setdefault('show_product', False)
            item.setdefault('quantity_show', False)
            item.setdefault('unit_scanned', False)
            item.setdefault('entry_quantity', False)
            item.setdefault('stock_situation', False)
            item.setdefault('is_variant', False)
            item.setdefault('n_lot', False)
            item.setdefault('n_serie', False)
            item.setdefault('dlc', False)

            mode = item.get('count_mode')
            if mode == CountMode.IN_BULK:
                if not item.get('unit_scanned') and not item.get('entry_quantity'):
                    item['entry_quantity'] = True
            elif mode == CountMode.BY_ARTICLE:
                item['unit_scanned'] = False
                item['entry_quantity'] = False
                item['stock_situation'] = False
            elif mode == CountMode.STOCK_IMAGE:
                item['stock_situation'] = True
                item['unit_scanned'] = False
                item['entry_quantity'] = False
                item['is_variant'] = False
                item['n_lot'] = False
                item['n_serie'] = False
                item['dlc'] = False
                item['show_product'] = False
                item['quantity_show'] = False

            normalized.append(item)

        comptages_sorted = sorted(normalized, key=lambda x: x.get('order', 0))
        orders = [c.get('order') for c in comptages_sorted]
        if orders != [1, 2, 3]:
            raise serializers.ValidationError(
                "Les comptages doivent avoir les ordres 1, 2, 3"
            )

        for i, comptage in enumerate(comptages_sorted, 1):
            if not comptage.get('count_mode'):
                raise serializers.ValidationError(
                    f"Le comptage {i} doit avoir un mode de comptage"
                )

        count_modes = [c.get('count_mode') for c in comptages_sorted]
        valid_modes = list(CountMode.ALL)
        for i, mode in enumerate(count_modes):
            if mode not in valid_modes:
                raise serializers.ValidationError(
                    f"Comptage {i + 1}: Mode de comptage invalide '{mode}'"
                )

        first_mode, second_mode, third_mode = count_modes[0], count_modes[1], count_modes[2]

        if first_mode == CountMode.STOCK_IMAGE:
            if second_mode != third_mode:
                raise serializers.ValidationError(
                    "Si le premier comptage est 'image de stock', "
                    "les 2e et 3e comptages doivent avoir le même mode"
                )
            if second_mode not in [CountMode.IN_BULK, CountMode.BY_ARTICLE]:
                raise serializers.ValidationError(
                    "Si le premier comptage est 'image de stock', "
                    "les 2e et 3e comptages doivent être 'en vrac' ou 'par article'"
                )
        elif first_mode in [CountMode.IN_BULK, CountMode.BY_ARTICLE]:
            for i, mode in enumerate(count_modes):
                if mode not in [CountMode.IN_BULK, CountMode.BY_ARTICLE]:
                    raise serializers.ValidationError(
                        "Si le premier comptage n'est pas 'image de stock', "
                        "tous les comptages doivent être 'en vrac' ou 'par article' "
                        f"(comptage {i + 1}: '{mode}')"
                    )

        return comptages_sorted


class InventoryTeamDetailSerializer(serializers.Serializer):
    """
    Serializer pour l'équipe d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    """
    equipe = serializers.ListField(
        child=serializers.DictField()
    )


class InventoryResourcesDetailSerializer(serializers.Serializer):
    """
    Serializer pour les ressources d'un inventaire.
    Ne fait que du formatage, les données viennent du service.
    """
    ressources = serializers.ListField(
        child=serializers.DictField()
    )
