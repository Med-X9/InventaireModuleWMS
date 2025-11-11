from typing import Iterable
from apps.inventory.models import Personne


class PersonRepository:
    """
    Repository dédié à l'accès aux données des personnes.
    """

    def list_all(self) -> Iterable[Personne]:
        """
        Récupère toutes les personnes enregistrées.

        Returns:
            Iterable[Personne]: Liste ou QuerySet des personnes triées par nom puis prénom.
        """
        return Personne.objects.all().order_by("nom", "prenom")

