"""
Vues pour l'affectation des ressources aux jobs.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Job
from ..services.resource_assignment_service import ResourceAssignmentService
from ..serializers.resource_assignment_serializer import (
    AssignResourcesToJobsSerializer,
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_resources_to_jobs(request):
    """
    Affecte les mêmes ressources à plusieurs jobs.
    
    Args:
        request: Requête HTTP contenant les IDs des jobs et les ressources à affecter
        
    Returns:
        Response: Résultat de l'affectation des ressources en lot
    """
    try:
        # Valider les données de la requête
        serializer = AssignResourcesToJobsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': ' | '.join([f"{field}: {', '.join(errors)}" for field, errors in serializer.errors.items()])},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Appeler le service
        service = ResourceAssignmentService()
        result = service.assign_resources_to_jobs_batch(serializer.validated_data)
        
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_resources(request, job_id):
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
        resources_data = service.get_job_resources(job_id)
        
        # Retourner la réponse
        return Response(resources_data, status=status.HTTP_200_OK)
        
    except ResourceAssignmentNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {'error': f'Erreur interne du serveur: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_resources_from_job(request, job_id):
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