"""
Vues pour l'affectation des ressources aux jobs.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Job
from ..services.resource_assignment_service import ResourceAssignmentService
from ..serializers.resource_assignment_serializer import (
    AssignResourcesToJobsSerializer,
    AssignResourcesToJobsSimpleSerializer,
    JobResourceDetailSerializer,
    RemoveResourcesFromJobSerializer,
    ResourceAssignmentResponseSerializer,
    BatchResourceAssignmentResponseSerializer,
    ResourceRemovalResponseSerializer
)
from ..exceptions.resource_assignment_exceptions import (
    ResourceAssignmentValidationError,
    ResourceAssignmentBusinessRuleError,
    ResourceAssignmentNotFoundError
)

class AssignResourcesToJobsView(APIView):
    """
    Affecte les mêmes ressources à plusieurs jobs.
    
    POST /api/inventory/jobs/assign-resources/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Affecte les mêmes ressources à plusieurs jobs.
        
        Args:
            request: Requête HTTP contenant les IDs des jobs et les ressources à affecter
            
        Returns:
            Response: Résultat de l'affectation des ressources en lot
        """
        try:
            # Valider les données de la requête avec le serializer simplifié
            serializer = AssignResourcesToJobsSimpleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': ' | '.join([f"{field}: {', '.join(errors)}" for field, errors in serializer.errors.items()])},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Adapter les données pour le service
            validated_data = serializer.validated_data
            adapted_data = {
                'job_ids': validated_data['job_ids'],
                'resource_assignments': [
                    {'resource_id': resource_id, 'quantity': 1} 
                    for resource_id in validated_data['resource_assignments']
                ]
            }
            
            # Appeler le service
            service = ResourceAssignmentService()
            result = service.assign_resources_to_jobs_batch(adapted_data)
            
            # Retourner la réponse
            response_serializer = BatchResourceAssignmentResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ResourceAssignmentValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ResourceAssignmentNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ResourceAssignmentBusinessRuleError as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response(
                {'error': f'Erreur interne du serveur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobResourcesView(APIView):
    """
    Récupère toutes les ressources affectées à un job.
    
    GET /api/inventory/jobs/{job_id}/resources/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        """
        Récupère toutes les ressources affectées à un job.
        
        Args:
            request: Requête HTTP
            job_id: ID du job (dans l'URL)
            
        Returns:
            Response: Liste des ressources affectées au job
        """
        try:
            # Vérifier que le job existe
            job = get_object_or_404(Job, id=job_id)
            
            # Appeler le service
            service = ResourceAssignmentService()
            job_resources = service.get_job_resources(job_id)
            
            # Sérialiser les données avec le serializer approprié
            serializer = JobResourceDetailSerializer(job_resources, many=True)
            
            # Retourner la réponse
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ResourceAssignmentNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'error': f'Erreur interne du serveur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RemoveResourcesFromJobView(APIView):
    """
    Supprime des ressources d'un job.
    
    DELETE /api/inventory/jobs/{job_id}/remove-resources/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, job_id):
        """
        Supprime des ressources d'un job.
        
        Args:
            request: Requête HTTP
            job_id: ID du job (dans l'URL)
            
        Returns:
            Response: Résultat de la suppression des ressources
        """
        try:
            # Vérifier que le job existe
            job = get_object_or_404(Job, id=job_id)
            
            # Valider les données de la requête
            serializer = RemoveResourcesFromJobSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': ' | '.join([f"{field}: {', '.join(errors)}" for field, errors in serializer.errors.items()])},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Appeler le service
            service = ResourceAssignmentService()
            result = service.remove_resources_from_job(job_id, serializer.validated_data['resource_ids'])
            
            # Retourner la réponse
            response_serializer = ResourceRemovalResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ResourceAssignmentValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ResourceAssignmentNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ResourceAssignmentBusinessRuleError as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response(
                {'error': f'Erreur interne du serveur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 