from rest_framework import serializers

from apps.inventory.models import Personne


class PersonSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'entité Personne.
    Retourne uniquement le numéro (numérotation) sans nom et prénom.
    """

    class Meta:
        model = Personne
        fields = [
            "numero",
        ]

