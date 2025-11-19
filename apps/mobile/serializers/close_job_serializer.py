from rest_framework import serializers


class CloseJobSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider les données de fermeture d'un job.
    Valide que les personnes sont présentes (min 1, max 2).
    """
    personnes = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=2,
        help_text="Liste des IDs des personnes (minimum 1, maximum 2)"
    )
    
    def validate_personnes(self, value):
        """
        Valide que la liste des personnes contient entre 1 et 2 éléments.
        
        Args:
            value: Liste des IDs des personnes
            
        Returns:
            Liste validée des IDs
            
        Raises:
            serializers.ValidationError: Si la validation échoue
        """
        if not value:
            raise serializers.ValidationError(
                "Au moins une personne est requise pour fermer le job."
            )
        
        if len(value) > 2:
            raise serializers.ValidationError(
                "Un maximum de deux personnes est autorisé pour fermer le job."
            )
        
        # Vérifier qu'il n'y a pas de doublons
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Les IDs des personnes ne doivent pas être dupliqués."
            )
        
        return value

