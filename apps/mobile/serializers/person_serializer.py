from rest_framework import serializers

from apps.inventory.models import Personne


class PersonSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'entité Personne.
    Retourne le numéro (numérotation) et l'ID pour l'application mobile.
    """

    class Meta:
        model = Personne
        fields = [
            "id",
            "numero",
        ]

