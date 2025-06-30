from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

class JobAssignmentSerializer(serializers.Serializer):
    """
    Serializer pour l'affectation des jobs de comptage
    """
    inventory_id = serializers.IntegerField(
        help_text="ID de l'inventaire (récupéré depuis l'URL)"
    )
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Liste des IDs des jobs à affecter"
    )
    counting_order = serializers.IntegerField(
        min_value=1,
        max_value=2,
        help_text="Ordre du comptage (1 ou 2)"
    )
    session_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID de la session (optionnel pour le mode 'image stock')"
    )
    date_start = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Date de début (optionnel, utilise la date actuelle par défaut)"
    )
    
    def validate_job_ids(self, value):
        """
        Valide la liste des IDs des jobs
        """
        if not value:
            raise serializers.ValidationError("La liste des IDs des jobs ne peut pas être vide")
        
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Les IDs des jobs doivent être uniques")
        
        return value
    
    def validate_counting_order(self, value):
        """
        Valide l'ordre du comptage
        """
        if value not in [1, 2]:
            raise serializers.ValidationError("L'ordre du comptage doit être 1 ou 2")
        
        return value
    
    def validate_date_start(self, value):
        """
        Valide la date de début
        """
        if value and value < timezone.now() - timezone.timedelta(days=1):
            raise serializers.ValidationError("La date de début ne peut pas être dans le passé")
        
        return value
    
    def validate(self, data):
        """
        Validation croisée des champs
        """
        counting_order = data.get('counting_order')
        session_id = data.get('session_id')
        
        # Pour le premier comptage, la session peut être optionnelle selon le mode
        # Cette validation sera faite dans le service
        
        return data

class JobAssignmentResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse de l'affectation des jobs
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    assignments_created = serializers.IntegerField()
    assignments_updated = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    counting_order = serializers.IntegerField()
    inventory_id = serializers.IntegerField()
    timestamp = serializers.DateTimeField(default=timezone.now)

class AssignmentRulesSerializer(serializers.Serializer):
    """
    Serializer pour les règles d'affectation
    """
    rules = serializers.DictField() 