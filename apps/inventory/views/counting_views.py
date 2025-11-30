from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import reverse
from django.http import HttpResponse

from ..serializers.counting_serializer import LaunchCountingRequestSerializer
from ..services.counting_launch_service import CountingLaunchService
from ..services.job_export_service import JobExportService
from ..exceptions.counting_exceptions import (
    CountingValidationError,
    CountingNotFoundError,
    CountingCreationError,
)
from ..repositories.job_repository import JobRepository


class CountingLaunchView(APIView):
    """
    API REST pour lancer un nouveau comptage (3e ou ultérieur) pour un job donné.
    
    Supporte deux formats :
    1. Ancien format : job_id, location_id, session_id (pour un seul emplacement)
    2. Nouveau format : jobs[] (liste de job IDs), session_id (pour tous les emplacements avec écart)
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = CountingLaunchService()
        self.job_repository = JobRepository()
        self.export_service = JobExportService()

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

        validated_data = serializer.validated_data
        session_id = validated_data['session_id']
        
        # Vérifier si c'est le nouveau format (jobs[]) ou l'ancien format (job_id, location_id)
        if 'jobs' in validated_data and validated_data['jobs']:
            # Nouveau format : traiter plusieurs jobs
            return self._handle_multiple_jobs(validated_data['jobs'], session_id)
        else:
            # Ancien format : traiter un seul job/emplacement
            return self._handle_single_job(
                validated_data['job_id'],
                validated_data['location_id'],
                session_id
            )

    def _handle_single_job(self, job_id: int, location_id: int, session_id: int) -> Response:
        """
        Gère le format ancien : un seul job et un seul emplacement.
        """
        try:
            result = self.service.launch_counting(job_id, location_id, session_id)
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

    def _handle_multiple_jobs(self, job_ids: list, session_id: int) -> Response:
        """
        Gère le nouveau format : plusieurs jobs, recherche automatique des emplacements avec écart.
        Appelle l'export seulement si TOUS les emplacements ont été traités avec succès (all or nothing).
        """
        try:
            # Traiter tous les jobs et leurs emplacements avec écart
            result = self.service.launch_counting_for_jobs(job_ids, session_id)
            
            # Vérifier si aucun emplacement avec écart n'a été trouvé
            if result['total_locations_found'] == 0:
                return Response(
                    {
                        'success': False,
                        'message': 'Aucun emplacement avec écart trouvé pour les jobs fournis.',
                        'data': result,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Vérifier si tous les emplacements ont été traités avec succès (all or nothing)
            all_success = (
                result['total_locations_found'] > 0 and
                result['total_locations_processed'] == result['total_locations_found'] and
                result['total_locations_failed'] == 0 and
                len(result['errors']) == 0
            )
            
            if not all_success:
                # Certains emplacements ont échoué, retourner une erreur
                return Response(
                    {
                        'success': False,
                        'message': f'Échec du traitement : {result["total_locations_failed"]} emplacement(s) sur {result["total_locations_found"]} ont échoué. Aucun export effectué.',
                        'data': result,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Tous les emplacements ont été traités avec succès, appeler l'export
            first_job = self.job_repository.get_job_by_id(job_ids[0])
            if not first_job:
                return Response(
                    {
                        'success': False,
                        'message': 'Impossible de récupérer les informations du job pour l\'export.',
                        'data': result,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            try:
                # Appeler l'export
                excel_buffer = self.export_service.generate_excel_export(
                    first_job.inventory_id,
                    first_job.warehouse_id
                )
                
                # Récupérer les informations pour le nom du fichier
                from ..models import Inventory
                from apps.masterdata.models import Warehouse
                inventory = Inventory.objects.get(id=first_job.inventory_id)
                warehouse = Warehouse.objects.get(id=first_job.warehouse_id)
                inventory_ref = inventory.reference.replace(' ', '_')
                warehouse_ref = warehouse.reference.replace(' ', '_')
                filename = f"jobs_prets_{inventory_ref}_{warehouse_ref}.xlsx"
                
                # Créer la réponse HTTP avec le fichier Excel
                response = HttpResponse(
                    excel_buffer.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
            except Exception as export_error:
                # Si l'export échoue, retourner une erreur
                return Response(
                    {
                        'success': False,
                        'message': f'Les comptages ont été lancés avec succès, mais l\'export a échoué: {str(export_error)}',
                        'data': result,
                        'export_error': str(export_error),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        except Exception as exc:
            return Response(
                {'success': False, 'message': f'Erreur inattendue: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

