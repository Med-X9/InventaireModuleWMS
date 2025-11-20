from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mobile.serializers import PersonSerializer
from apps.mobile.services.person_service import PersonService
from apps.mobile.utils import success_response, error_response

import logging

logger = logging.getLogger(__name__)


class PersonListView(APIView):
    """
    Vue permettant de récupérer la liste des personnes disponibles pour l'application mobile.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.person_service = PersonService()

    def get(self, request):
        """
        Retourne l'ensemble des personnes triées par nom puis prénom.
        """
        try:
            # Récupérer les personnes via le service dédié
            persons = self.person_service.list_persons()

            # Sérialiser les données pour la réponse API
            serializer = PersonSerializer(persons, many=True)

            return success_response(
                data=serializer.data,
                message="Personnes récupérées avec succès"
            )
        except Exception as exc:  # pragma: no cover - log et réponse générique
            logger.exception("Erreur lors de la récupération des personnes: %s", exc)
            return error_response(
                message="Erreur interne du serveur",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

