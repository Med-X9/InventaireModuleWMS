from rest_framework import serializers
from ..models import InventoryDetailRessource

class InventoryResourceAssignmentSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un inventaire"""
    
    resource_id = serializers.IntegerField(
        help_text="ID de la ressource à affecter"
    )
    quantity = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Quantité de la ressource à affecter (défaut: 1)"
    )

class AssignResourcesToInventorySerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un inventaire (format complet)"""
    
    resource_assignments = serializers.ListField(
        child=InventoryResourceAssignmentSerializer(),
        help_text="Liste des ressources à affecter avec leurs quantités"
    )

class AssignResourcesToInventorySimpleSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un inventaire (format simplifié)"""
    
    resource_assignments = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Liste des IDs des ressources à affecter (quantité = 1 par défaut)"
    )

class FlexibleResourceAssignmentField(serializers.Field):
    """Champ flexible qui accepte soit un entier soit un objet avec resource_id et quantity"""
    
    def to_internal_value(self, data):
        if isinstance(data, int):
            return {'resource_id': data, 'quantity': 1}
        elif isinstance(data, dict) and 'resource_id' in data:
            return {
                'resource_id': data['resource_id'],
                'quantity': data.get('quantity', 1)
            }
        else:
            raise serializers.ValidationError("Doit être un entier ou un objet avec resource_id")

class AssignResourcesToInventoryDirectSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un inventaire (format direct - liste d'IDs ou liste d'objets)"""
    
    def to_internal_value(self, data):
        """
        Accepte directement une liste d'IDs, une liste d'objets, ou un objet avec resource_assignments
        """
        if isinstance(data, list):
            # Si c'est une liste directe
            return {'resource_assignments': data}
        elif isinstance(data, dict) and 'resource_assignments' in data:
            # Si c'est déjà un objet avec resource_assignments
            return data
        else:
            raise serializers.ValidationError("Format invalide. Attendu: liste d'IDs, liste d'objets, ou objet avec resource_assignments")
    
    resource_assignments = serializers.ListField(
        child=FlexibleResourceAssignmentField(),
        help_text="Liste des ressources à affecter (IDs ou objets avec resource_id et quantity)"
    )

class InventoryResourceDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails d'une ressource affectée à un inventaire"""
    
    resource_id = serializers.IntegerField(source='ressource.id', read_only=True)
    resource_name = serializers.CharField(source='ressource.libelle', read_only=True)
    resource_code = serializers.CharField(source='ressource.reference', read_only=True)
    
    class Meta:
        model = InventoryDetailRessource
        fields = [
            'id', 'reference', 'resource_id', 'resource_name', 
            'resource_code', 'quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

class InventoryResourceAssignmentResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse d'affectation de ressources à un inventaire"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    assignments_created = serializers.IntegerField()
    assignments_updated = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    inventory_id = serializers.IntegerField()
    inventory_reference = serializers.CharField() 