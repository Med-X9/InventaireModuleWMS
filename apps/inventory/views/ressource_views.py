"""
Vues pour la gestion des ressources.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.ressource_service import RessourceService
from ..serializers.ressource_serializer import RessourceListSerializer, RessourceDetailSerializer
from apps.masterdata.models import TypeRessource

# Configuration du logger
logger = logging.getLogger(__name__)

class RessourceListView(APIView):
    """
    Vue pour lister les ressources.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = RessourceService()

    def get(self, request, *args, **kwargs):
        """
        Récupère la liste des ressources.
        """
        try:
            # Récupérer les ressources via le service
            resources_data = self.service.get_all_resources()
            
            # Sérialiser les données
            serializer = RessourceListSerializer(resources_data, many=True)
            
            return Response({
                "message": "Liste des ressources récupérée avec succès",
                "count": len(resources_data),
                "data": serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des ressources: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RessourceDetailView(APIView):
    """
    Vue pour récupérer le détail d'une ressource.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = RessourceService()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère le détail d'une ressource.
        """
        try:
            # Récupérer la ressource via le service
            resource_data = self.service.get_resource_by_id(pk)
            
            if not resource_data:
                return Response(
                    {"error": "Ressource non trouvée"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Sérialiser les données
            serializer = RessourceDetailSerializer(resource_data)
            
            return Response({
                "message": "Détail de la ressource récupéré avec succès",
                "data": serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du détail de la ressource: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 

class RessourceInventaireListView(APIView):
    """
    Vue pour lister les ressources de type 'inventaire'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = RessourceService()

    def get(self, request, *args, **kwargs):
        try:
            type_obj = TypeRessource.objects.get(libelle__iexact='inventaire')
            resources_data = self.service.get_resources_by_type(type_obj.id)
            serializer = RessourceListSerializer(resources_data, many=True)
            return Response({
                "message": "Liste des ressources de type inventaire récupérée avec succès",
                "count": len(resources_data),
                "data": serializer.data
            })
        except TypeRessource.DoesNotExist:
            return Response({"error": "Type de ressource 'inventaire' non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des ressources de type inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RessourceJobListView(APIView):
    """
    Vue pour lister les ressources de type 'job'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = RessourceService()

    def get(self, request, *args, **kwargs):
        try:
            type_obj = TypeRessource.objects.get(libelle__iexact='job')
            resources_data = self.service.get_resources_by_type(type_obj.id)
            serializer = RessourceListSerializer(resources_data, many=True)
            return Response({
                "message": "Liste des ressources de type job récupérée avec succès",
                "count": len(resources_data),
                "data": serializer.data
            })
        except TypeRessource.DoesNotExist:
            return Response({"error": "Type de ressource 'job' non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des ressources de type job: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 