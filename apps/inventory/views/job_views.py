from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers import (
    InventoryJobCreateSerializer,
    JobSerializer
)
from ..services.job_service import JobService
from ..serializers.job_serializer import (
    InventoryJobRetrieveSerializer, 
    InventoryJobUpdateSerializer,
    JobAssignmentRequestSerializer
)
from ..exceptions import JobCreationError
import logging
from datetime import datetime
from ..models import Warehouse

logger = logging.getLogger(__name__)

class InventoryJobCreateView(APIView):
    def post(self, request):
        try:
            result = JobService.create_inventory_jobs(request.data)
            return Response({"message": "Ajouter avec succès"}, status=status.HTTP_201_CREATED)
        except JobCreationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryJobRetrieveView(APIView):
    def get(self, request, inventory_id, warehouse_id):
        """
        Récupère les jobs d'inventaire pour un inventaire et un warehouse spécifiques
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
        """
        try:
            result = JobService.get_inventory_jobs(inventory_id, warehouse_id)
            return Response(result, status=status.HTTP_200_OK)
        except JobCreationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryJobUpdateView(APIView):
    def put(self, request, inventory_id, warehouse_id):
        try:
            # Valider les données
            serializer = InventoryJobUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Mettre à jour les jobs
            JobService.update_inventory_jobs(inventory_id, warehouse_id, serializer.validated_data)
            return Response({"message": "Modification effectuée avec succès"}, status=status.HTTP_200_OK)

        except JobCreationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryJobDeleteView(APIView):
    def delete(self, request, inventory_id, warehouse_id):
        try:
            # Supprimer les jobs
            JobService.delete_inventory_jobs(inventory_id, warehouse_id)
            return Response({"message": "Suppression effectuée avec succès"}, status=status.HTTP_200_OK)

        except JobCreationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryJobAssignmentView(APIView):
    """
    Vue pour affecter des jobs à l'équipe
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = JobService()

    def post(self, request, *args, **kwargs):
        """
        Affecte des jobs à l'équipe
        """
        try:
            serializer = JobAssignmentRequestSerializer(data=request.data)
            if serializer.is_valid():
                result = self.service.assign_jobs_to_team(serializer.validated_data)
                return Response(result, status=status.HTTP_200_OK)
            
            logger.warning(f"Données invalides lors de l'affectation des jobs: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except JobCreationError as e:
            logger.warning(f"Erreur lors de l'affectation des jobs: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'affectation des jobs: {str(e)}", exc_info=True)
            return Response(
                {"error": "Une erreur inattendue s'est produite lors de l'affectation des jobs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PendingJobsView(APIView):
    """
    Vue pour récupérer les jobs en attente d'un warehouse
    """
    def get(self, request, warehouse_id):
        try:
            # Récupérer les paramètres de pagination
            try:
                page = int(request.query_params.get('page', 1))
                if page < 1:
                    raise ValueError
            except ValueError:
                return Response(
                    {'error': 'Numéro de page invalide'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                page_size = int(request.query_params.get('page_size', 10))
                if page_size < 1 or page_size > 100:
                    raise ValueError
            except ValueError:
                return Response(
                    {'error': 'Taille de page invalide. Doit être entre 1 et 100'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Récupérer les jobs
            result = JobService.get_pending_jobs(
                warehouse_id=warehouse_id,
                filters=request.query_params,
                page=page,
                page_size=page_size
            )

            return Response(result)

        except JobCreationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des jobs: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Une erreur inattendue s\'est produite'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LaunchJobsView(APIView):
    """
    Vue pour lancer des jobs
    """
    def post(self, request, warehouse_id):
        try:
            # Vérifier que le warehouse existe
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                return Response(
                    {"error": f"Warehouse avec l'ID {warehouse_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Récupérer les IDs des jobs
            job_ids = request.data.get('job_ids', [])
            if not job_ids:
                return Response(
                    {"error": "Aucun job ID fourni"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lancer les jobs
            result = JobService.launch_jobs(job_ids)
            return Response(result, status=status.HTTP_200_OK)

        except JobCreationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors du lancement des jobs: {str(e)}")
            return Response(
                {"error": f"Erreur lors du lancement des jobs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 