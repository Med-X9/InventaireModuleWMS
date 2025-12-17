"""
Service pour récupérer les détails d'un inventaire par sections.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict
from ..repositories import InventoryRepository
from ..exceptions import InventoryNotFoundError
from ..models import Inventory, Setting, Counting, Assigment, InventoryDetailRessource
from .counting_service import CountingService
import logging

logger = logging.getLogger(__name__)


class InventoryDetailService:
    """
    Service pour récupérer les détails d'un inventaire par sections.
    Respecte l'architecture : Repository -> Service -> Serializer -> View
    """
    
    def __init__(self, repository: InventoryRepository = None):
        self.repository = repository or InventoryRepository()
        self.counting_service = CountingService()
    
    def get_basic_info(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère les informations de base d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict contenant les informations de base
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        
        # Convertir le datetime en date si nécessaire
        date_value = inventory.date
        if date_value and hasattr(date_value, 'date'):
            date_value = date_value.date()
        
        return {
            'reference': inventory.reference,
            'label': inventory.label,
            'date': date_value,
            'status': inventory.status,
            'inventory_type': inventory.inventory_type,
            'en_preparation_status_date': inventory.en_preparation_status_date,
            'en_realisation_status_date': inventory.en_realisation_status_date,
            'termine_status_date': inventory.termine_status_date,
            'cloture_status_date': inventory.cloture_status_date,
        }
    
    def get_account_info(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère les informations du compte d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict contenant les informations du compte
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        setting = Setting.objects.filter(inventory=inventory).first()
        
        account_name = None
        account_reference = None
        
        if setting and setting.account:
            account_name = setting.account.account_name
            if hasattr(setting.account, 'reference'):
                account_reference = setting.account.reference
        
        return {
            'account_name': account_name,
            'account_reference': account_reference,
        }
    
    def get_warehouses(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère la liste des magasins d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Liste des magasins avec nom et date
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        settings = Setting.objects.filter(inventory=inventory).select_related('warehouse')
        
        magasins = []
        for setting in settings:
            magasins.append({
                'nom': setting.warehouse.warehouse_name,
                'date': setting.created_at.date() if setting.created_at else None
            })
        
        return magasins
    
    def get_countings(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère la liste des comptages d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Liste des comptages avec leurs informations
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        countings = Counting.objects.filter(inventory=inventory).order_by('order')
        
        result = []
        for counting in countings:
            counting_data = {
                'order': counting.order,
                'count_mode': counting.count_mode,
                'champs_actifs': self._get_active_fields(counting)
            }
            result.append(counting_data)
        
        return result
    
    def _get_active_fields(self, counting: Counting) -> List[str]:
        """
        Récupère la liste des champs actifs d'un comptage.
        
        Args:
            counting: L'instance du comptage
            
        Returns:
            Liste des labels des champs actifs
        """
        if counting.count_mode == 'image de stock':
            return []
        
        mapping = {
            'unit_scanned': 'Unité scannée',
            'entry_quantity': 'Saisie quantité',
            'stock_situation': 'Situation de stock',
            'is_variant': 'Variante',
            'n_lot': 'N° lot',
            'n_serie': 'N° série',
            'dlc': 'DLC',
            'show_product': 'Afficher produit',
            'quantity_show': 'Afficher quantité',
        }
        
        actifs = []
        for field, label in mapping.items():
            if getattr(counting, field, False):
                actifs.append(label)
        
        return actifs
    
    def get_team(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère l'équipe de l'inventaire groupée par session avec le nombre de comptages.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Liste des sessions avec leurs informations
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        
        # Récupérer tous les assignments de l'inventaire avec leurs sessions
        assignments = Assigment.objects.filter(
            job__inventory=inventory,
            session__isnull=False
        ).select_related('session').prefetch_related('counting')
        
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
                    # Retourner seulement le username
                    session_data[session_id]['user'] = session.username
                
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
    
    def get_resources(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les ressources d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Liste des ressources avec leurs informations
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        inventory = self.repository.get_with_related_data(inventory_id)
        ressources = InventoryDetailRessource.objects.filter(
            inventory=inventory
        ).select_related('ressource')
        
        result = []
        for ressource in ressources:
            result.append({
                'reference': ressource.reference,
                'ressource_reference': ressource.ressource.reference if ressource.ressource and hasattr(ressource.ressource, 'reference') else None,
                'ressource_nom': ressource.ressource.libelle if ressource.ressource else None,
                'quantity': ressource.quantity
            })
        
        return result

