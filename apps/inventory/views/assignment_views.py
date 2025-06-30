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
def assign_jobs_to_counting(request, inventory_id):
    """
    Affecte des jobs à un comptage spécifique
    
    POST /api/inventory/{inventory_id}/assign-jobs/
    
    Body:
    {
        "job_ids": [1, 2, 3],
        "counting_order": 1,
        "session_id": 5,
        "date_start": "2024-01-15T10:00:00Z"
    }
    """
    try:
        # Ajouter l'ID de l'inventaire aux données de la requête
        request_data = request.data.copy()
        request_data['inventory_id'] = inventory_id
        
        # Validation des données d'entrée
        serializer = JobAssignmentSerializer(data=request_data)
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
            'assignments_updated': result['assignments_updated'],
            'total_assignments': result['total_assignments'],
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignments_by_session(request, session_id):
    """
    Récupère toutes les affectations d'une session
    
    GET /api/inventory/session/{session_id}/assignments/
    """
    try:
        from ..repositories.assignment_repository import AssignmentRepository
        
        repository = AssignmentRepository()
        assignments = repository.get_assignments_by_session(session_id)
        
        # Préparer les données de réponse
        assignments_data = []
        for assignment in assignments:
            assignments_data.append({
                'id': assignment.id,
                'reference': assignment.reference,
                'job_id': assignment.job.id,
                'job_reference': assignment.job.reference,
                'counting_id': assignment.counting.id,
                'counting_order': assignment.counting.order,
                'counting_mode': assignment.counting.count_mode,
                'date_start': assignment.date_start,
                'session_id': assignment.session.id if assignment.session else None,
                'session_username': assignment.session.username if assignment.session else None,
                'created_at': assignment.created_at,
                'updated_at': assignment.updated_at
            })
        
        return Response({
            'success': True,
            'session_id': session_id,
            'assignments_count': len(assignments_data),
            'assignments': assignments_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Erreur lors de la récupération des affectations',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 