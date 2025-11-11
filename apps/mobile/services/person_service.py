from typing import Iterable, Optional

from apps.inventory.models import Personne
from apps.mobile.repositories.person_repository import PersonRepository


class PersonService:
    """
    Service pour la gestion des personnes dans l'application mobile.
    """

    def __init__(self, repository: Optional[PersonRepository] = None) -> None:
        """
        Initialise le service avec un repository, en supportant l'injection de dépendance.

        Args:
            repository: Instance de PersonRepository à utiliser. Si None, crée une instance par défaut.
        """
        self.repository = repository or PersonRepository()

    def list_persons(self) -> Iterable[Personne]:
        """
        Retourne la liste des personnes triées.

        Returns:
            Iterable[Personne]: Collection d'instances Personne.
        """
        return self.repository.list_all()

