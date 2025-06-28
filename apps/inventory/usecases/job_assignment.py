"""
Use case pour l'affectation des jobs de comptage.
"""
from typing import Dict, Any
from django.utils import timezone
from ..services.assignment_service import AssignmentService
from ..exceptions.assignment_exceptions import (
    AssignmentValidationError,
    AssignmentBusinessRuleError,
    AssignmentSessionError
)

class JobAssignmentUseCase:
    """
    Use case pour l'affectation des jobs de comptage.
    
    Ce use case gère :
    - La validation des règles métier pour l'affectation
    - La gestion des sessions selon le mode de comptage
    - L'affectation des jobs avec date_start et session
    """
    
    def __init__(self, assignment_service: AssignmentService = None):
        self.assignment_service = assignment_service or AssignmentService()
    
    def assign_jobs_to_counting(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte des jobs à un comptage spécifique
        
        Args:
            assignment_data: Données d'affectation contenant :
                - job_ids: Liste des IDs des jobs
                - counting_order: Ordre du comptage (1, 2, ou 3)
                - session_id: ID de la session (optionnel)
                - date_start: Date de début (optionnel)
        
        Returns:
            Dict[str, Any]: Résultat de l'affectation
            
        Raises:
            AssignmentValidationError: Si les données sont invalides
            AssignmentBusinessRuleError: Si une règle métier n'est pas respectée
            AssignmentSessionError: Si l'affectation de session n'est pas autorisée
        """
        # Validation préliminaire
        self._validate_assignment_request(assignment_data)
        
        # Traitement de l'affectation via le service
        result = self.assignment_service.assign_jobs(assignment_data)
        
        return result
    
    def _validate_assignment_request(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide la demande d'affectation selon les règles métier
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            AssignmentValidationError: Si la validation échoue
        """
        errors = []
        
        # Validation des champs obligatoires
        if not assignment_data.get('job_ids'):
            errors.append("La liste des IDs des jobs est obligatoire")
        
        if not assignment_data.get('counting_order'):
            errors.append("L'ordre du comptage est obligatoire")
        
        # Validation de l'ordre du comptage
        counting_order = assignment_data.get('counting_order')
        if counting_order and counting_order not in [1, 2, 3]:
            errors.append("L'ordre du comptage doit être 1, 2 ou 3")
        
        # Validation de la session pour le mode "image stock"
        counting_order = assignment_data.get('counting_order')
        session_id = assignment_data.get('session_id')
        
        if counting_order == 1 and session_id:
            # Pour le premier comptage, vérifier si c'est "image stock"
            # Cette validation sera faite plus tard dans le service
            pass
        
        if errors:
            raise AssignmentValidationError(" | ".join(errors))
    
    def get_assignment_rules(self) -> Dict[str, Any]:
        """
        Retourne les règles d'affectation pour information
        
        Returns:
            Dict[str, Any]: Règles d'affectation
        """
        return {
            "rules": {
                "counting_modes": {
                    "image_stock": {
                        "description": "Comptage basé sur l'image de stock",
                        "session_required": False,
                        "automatic": True
                    },
                    "en_vrac": {
                        "description": "Comptage en lot",
                        "session_required": True,
                        "automatic": False
                    },
                    "par_article": {
                        "description": "Comptage article par article",
                        "session_required": True,
                        "automatic": False
                    }
                },
                "counting_orders": {
                    "1": "Premier comptage",
                    "2": "Deuxième comptage", 
                    "3": "Troisième comptage"
                },
                "session_rules": {
                    "image_stock": "Pas d'affectation de session (automatique)",
                    "en_vrac": "Affectation de session obligatoire",
                    "par_article": "Affectation de session obligatoire"
                }
            }
        } 