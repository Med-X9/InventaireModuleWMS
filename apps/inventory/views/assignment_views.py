from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ..serializers.assignment_serializer import (
    JobAssignmentSerializer,
    JobAssignmentResponseSerializer,
    AssignmentRulesSerializer,
    SessionAssignmentsResponseSerializer,
    AssignmentSerializer,
    JobBasicSerializer
)
from ..serializers.inventory_resource_serializer import (
    AssignResourcesToInventorySerializer,
    AssignResourcesToInventorySimpleSerializer,
    AssignResourcesToInventoryDirectSerializer,
    InventoryResourceDetailSerializer,
    InventoryResourceAssignmentResponseSerializer
)
from ..usecases.job_assignment import JobAssignmentUseCase
from ..services.inventory_resource_service import InventoryResourceService
from ..services.assignment_service import AssignmentService
from ..exceptions.assignment_exceptions import (
    AssignmentValidationError,
    AssignmentBusinessRuleError,
    AssignmentSessionError,
    AssignmentNotFoundError
)
from ..exceptions.inventory_resource_exceptions import (
    InventoryResourceValidationError,
    InventoryResourceBusinessRuleError,
    InventoryResourceNotFoundError
)

class AssignJobsToCountingView(APIView):
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
    permission_classes = [IsAuthenticated]
    
    def post(self, request, inventory_id):
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


class AssignResourcesToInventoryView(APIView):
    """
    Affecte des ressources à un inventaire.
    
    POST /api/inventory/{inventory_id}/assign-resources/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, inventory_id):
        """
        Affecte des ressources à un inventaire.
        
        Args:
            request: Requête HTTP contenant les ressources à affecter
            inventory_id: ID de l'inventaire (dans l'URL)
            
        Returns:
            Response: Résultat de l'affectation des ressources
        """
        try:
            # Valider les données de la requête avec le serializer direct
            serializer = AssignResourcesToInventoryDirectSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': ' | '.join([f"{field}: {', '.join(errors)}" for field, errors in serializer.errors.items()])},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Adapter les données pour le service
            validated_data = serializer.validated_data
            
            # Vérifier si les données sont déjà au bon format ou si elles sont des entiers simples
            first_item = validated_data['resource_assignments'][0] if validated_data['resource_assignments'] else None
            
            if isinstance(first_item, dict) and 'resource_id' in first_item:
                # Les données sont déjà au bon format (objets avec resource_id et quantity)
                adapted_data = {
                    'resource_assignments': validated_data['resource_assignments']
                }
            else:
                # Les données sont des entiers simples, les convertir en objets
                adapted_data = {
                    'resource_assignments': [
                        {'resource_id': resource_id, 'quantity': 1} 
                        for resource_id in validated_data['resource_assignments']
                    ]
                }
            
            # Appeler le service
            service = InventoryResourceService()
            result = service.assign_resources_to_inventory(inventory_id, adapted_data)
            
            # Retourner la réponse
            response_serializer = InventoryResourceAssignmentResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except InventoryResourceValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InventoryResourceNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InventoryResourceBusinessRuleError as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response(
                {'error': f'Erreur interne du serveur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryResourcesView(APIView):
    """
    Récupère toutes les ressources affectées à un inventaire.
    
    GET /api/inventory/{inventory_id}/resources/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id):
        """
        Récupère toutes les ressources affectées à un inventaire.
        
        Args:
            request: Requête HTTP
            inventory_id: ID de l'inventaire (dans l'URL)
            
        Returns:
            Response: Liste des ressources affectées à l'inventaire
        """
        try:
            # Appeler le service
            service = InventoryResourceService()
            inventory_resources = service.get_inventory_resources(inventory_id)
            
            # Sérialiser les données avec le serializer approprié
            serializer = InventoryResourceDetailSerializer(inventory_resources, many=True)
            
            # Retourner la réponse
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except InventoryResourceNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'error': f'Erreur interne du serveur: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionAssignmentsView(APIView):
    """
    Récupère toutes les affectations d'une session (équipe) avec leurs jobs associés
    
    GET /api/inventory/session/<int:session_id>/assignments/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """
        Récupère toutes les affectations d'une session avec leurs jobs
        
        Args:
            request: Requête HTTP
            session_id: ID de la session (équipe)
            
        Returns:
            Response: Liste des affectations avec leurs jobs
        """
        try:
            # Appeler le service
            service = AssignmentService()
            assignments = service.get_assignments_by_session(session_id)
            
            # Si aucune affectation trouvée, retourner une liste vide
            if not assignments:
                return Response({
                    'session_id': session_id,
                    'session_username': None,
                    'jobs': [],
                    'assignments': [],
                    'total_assignments': 0,
                    'total_jobs': 0
                }, status=status.HTTP_200_OK)
            
            # Récupérer les informations de la session depuis la première affectation
            session = assignments[0].session if assignments else None
            session_username = session.username if session else None
            
            # Extraire les jobs uniques des assignments
            jobs_dict = {}
            for assignment in assignments:
                if assignment.job and assignment.job.id not in jobs_dict:
                    jobs_dict[assignment.job.id] = assignment.job
            
            # Sérialiser les jobs et les assignments séparément
            jobs_list = list(jobs_dict.values())
            jobs_data = JobBasicSerializer(jobs_list, many=True).data
            assignments_data = AssignmentSerializer(assignments, many=True).data
            
            # Préparer la réponse
            response_data = {
                'session_id': session_id,
                'session_username': session_username,
                'jobs': jobs_data,
                'assignments': assignments_data,
                'total_assignments': len(assignments),
                'total_jobs': len(jobs_list)
            }
            
            # Valider et retourner la réponse
            response_serializer = SessionAssignmentsResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except AssignmentValidationError as e:
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Erreur interne du serveur',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

