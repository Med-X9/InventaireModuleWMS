from django.db import models
from django.utils import timezone
from datetime import timedelta
from ..models import NSerie, Product, Location
from typing import List, Optional, Dict, Any

class NSerieRepository:
    """
    Repository pour la gestion des numéros de série
    """
    
    def create_nserie(self, data: Dict[str, Any]) -> NSerie:
        """
        Crée un nouveau numéro de série
        """
        nserie = NSerie.objects.create(**data)
        return nserie
    
    def get_nserie_by_id(self, nserie_id: int) -> Optional[NSerie]:
        """
        Récupère un numéro de série par son ID
        """
        try:
            return NSerie.objects.get(id=nserie_id)
        except NSerie.DoesNotExist:
            return None
    
    def get_nserie_by_reference(self, reference: str) -> Optional[NSerie]:
        """
        Récupère un numéro de série par sa référence
        """
        try:
            return NSerie.objects.get(reference=reference)
        except NSerie.DoesNotExist:
            return None
    
    def get_nserie_by_number(self, n_serie: str) -> Optional[NSerie]:
        """
        Récupère un numéro de série par son numéro
        """
        try:
            return NSerie.objects.get(n_serie=n_serie)
        except NSerie.DoesNotExist:
            return None
    
    def get_nseries_by_product(self, product_id: int) -> List[NSerie]:
        """
        Récupère tous les numéros de série d'un produit
        """
        return NSerie.objects.filter(product_id=product_id).order_by('-created_at')
    
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
        return NSerie.objects.filter(status=status).order_by('-created_at')
    
    def get_expired_nseries(self) -> List[NSerie]:
        """
        Récupère tous les numéros de série expirés
        """
        today = timezone.now().date()
        return NSerie.objects.filter(
            date_expiration__lt=today,
            status__in=['ACTIVE', 'USED']
        ).order_by('date_expiration')
    
    def get_expiring_nseries(self, days: int = 30) -> List[NSerie]:
        """
        Récupère tous les numéros de série qui expirent dans les X jours
        """
        today = timezone.now().date()
        future_date = today + timedelta(days=days)
        
        return NSerie.objects.filter(
            date_expiration__gte=today,
            date_expiration__lte=future_date,
            status__in=['ACTIVE', 'USED']
        ).order_by('date_expiration')
    
    def get_warranty_expired_nseries(self) -> List[NSerie]:
        """
        Récupère tous les numéros de série dont la garantie est expirée
        """
        today = timezone.now().date()
        return NSerie.objects.filter(
            warranty_end_date__lt=today,
            status__in=['ACTIVE', 'USED']
        ).order_by('warranty_end_date')
    
    def update_nserie(self, nserie: NSerie, data: Dict[str, Any]) -> NSerie:
        """
        Met à jour un numéro de série
        """
        for field, value in data.items():
            setattr(nserie, field, value)
        nserie.save()
        return nserie
    
    def delete_nserie(self, nserie_id: int) -> bool:
        """
        Supprime un numéro de série (soft delete)
        """
        try:
            nserie = self.get_nserie_by_id(nserie_id)
            if nserie:
                nserie.soft_delete()
                return True
            return False
        except Exception:
            return False
    
    def get_nseries_with_filters(self, filters: Dict[str, Any]) -> List[NSerie]:
        """
        Récupère les numéros de série avec des filtres
        """
        queryset = NSerie.objects.all()
        
        # Filtres par produit
        if 'product_id' in filters:
            queryset = queryset.filter(product_id=filters['product_id'])
        
        # Filtres par statut
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        
        # Filtres par emplacement (non disponible - pas de champ location dans NSerie)
        # if 'location_id' in filters:
        #     queryset = queryset.filter(location_id=filters['location_id'])
        
        # Filtres par date d'expiration
        if 'expired' in filters:
            if filters['expired']:
                today = timezone.now().date()
                queryset = queryset.filter(date_expiration__lt=today)
            else:
                today = timezone.now().date()
                queryset = queryset.filter(
                    models.Q(date_expiration__gte=today) | models.Q(date_expiration__isnull=True)
                )
        
        # Filtres par garantie expirée
        if 'warranty_expired' in filters:
            if filters['warranty_expired']:
                today = timezone.now().date()
                queryset = queryset.filter(warranty_end_date__lt=today)
            else:
                today = timezone.now().date()
                queryset = queryset.filter(
                    models.Q(warranty_end_date__gte=today) | models.Q(warranty_end_date__isnull=True)
                )
        
        # Filtres par suivi
        if 'is_tracked' in filters:
            queryset = queryset.filter(is_tracked=filters['is_tracked'])
        
        # Tri
        order_by = filters.get('order_by', '-created_at')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_nseries_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des numéros de série
        """
        total_nseries = NSerie.objects.count()
        active_nseries = NSerie.objects.filter(status='ACTIVE').count()
        expired_nseries = NSerie.objects.filter(status='EXPIRED').count()
        used_nseries = NSerie.objects.filter(status='USED').count()
        blocked_nseries = NSerie.objects.filter(status='BLOCKED').count()
        
        # Statistiques par produit
        products_with_nseries = Product.objects.filter(n_serie=True).count()
        
        # Statistiques par emplacement (non disponible - pas de champ location dans NSerie)
        nseries_with_location = 0  # Non disponible
        
        # Statistiques par date d'expiration
        today = timezone.now().date()
        expiring_soon = NSerie.objects.filter(
            date_expiration__gte=today,
            date_expiration__lte=today + timedelta(days=30),
            status__in=['ACTIVE', 'USED']
        ).count()
        
        return {
            'total_nseries': total_nseries,
            'active_nseries': active_nseries,
            'expired_nseries': expired_nseries,
            'used_nseries': used_nseries,
            'blocked_nseries': blocked_nseries,
            'products_with_nseries': products_with_nseries,
            'nseries_with_location': nseries_with_location,
            'nseries_without_location': total_nseries - nseries_with_location,
            'expiring_soon': expiring_soon
        }
    
    def search_nseries(self, search_term: str) -> List[NSerie]:
        """
        Recherche des numéros de série par terme de recherche
        """
        return NSerie.objects.filter(
            models.Q(n_serie__icontains=search_term) |
            models.Q(description__icontains=search_term) |
            models.Q(product__Short_Description__icontains=search_term) |
            models.Q(product__Internal_Product_Code__icontains=search_term)
            # models.Q(location__location_reference__icontains=search_term)  # Non disponible - pas de champ location
        ).order_by('-created_at') 