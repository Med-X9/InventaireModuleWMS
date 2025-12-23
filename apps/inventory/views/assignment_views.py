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
from ..utils.response_utils import success_response, error_response, validation_error_response
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
        "counting_order": 1,  // Peut être 1, 2, 3, 4, 5, etc.
        "session_id": 5,
        "date_start": "2024-01-15T10:00:00Z"
    }
    
    Comportement :
    - Si l'assignment existe déjà et est au statut ENTAME, il sera mis en TRANSFERT lors de l'affectation
    - Les autres statuts (PRET, TRANSFERT, TERMINE, etc.) restent inchangés
    - La session et la date_start sont mises à jour
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
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation lors de l'affectation des jobs"
                )
            
            # Traitement de l'affectation
            use_case = JobAssignmentUseCase()
            result = use_case.assign_jobs_to_counting(serializer.validated_data)
            
            # Préparation de la réponse
            response_data = {
                'assignments_created': result['assignments_created'],
                'assignments_updated': result['assignments_updated'],
                'total_assignments': result['total_assignments'],
                'counting_order': result['counting_order'],
                'timestamp': timezone.now()
            }
            
            return success_response(
                data=response_data,
                message=result['message'],
                status_code=status.HTTP_201_CREATED
            )
            
        except AssignmentValidationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except AssignmentBusinessRuleError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except AssignmentSessionError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except AssignmentNotFoundError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            return error_response(
                message="Une erreur inattendue s'est produite lors de l'affectation",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                return success_response(
                    data={
                        'session_id': session_id,
                        'session_username': None,
                        'jobs': [],
                        'total_jobs': 0
                    },
                    message="Aucune affectation trouvée pour cette session"
                )
            
            # Récupérer les informations de la session depuis la première affectation
            session = assignments[0].session if assignments else None
            session_username = session.username if session else None
            
            # Extraire les jobs uniques des assignments (utiliser les références)
            jobs_dict = {}
            for assignment in assignments:
                if assignment.job and assignment.job.reference not in jobs_dict:
                    jobs_dict[assignment.job.reference] = assignment.job
            
            # Sérialiser les jobs uniquement (sans les assignments)
            jobs_list = list(jobs_dict.values())
            jobs_data = JobBasicSerializer(jobs_list, many=True).data
            
            # Préparer la réponse avec uniquement les références des jobs
            response_data = {
                'session_id': session_id,
                'session_username': session_username,
                'jobs': jobs_data,
                'total_jobs': len(jobs_list)
            }
            
            return success_response(
                data=response_data,
                message="Affectations récupérées avec succès"
            )
            
        except AssignmentValidationError as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return error_response(
                message="Une erreur inattendue s'est produite",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssignJobsToBothCountingsView(APIView):
    """
    Affecte des jobs aux comptages 1 et 2 avec des sessions spécifiques.
    Crée des assignments avec statut PRET pour les deux comptages.
    
    POST /api/inventory/assign-jobs-both-countings/
    
    Body:
    {
        "job_ids": [1, 2, 3],
        "session_id_1": 5,  // Session pour le comptage 1 (optionnel)
        "session_id_2": 6   // Session pour le comptage 2 (optionnel)
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Affecte des jobs aux comptages 1 et 2 avec des sessions spécifiques.
        Crée des assignments avec statut PRET.
        
        Args:
            request: Requête HTTP contenant job_ids, session_id_1, session_id_2
            
        Returns:
            Response: Résultat de l'affectation
        """
        try:
            from ..models import Job, Counting, Assigment
            from apps.users.models import UserApp
            from django.db import transaction
            
            # Validation des données
            job_ids = request.data.get('job_ids', [])
            session_id_1 = request.data.get('session_id_1')
            session_id_2 = request.data.get('session_id_2')
            
            if not job_ids:
                return error_response(
                    message="La liste des IDs des jobs est obligatoire",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not isinstance(job_ids, list):
                return error_response(
                    message="job_ids doit être une liste",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que les sessions existent si fournies
            session_1 = None
            session_2 = None
            
            if session_id_1:
                try:
                    session_1 = UserApp.objects.get(id=session_id_1, type='Mobile', is_active=True)
                except UserApp.DoesNotExist:
                    return error_response(
                        message=f"Session avec l'ID {session_id_1} non trouvée (type Mobile)",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            
            if session_id_2:
                try:
                    session_2 = UserApp.objects.get(id=session_id_2, type='Mobile', is_active=True)
                except UserApp.DoesNotExist:
                    return error_response(
                        message=f"Session avec l'ID {session_id_2} non trouvée (type Mobile)",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            
            # Récupérer les jobs
            jobs = Job.objects.filter(id__in=job_ids)
            if jobs.count() != len(job_ids):
                found_ids = set(jobs.values_list('id', flat=True))
                missing_ids = set(job_ids) - found_ids
                return error_response(
                    message=f"Jobs non trouvés: {missing_ids}",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Vérifier que tous les jobs appartiennent au même inventaire
            inventory_ids = set(job.inventory_id for job in jobs)
            if len(inventory_ids) != 1:
                return error_response(
                    message="Tous les jobs doivent appartenir au même inventaire",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            inventory_id = list(inventory_ids)[0]
            
            # Récupérer les comptages 1 et 2
            counting_1 = Counting.objects.filter(inventory_id=inventory_id, order=1).first()
            counting_2 = Counting.objects.filter(inventory_id=inventory_id, order=2).first()
            
            if not counting_1:
                return error_response(
                    message=f"Comptage d'ordre 1 non trouvé pour l'inventaire {inventory_id}",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if not counting_2:
                return error_response(
                    message=f"Comptage d'ordre 2 non trouvé pour l'inventaire {inventory_id}",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Créer les assignments avec statut PRET
            assignments_created_1 = []
            assignments_created_2 = []
            assignments_updated_1 = []
            assignments_updated_2 = []
            current_time = timezone.now()
            
            with transaction.atomic():
                for job in jobs:
                    # Assignment pour le comptage 1
                    if session_id_1:
                        assignment_1, created_1 = Assigment.objects.get_or_create(
                            job=job,
                            counting=counting_1,
                            defaults={
                                'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                                'session': session_1,
                                'status': 'PRET',
                                'pret_date': current_time,
                                'affecte_date': current_time,
                                'date_start': current_time
                            }
                        )
                        
                        if not created_1:
                            # Mettre à jour l'assignment existant
                            assignment_1.session = session_1
                            assignment_1.status = 'PRET'
                            assignment_1.pret_date = current_time
                            assignment_1.affecte_date = current_time
                            assignment_1.date_start = current_time
                            assignment_1.save()
                            assignments_updated_1.append(assignment_1.id)
                        else:
                            assignments_created_1.append(assignment_1.id)
                    
                    # Assignment pour le comptage 2
                    if session_id_2:
                        assignment_2, created_2 = Assigment.objects.get_or_create(
                            job=job,
                            counting=counting_2,
                            defaults={
                                'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                                'session': session_2,
                                'status': 'PRET',
                                'pret_date': current_time,
                                'affecte_date': current_time,
                                'date_start': current_time
                            }
                        )
                        
                        if not created_2:
                            # Mettre à jour l'assignment existant
                            assignment_2.session = session_2
                            assignment_2.status = 'PRET'
                            assignment_2.pret_date = current_time
                            assignment_2.affecte_date = current_time
                            assignment_2.date_start = current_time
                            assignment_2.save()
                            assignments_updated_2.append(assignment_2.id)
                        else:
                            assignments_created_2.append(assignment_2.id)
            
            # Préparer la réponse
            response_data = {
                'assignments_created_counting_1': len(assignments_created_1),
                'assignments_updated_counting_1': len(assignments_updated_1),
                'assignments_created_counting_2': len(assignments_created_2),
                'assignments_updated_counting_2': len(assignments_updated_2),
                'total_jobs': len(jobs),
                'inventory_id': inventory_id,
                'counting_1_order': 1,
                'counting_2_order': 2,
                'session_1_id': session_id_1,
                'session_2_id': session_id_2,
                'timestamp': current_time
            }
            
            return success_response(
                data=response_data,
                message=f"Affectation réussie : {len(assignments_created_1) + len(assignments_created_2)} assignments créés, "
                       f"{len(assignments_updated_1) + len(assignments_updated_2)} assignments mis à jour",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return error_response(
                message=f"Une erreur inattendue s'est produite: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AutoAssignJobsFromInventoryLocationJobView(APIView):
    """
    Affectation automatique des jobs à partir de la table InventoryLocationJob
    
    POST /api/inventory/{inventory_id}/auto-assign-jobs-from-location-jobs/
    
    Cette API :
    1. Récupère tous les InventoryLocationJob pour l'inventaire donné
    2. Extrait les équipes uniques de session_1 et session_2
    3. Vérifie que les équipes existent dans UserApp (type='Mobile')
    4. Vérifie que les équipes ne sont pas déjà affectées à un inventaire GENERAL en cours
    5. Applique l'affectation automatique avec transaction atomique (tout ou rien)
    6. Trouve les Jobs correspondants par référence
    7. Crée les assignments pour les comptages 1 et 2 avec le statut AFFECTE
    8. Met à jour le statut des jobs à AFFECTE
    
    Logique "tout ou rien" : Si une seule équipe échoue la validation, toute l'opération est annulée
    
    Comportement :
    - Les assignments sont créés avec le statut AFFECTE
    - Les jobs sont mis à jour au statut AFFECTE (sauf s'ils sont déjà à un statut avancé)
    - Si un assignment est ENTAME, il est mis en TRANSFERT lors de la réaffectation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, inventory_id):
        try:
            from ..models import Job, Counting, Assigment, Inventory
            from apps.users.models import UserApp
            from apps.masterdata.models import InventoryLocationJob
            from django.db import transaction
            
            # Liste pour collecter toutes les erreurs
            errors = []
            
            # Vérifier que l'inventaire existe
            try:
                inventory = Inventory.objects.get(id=inventory_id)
            except Inventory.DoesNotExist:
                errors.append(f"Inventaire avec l'ID {inventory_id} non trouvé")
                return error_response(
                    message="Erreurs de validation",
                    errors=errors,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Récupérer tous les InventoryLocationJob pour cet inventaire
            location_jobs = InventoryLocationJob.objects.filter(
                inventaire_id=inventory_id,
                is_deleted=False
            ).select_related('inventaire', 'emplacement')
            
            if not location_jobs.exists():
                errors.append(f"Aucun InventoryLocationJob trouvé pour l'inventaire {inventory_id}")
                return error_response(
                    message="Erreurs de validation",
                    errors=errors,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Extraire toutes les équipes uniques de session_1 et session_2
            teams_set = set()
            for location_job in location_jobs:
                if location_job.session_1:
                    teams_set.add(location_job.session_1.strip())
                if location_job.session_2:
                    teams_set.add(location_job.session_2.strip())
            
            if not teams_set:
                errors.append("Aucune équipe trouvée dans les InventoryLocationJob")
            
            # Vérifier que toutes les équipes existent dans UserApp (type='Mobile')
            teams_list = list(teams_set) if teams_set else []
            if teams_list:
                existing_teams = UserApp.objects.filter(
                    username__in=teams_list,
                    type='Mobile',
                    is_active=True
                ).values_list('username', flat=True)
                
                existing_teams_set = set(existing_teams)
                missing_teams = teams_set - existing_teams_set
                
                if missing_teams:
                    errors.append(f"Équipes non trouvées dans UserApp (type Mobile) : {', '.join(sorted(missing_teams))}")
            
            # Récupérer les comptages 1 et 2 pour cet inventaire
            counting_1 = Counting.objects.filter(inventory_id=inventory_id, order=1).first()
            counting_2 = Counting.objects.filter(inventory_id=inventory_id, order=2).first()
            
            if not counting_1:
                errors.append(f"Comptage d'ordre 1 non trouvé pour l'inventaire {inventory_id}")
            
            if not counting_2:
                errors.append(f"Comptage d'ordre 2 non trouvé pour l'inventaire {inventory_id}")
            
            # Vérifier que les équipes ne sont pas déjà affectées à un inventaire GENERAL en cours
            # Un inventaire en cours = status != 'TERMINE' et status != 'CLOTURE'
            if teams_list:
                active_general_inventories = Inventory.objects.filter(
                    inventory_type='GENERAL',
                    status__in=['EN PREPARATION', 'EN REALISATION']
                ).exclude(id=inventory_id)
                
                if active_general_inventories.exists():
                    # Vérifier les assignments pour ces inventaires
                    conflicting_assignments = Assigment.objects.filter(
                        session__username__in=teams_list,
                        job__inventory__in=active_general_inventories
                    ).select_related('session', 'job__inventory')
                    
                    if conflicting_assignments.exists():
                        # Grouper par équipe et inventaire
                        conflicts_by_team = {}
                        for assignment in conflicting_assignments:
                            team_username = assignment.session.username
                            inv_ref = assignment.job.inventory.reference
                            if team_username not in conflicts_by_team:
                                conflicts_by_team[team_username] = set()
                            conflicts_by_team[team_username].add(inv_ref)
                        
                        # Ajouter les erreurs de conflit
                        for team, inv_refs in conflicts_by_team.items():
                            errors.append(
                                f"Équipe '{team}' déjà affectée à l'inventaire GENERAL en cours : {', '.join(sorted(inv_refs))}"
                            )
            
            # Grouper les location_jobs par référence de job
            jobs_by_reference = {}
            for location_job in location_jobs:
                if location_job.job:
                    job_ref = location_job.job.strip()
                    if job_ref not in jobs_by_reference:
                        jobs_by_reference[job_ref] = []
                    jobs_by_reference[job_ref].append(location_job)
            
            # Trouver les Jobs correspondants par référence
            job_references = list(jobs_by_reference.keys())
            if job_references:
                jobs = Job.objects.filter(
                    reference__in=job_references,
                    inventory_id=inventory_id
                )
                
                jobs_by_ref_dict = {job.reference: job for job in jobs}
                missing_job_refs = set(job_references) - set(jobs_by_ref_dict.keys())
                
                if missing_job_refs:
                    errors.append(f"Jobs non trouvés pour les références : {', '.join(sorted(missing_job_refs))}")
            else:
                jobs_by_ref_dict = {}
            
            # Si des erreurs ont été collectées, les retourner toutes
            if errors:
                return error_response(
                    message="Erreurs de validation détectées",
                    errors=errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer les UserApp correspondants (si pas d'erreurs)
            teams_userapp = {
                team.username: team 
                for team in UserApp.objects.filter(
                    username__in=teams_list,
                    type='Mobile',
                    is_active=True
                )
            }
            
            # Appliquer l'affectation avec transaction atomique (tout ou rien)
            assignments_created_1 = []
            assignments_created_2 = []
            assignments_updated_1 = []
            assignments_updated_2 = []
            current_time = timezone.now()
            
            with transaction.atomic():
                # Parcourir chaque job et créer/mettre à jour les assignments
                for job_ref, location_jobs_list in jobs_by_reference.items():
                    job = jobs_by_ref_dict[job_ref]
                    
                    # Pour chaque location_job, utiliser session_1 et session_2
                    # Si plusieurs location_jobs ont le même job, on prend les sessions du premier
                    # (selon la logique, normalement un job devrait avoir les mêmes sessions pour tous ses emplacements)
                    first_location_job = location_jobs_list[0]
                    
                    # Assignment pour le comptage 1 avec session_1
                    if first_location_job.session_1:
                        session_1_username = first_location_job.session_1.strip()
                        session_1_userapp = teams_userapp.get(session_1_username)
                        
                        if session_1_userapp:
                            assignment_1, created_1 = Assigment.objects.get_or_create(
                                job=job,
                                counting=counting_1,
                                defaults={
                                    'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                                    'session': session_1_userapp,
                                    'status': 'AFFECTE',
                                    'affecte_date': current_time,
                                    'date_start': current_time
                                }
                            )
                            
                            if not created_1:
                                # Mettre à jour l'assignment existant
                                # Si l'assignment est ENTAME, le mettre en TRANSFERT
                                if assignment_1.status == 'ENTAME':
                                    assignment_1.status = 'TRANSFERT'
                                    assignment_1.transfert_date = current_time
                                else:
                                    assignment_1.status = 'AFFECTE'
                                
                                assignment_1.session = session_1_userapp
                                assignment_1.affecte_date = current_time
                                assignment_1.date_start = current_time
                                assignment_1.save()
                                assignments_updated_1.append(assignment_1.id)
                            else:
                                assignments_created_1.append(assignment_1.id)
                    
                    # Assignment pour le comptage 2 avec session_2
                    if first_location_job.session_2:
                        session_2_username = first_location_job.session_2.strip()
                        session_2_userapp = teams_userapp.get(session_2_username)
                        
                        if session_2_userapp:
                            assignment_2, created_2 = Assigment.objects.get_or_create(
                                job=job,
                                counting=counting_2,
                                defaults={
                                    'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                                    'session': session_2_userapp,
                                    'status': 'AFFECTE',
                                    'affecte_date': current_time,
                                    'date_start': current_time
                                }
                            )
                            
                            if not created_2:
                                # Mettre à jour l'assignment existant
                                # Si l'assignment est ENTAME, le mettre en TRANSFERT
                                if assignment_2.status == 'ENTAME':
                                    assignment_2.status = 'TRANSFERT'
                                    assignment_2.transfert_date = current_time
                                else:
                                    assignment_2.status = 'AFFECTE'
                                
                                assignment_2.session = session_2_userapp
                                assignment_2.affecte_date = current_time
                                assignment_2.date_start = current_time
                                assignment_2.save()
                                assignments_updated_2.append(assignment_2.id)
                            else:
                                assignments_created_2.append(assignment_2.id)
                    
                    # Mettre à jour le statut du job à AFFECTE
                    # Ne pas modifier si le job est déjà dans un statut avancé
                    preserved_job_statuses = ['PRET', 'TRANSFERT', 'ENTAME', 'TERMINE', 'SAISIE MANUELLE']
                    if job.status not in preserved_job_statuses:
                        job.status = 'AFFECTE'
                        job.affecte_date = current_time
                        job.save()
            
            # Préparer la réponse
            response_data = {
                'assignments_created_counting_1': len(assignments_created_1),
                'assignments_updated_counting_1': len(assignments_updated_1),
                'assignments_created_counting_2': len(assignments_created_2),
                'assignments_updated_counting_2': len(assignments_updated_2),
                'total_jobs': len(jobs_by_ref_dict),
                'total_teams': len(teams_set),
                'teams': sorted(list(teams_set)),
                'inventory_id': inventory_id,
                'inventory_reference': inventory.reference,
                'counting_1_order': 1,
                'counting_2_order': 2,
                'timestamp': current_time
            }
            
            return success_response(
                data=response_data,
                message=f"Affectation automatique réussie : {len(assignments_created_1) + len(assignments_created_2)} assignments créés, "
                       f"{len(assignments_updated_1) + len(assignments_updated_2)} assignments mis à jour pour {len(jobs_by_ref_dict)} jobs",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            import traceback
            return error_response(
                message=f"Une erreur inattendue s'est produite: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
