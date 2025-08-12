from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import NSerie, Product, Location
from ..repositories.nserie_repository import NSerieRepository
from typing import List, Dict, Any, Optional
from django.utils.translation import gettext_lazy as _

class NSerieService:
    """
    Service pour la gestion des numéros de série
    """
    
    def __init__(self):
        self.repository = NSerieRepository()
    
    @transaction.atomic
    def create_nserie(self, data: Dict[str, Any]) -> NSerie:
        """
        Crée un nouveau numéro de série
        """
        try:
            # Validation des données
            self._validate_nserie_data(data)
            
            # Création du numéro de série
            nserie = self.repository.create_nserie(data)
            
            return nserie
            
        except Exception as e:
            raise ValidationError(f"Erreur lors de la création du numéro de série: {str(e)}")
    
    @transaction.atomic
    def update_nserie(self, nserie_id: int, data: Dict[str, Any]) -> NSerie:
        """
        Met à jour un numéro de série existant
        """
        try:
            nserie = self.repository.get_nserie_by_id(nserie_id)
            if not nserie:
                raise ValidationError(f"Numéro de série avec l'ID {nserie_id} non trouvé")
            
            # Validation des données
            self._validate_nserie_update_data(nserie, data)
            
            # Mise à jour du numéro de série
            updated_nserie = self.repository.update_nserie(nserie, data)
            
            return updated_nserie
            
        except Exception as e:
            raise ValidationError(f"Erreur lors de la mise à jour du numéro de série: {str(e)}")
    
    def get_nserie_by_id(self, nserie_id: int) -> Optional[NSerie]:
        """
        Récupère un numéro de série par son ID
        """
        return self.repository.get_nserie_by_id(nserie_id)
    
    def get_nserie_by_reference(self, reference: str) -> Optional[NSerie]:
        """
        Récupère un numéro de série par sa référence
        """
        return self.repository.get_nserie_by_reference(reference)
    
    def get_nserie_by_number(self, n_serie: str) -> Optional[NSerie]:
        """
        Récupère un numéro de série par son numéro
        """
        return self.repository.get_nserie_by_number(n_serie)
    
    def get_nseries_by_product(self, product_id: int) -> List[NSerie]:
        """
        Récupère tous les numéros de série d'un produit
        """
        return self.repository.get_nseries_by_product(product_id)
    
    def get_nseries_by_location(self, location_id: int) -> List[NSerie]:
        """
        Récupère tous les numéros de série d'un emplacement
        Note: Cette méthode n'est pas disponible car NSerie n'a pas de champ location
        """
        # Cette méthode n'est pas disponible car NSerie n'a pas de champ location
        return []
    
    def get_nseries_by_status(self, status: str) -> List[NSerie]:
        """
        Récupère tous les numéros de série par statut
        """
        return self.repository.get_nseries_by_status(status)
    
    def get_expired_nseries(self) -> List[NSerie]:
        """
        Récupère tous les numéros de série expirés
        """
        return self.repository.get_expired_nseries()
    
    def get_expiring_nseries(self, days: int = 30) -> List[NSerie]:
        """
        Récupère tous les numéros de série qui expirent dans les X jours
        """
        return self.repository.get_expiring_nseries(days)
    
    def get_warranty_expired_nseries(self) -> List[NSerie]:
        """
        Récupère tous les numéros de série dont la garantie est expirée
        """
        return self.repository.get_warranty_expired_nseries()
    
    @transaction.atomic
    def delete_nserie(self, nserie_id: int) -> bool:
        """
        Supprime un numéro de série (soft delete)
        """
        try:
            nserie = self.repository.get_nserie_by_id(nserie_id)
            if not nserie:
                raise ValidationError(f"Numéro de série avec l'ID {nserie_id} non trouvé")
            
            # Soft delete
            nserie.soft_delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Erreur lors de la suppression du numéro de série: {str(e)}")
    
    @transaction.atomic
    def move_nserie_to_location(self, nserie_id: int, location_id: int) -> NSerie:
        """
        Déplace un numéro de série vers un nouvel emplacement
        Note: Cette méthode n'est pas disponible car NSerie n'a pas de champ location
        """
        # Cette méthode n'est pas disponible car NSerie n'a pas de champ location
        raise ValidationError("Cette fonctionnalité n'est pas disponible car NSerie n'a pas de champ location")
    
    @transaction.atomic
    def update_nserie_status(self, nserie_id: int, status: str) -> NSerie:
        """
        Met à jour le statut d'un numéro de série
        """
        try:
            nserie = self.repository.get_nserie_by_id(nserie_id)
            if not nserie:
                raise ValidationError(f"Numéro de série avec l'ID {nserie_id} non trouvé")
            
            # Validation du statut
            valid_statuses = [choice[0] for choice in NSerie.STATUS_CHOICES]
            if status not in valid_statuses:
                raise ValidationError(f"Statut invalide: {status}")
            
            # Mise à jour du statut
            nserie.status = status
            nserie.save()
            
            return nserie
            
        except Exception as e:
            raise ValidationError(f"Erreur lors de la mise à jour du statut: {str(e)}")
    
    def get_nserie_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des numéros de série
        """
        try:
            total_nseries = NSerie.objects.count()
            active_nseries = NSerie.objects.filter(status='ACTIVE').count()
            expired_nseries = NSerie.objects.filter(status='EXPIRED').count()
            used_nseries = NSerie.objects.filter(status='USED').count()
            blocked_nseries = NSerie.objects.filter(status='BLOCKED').count()
            
            # Statistiques par produit
            products_with_nseries = Product.objects.filter(n_serie=True).count()
            
            # Statistiques par emplacement
            nseries_with_location = NSerie.objects.filter(location__isnull=False).count()
            
            return {
                'total_nseries': total_nseries,
                'active_nseries': active_nseries,
                'expired_nseries': expired_nseries,
                'used_nseries': used_nseries,
                'blocked_nseries': blocked_nseries,
                'products_with_nseries': products_with_nseries,
                'nseries_with_location': nseries_with_location,
                'nseries_without_location': total_nseries - nseries_with_location
            }
            
        except Exception as e:
            raise ValidationError(f"Erreur lors du calcul des statistiques: {str(e)}")
    
    def _validate_nserie_data(self, data: Dict[str, Any]) -> None:
        """
        Validation des données pour la création
        """
        product = data.get('product')
        n_serie = data.get('n_serie')
        
        if not product:
            raise ValidationError(_('Le produit est obligatoire'))
        
        if not n_serie:
            raise ValidationError(_('Le numéro de série est obligatoire'))
        
        # Vérifier que le produit supporte les numéros de série
        if not product.n_serie:
            raise ValidationError(_('Ce produit ne supporte pas les numéros de série'))
        
        # Vérifier l'unicité du numéro de série pour ce produit
        if NSerie.objects.filter(n_serie=n_serie, product=product).exists():
            raise ValidationError(_('Ce numéro de série existe déjà pour ce produit'))
    
    def _validate_nserie_update_data(self, nserie: NSerie, data: Dict[str, Any]) -> None:
        """
        Validation des données pour la mise à jour
        """
        # Vérifier que le produit supporte toujours les numéros de série
        if not nserie.product.n_serie:
            raise ValidationError(_('Ce produit ne supporte pas les numéros de série'))
        
        # Validation des dates si fournies
        date_expiration = data.get('date_expiration')
        warranty_end_date = data.get('warranty_end_date')
        
        if date_expiration and warranty_end_date:
            if date_expiration > warranty_end_date:
                raise ValidationError(_('La date d\'expiration ne peut pas être postérieure à la date de fin de garantie')) 