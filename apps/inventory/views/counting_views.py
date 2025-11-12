from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.counting_serializer import LaunchCountingRequestSerializer
from ..services.counting_launch_service import CountingLaunchService
from ..exceptions.counting_exceptions import (
    CountingValidationError,
    CountingNotFoundError,
    CountingCreationError,
)


class CountingLaunchView(APIView):
    """
    API REST pour lancer un nouveau comptage (3e ou ultérieur) pour un job donné.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = CountingLaunchService()

    def post(self, request):
        serializer = LaunchCountingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = self.service.launch_counting(**serializer.validated_data)
            status_code = status.HTTP_201_CREATED if (
                result['counting']['new_counting_created'] or result['assignment']['created']
            ) else status.HTTP_200_OK

            return Response(
                {
                    'success': True,
                    'message': 'Comptage lancé avec succès.',
                    'data': result,
                },
                status=status_code,
            )
        except CountingValidationError as exc:
            return Response(
                {'success': False, 'message': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CountingNotFoundError as exc:
            return Response(
                {'success': False, 'message': str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except CountingCreationError as exc:
            return Response(
                {'success': False, 'message': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

