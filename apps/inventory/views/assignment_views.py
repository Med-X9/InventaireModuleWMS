from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from ..serializers.assignment_serializer import (
    JobAssignmentSerializer,
    JobAssignmentResponseSerializer,
    AssignmentRulesSerializer
)
from ..usecases.job_assignment import JobAssignmentUseCase
from ..exceptions.assignment_exceptions import (
    AssignmentValidationError,
    AssignmentBusinessRuleError,
    AssignmentSessionError,
    AssignmentNotFoundError
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_jobs_to_counting(request):
    """
    Affecte des jobs à un comptage spécifique
    
    POST /api/inventory/assign-jobs/
    
    Body:
    {
        "job_ids": [1, 2, 3],
        "counting_order": 1,
        "session_id": 5,
        "date_start": "2024-01-15T10:00:00Z"
    }
    """
    try:
        # Validation des données d'entrée
        serializer = JobAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Données invalides',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Traitement de l'affectation
        use_case = JobAssignmentUseCase()
        result = use_case.assign_jobs_to_counting(serializer.validated_data)
        
        # Préparation de la réponse
        response_data = {
            'success': result['success'],
            'message': result['message'],
            'assignments_created': result['assignments_created'],
            'counting_order': result['counting_order'],
            'inventory_id': result['inventory_id'],
            'timestamp': timezone.now()
        }
        
        response_serializer = JobAssignmentResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except AssignmentValidationError as e:
        return Response({
            'success': False,
            'message': 'Erreur de validation',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except AssignmentBusinessRuleError as e:
        return Response({
            'success': False,
            'message': 'Règle métier non respectée',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except AssignmentSessionError as e:
        return Response({
            'success': False,
            'message': 'Erreur d\'affectation de session',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except AssignmentNotFoundError as e:
        return Response({
            'success': False,
            'message': 'Ressource non trouvée',
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_rules(request):
    """
    Récupère les règles d'affectation des jobs
    
    GET /api/inventory/assignment-rules/
    """
    try:
        use_case = JobAssignmentUseCase()
        rules = use_case.get_assignment_rules()
        
        serializer = AssignmentRulesSerializer(rules)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Erreur lors de la récupération des règles',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 