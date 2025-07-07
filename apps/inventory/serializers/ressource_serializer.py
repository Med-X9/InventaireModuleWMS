from rest_framework import serializers

class RessourceListSerializer(serializers.Serializer):
    """
    Serializer pour la liste des ressources
    Retourne seulement reference, libelle et type_ressource
    """
    reference = serializers.CharField()
    libelle = serializers.CharField()
    type_ressource = serializers.CharField(allow_null=True)

class RessourceDetailSerializer(serializers.Serializer):
    """
    Serializer pour le détail d'une ressource
    """
    reference = serializers.CharField()
    libelle = serializers.CharField()
    type_ressource = serializers.CharField(allow_null=True) 