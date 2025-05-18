from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers import (
    InventoryJobCreateSerializer,
    JobSerializer
)
from ..services.job_service import JobService
from ..serializers.job_serializer import InventoryJobRetrieveSerializer, InventoryJobUpdateSerializer
from ..exceptions import JobCreationError

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