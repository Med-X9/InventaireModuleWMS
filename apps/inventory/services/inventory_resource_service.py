"""
Service pour l'affectation des ressources aux inventaires.
"""
from typing import Dict, Any, List
from django.db import transaction
from ..interfaces.inventory_resource_interface import IInventoryResourceService
from ..repositories.inventory_resource_repository import InventoryResourceRepository
from ..exceptions.inventory_resource_exceptions import (
    InventoryResourceValidationError, 
    InventoryResourceBusinessRuleError,
    InventoryResourceNotFoundError
)

class InventoryResourceService(IInventoryResourceService):
    """Service pour l'affectation des ressources aux inventaires."""
    
    def __init__(self, repository: InventoryResourceRepository = None):
        self.repository = repository or InventoryResourceRepository()

    def assign_resources_to_inventory(self, inventory_id: int, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte des ressources à un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            assignment_data: Données d'affectation contenant resource_assignments
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        # Validation des données
        self.validate_inventory_resource_assignment_data(assignment_data)
        
        resource_assignments = assignment_data['resource_assignments']
        
        with transaction.atomic():
            # Vérifier que l'inventaire existe
            inventory = self.repository.get_inventory_by_id(inventory_id)
            if not inventory:
                raise InventoryResourceNotFoundError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Traiter chaque affectation de ressource
            assignments_created = 0
            assignments_updated = 0
            
            for resource_assignment in resource_assignments:
                resource_id = resource_assignment['resource_id']
                quantity = resource_assignment.get('quantity', 1)
                
                # Vérifier que la ressource existe
                resource = self.repository.get_resource_by_id(resource_id)
                if not resource:
                    raise InventoryResourceNotFoundError(f"Ressource avec l'ID {resource_id} non trouvée")
                
                # Vérifier s'il existe déjà une affectation pour cette ressource
                existing_assignment = self.repository.get_existing_inventory_resource(inventory_id, resource_id)
                
                if existing_assignment:
                    # Mettre à jour l'affectation existante
                    self.repository.update_inventory_resource(
                        existing_assignment,
                        quantity=quantity
                    )
                    assignments_updated += 1
                else:
                    # Créer une nouvelle affectation
                    assignment_data = {
                        'inventory': inventory,
                        'ressource': resource,
                        'quantity': quantity
                    }
                    
                    self.repository.create_inventory_resource(assignment_data)
                    assignments_created += 1
            
            total_assignments = assignments_created + assignments_updated
            
            return {
                'success': True,
                'message': f"{assignments_created} affectations créées, {assignments_updated} affectations mises à jour",
                'assignments_created': assignments_created,
                'assignments_updated': assignments_updated,
                'total_assignments': total_assignments,
                'inventory_id': inventory_id,
                'inventory_reference': inventory.reference
            }

    def get_inventory_resources(self, inventory_id: int) -> List[Any]:
        """
        Récupère les ressources affectées à un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Any]: Liste des objets InventoryDetailRessource
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.repository.get_inventory_by_id(inventory_id)
            if not inventory:
                raise InventoryResourceNotFoundError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Récupérer les ressources affectées
            inventory_resources = self.repository.get_inventory_resources(inventory_id)
            
            # Retourner directement les objets InventoryDetailRessource
            # Le serializer InventoryResourceDetailSerializer s'occupera de la sérialisation
            return inventory_resources
            
        except InventoryResourceNotFoundError:
            raise
        except Exception as e:
            raise InventoryResourceValidationError(f"Erreur lors de la récupération des ressources : {str(e)}")

    def remove_resources_from_inventory(self, inventory_id: int, resource_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des ressources d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            resource_ids: Liste des IDs des ressources à supprimer
            
        Returns:
            Dict[str, Any]: Résultat de la suppression
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.repository.get_inventory_by_id(inventory_id)
            if not inventory:
                raise InventoryResourceNotFoundError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Supprimer les affectations
            deleted_count = self.repository.delete_inventory_resources(inventory_id, resource_ids)
            
            return {
                'success': True,
                'message': f"{deleted_count} affectations de ressources supprimées",
                'deleted_count': deleted_count,
                'inventory_id': inventory_id,
                'inventory_reference': inventory.reference
            }
            
        except InventoryResourceNotFoundError:
            raise
        except Exception as e:
            raise InventoryResourceValidationError(f"Erreur lors de la suppression des ressources : {str(e)}")

    def validate_inventory_resource_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation des ressources à un inventaire
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            InventoryResourceValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not assignment_data.get('resource_assignments'):
            errors.append("La liste des affectations de ressources est obligatoire")
        
        # Validation des types
        resource_assignments = assignment_data.get('resource_assignments', [])
        if not isinstance(resource_assignments, list) or not resource_assignments:
            errors.append("resource_assignments doit être une liste non vide")
        
        # Validation de chaque affectation de ressource
        for i, resource_assignment in enumerate(resource_assignments):
            if not isinstance(resource_assignment, dict):
                errors.append(f"L'affectation de ressource {i+1} doit être un objet")
                continue
            
            if not resource_assignment.get('resource_id'):
                errors.append(f"resource_id est obligatoire pour l'affectation de ressource {i+1}")
            
            resource_id = resource_assignment.get('resource_id')
            if resource_id and not isinstance(resource_id, int):
                errors.append(f"resource_id doit être un entier pour l'affectation de ressource {i+1}")
            
            quantity = resource_assignment.get('quantity', 1)
            if quantity and not isinstance(quantity, int):
                errors.append(f"quantity doit être un entier pour l'affectation de ressource {i+1}")
            
            if quantity and quantity <= 0:
                errors.append(f"quantity doit être positif pour l'affectation de ressource {i+1}")
        
        if errors:
            raise InventoryResourceValidationError(" | ".join(errors)) 