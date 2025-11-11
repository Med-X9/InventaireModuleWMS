from rest_framework import serializers

from apps.inventory.models import Personne


class PersonSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'entité Personne.
    """

    class Meta:
        model = Personne
        fields = [
            "id",
            "reference",
            "nom",
            "prenom",
            "created_at",
            "updated_at",
        ]

