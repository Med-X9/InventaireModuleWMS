from django.db import transaction
from ..repositories.job_repository import JobRepository
from ..exceptions.job_exceptions import JobCreationError
from ..models import Job, JobDetail, Assigment, JobDetailRessource
from django.utils import timezone
from ..interfaces.job_interface import JobServiceInterface
from typing import List, Dict, Any

class JobService(JobServiceInterface):
    """
    Service pour les opérations de gestion des jobs
    Contient la logique métier et utilise le repository pour l'accès aux données
    """
    
    def __init__(self):
        self.repository = JobRepository()
    
    @transaction.atomic
    def create_jobs_for_inventory_warehouse(self, inventory_id, warehouse_id, emplacements):
        """
        Crée un job pour un inventaire et un warehouse avec les emplacements spécifiés
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.repository.get_inventory_by_id(inventory_id)
            if not inventory:
                raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Vérifier que le warehouse existe
            warehouse = self.repository.get_warehouse_by_id(warehouse_id)
            if not warehouse:
                raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
            
            # Vérifier qu'il y a au moins deux comptages pour cet inventaire
            countings = self.repository.get_countings_by_inventory(inventory)
            if len(countings) < 2:
                raise JobCreationError(f"Il faut au moins deux comptages pour l'inventaire {inventory.reference}. Comptages trouvés : {len(countings)}")
            
            # Prendre les deux premiers comptages
            countings_to_use = countings[:2]
            
            # Vérifier que tous les emplacements existent et appartiennent au warehouse
            locations = []
            for emplacement_id in emplacements:
                location = self.repository.get_location_by_id(emplacement_id)
                if not location:
                    raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
                
                # Vérifier que l'emplacement appartient au warehouse via la relation sous_zone.zone.warehouse
                if location.sous_zone.zone.warehouse.id != warehouse_id:
                    raise JobCreationError(f"L'emplacement {location.location_reference} n'appartient pas au warehouse {warehouse.warehouse_name}")
                
                # Vérifier que l'emplacement n'est pas déjà affecté à un autre job pour cet inventaire
                existing_job_detail = self.repository.get_existing_job_detail_by_location_and_inventory(location, inventory)
                if existing_job_detail:
                    raise JobCreationError(f"L'emplacement {location.location_reference} est déjà affecté au job {existing_job_detail.job.reference}")
                
                locations.append(location)
            
            # Créer un seul job pour tous les emplacements
            job = self.repository.create_job(
                reference=Job().generate_reference(Job.REFERENCE_PREFIX),
                status='EN ATTENTE',
                warehouse=warehouse,
                inventory=inventory
            )
            
            # Créer les JobDetail pour tous les emplacements
            for location in locations:
                self.repository.create_job_detail(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    status='EN ATTENTE'
                )
            
            # Créer les assignements pour les deux comptages
            for counting in countings_to_use:
                self.repository.create_assignment(
                    reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    job=job,
                    counting=counting
                )
            
            return [job]
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la création des jobs : {str(e)}")

    def get_pending_jobs_references(self, warehouse_id, filters=None):
        """
        Récupère les jobs en attente pour un warehouse avec filtres optionnels
        """
        try:
            # Vérifier que le warehouse existe
            warehouse = self.repository.get_warehouse_by_id(warehouse_id)
            if not warehouse:
                raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
            
            # Récupérer les jobs en attente pour ce warehouse avec filtres
            return self.repository.get_pending_jobs_by_warehouse_with_filters(warehouse_id, filters)
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la récupération des jobs en attente : {str(e)}")

    @transaction.atomic
    def remove_job_emplacements(self, job_id, emplacement_id):
        """
        Supprime un emplacement d'un job
        """
        try:
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être modifiés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être modifiés. Statut actuel : {job.status}")
            
            # Vérifier que l'emplacement existe dans le job
            existing_job_detail = self.repository.get_job_details_by_job_and_locations(job, [emplacement_id])
            if not existing_job_detail:
                # Si le job n'a aucun emplacement, on peut le supprimer
                job_details = self.repository.get_job_details_by_job(job)
                if not job_details:
                    self.repository.delete_assignments_by_job(job)
                    self.repository.delete_job(job)
                    return {
                        'job_id': job.id,
                        'job_reference': job.reference,
                        'deleted_emplacements_count': 0,
                        'job_deleted': True
                    }
                raise JobCreationError(f"L'emplacement {emplacement_id} n'est pas associé à ce job")
            
            # Supprimer le JobDetail pour l'emplacement spécifié
            deleted_count = self.repository.delete_job_details(existing_job_detail)
            
            # Vérifier s'il reste des emplacements dans le job
            remaining_job_details = self.repository.get_job_details_by_job(job)
            if not remaining_job_details:
                # Supprimer les assignments liés au job
                self.repository.delete_assignments_by_job(job)
                # Supprimer le job
                self.repository.delete_job(job)
                return {
                    'job_id': job.id,
                    'job_reference': job.reference,
                    'deleted_emplacements_count': deleted_count,
                    'job_deleted': True
                }
            
            return {
                'job_id': job.id,
                'job_reference': job.reference,
                'deleted_emplacements_count': deleted_count,
                'job_deleted': False
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la suppression de l'emplacement : {str(e)}")
    @transaction.atomic
    def add_job_emplacements(self, job_id, emplacement_ids):
        """
        Ajoute des emplacements à un job
        """
        try:
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être modifiés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être modifiés. Statut actuel : {job.status}")
            
            # Vérifier que tous les emplacements existent
            for emplacement_id in emplacement_ids:
                location = self.repository.get_location_by_id(emplacement_id)
                if not location:
                    raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
                
                # Vérifier que l'emplacement appartient au warehouse du job via la relation sous_zone.zone.warehouse
                if location.sous_zone.zone.warehouse.id != job.warehouse.id:
                    raise JobCreationError(f"L'emplacement {location.location_reference} n'appartient pas au warehouse {job.warehouse.warehouse_name}")
                
                # Vérifier que l'emplacement n'est pas déjà associé au job actuel
                existing_job_detail = self.repository.get_existing_job_detail_by_location_and_job(location, job)
                if existing_job_detail:
                    raise JobCreationError(f"L'emplacement {location.location_reference} est déjà associé à ce job")
                
                # Vérifier que l'emplacement n'est pas déjà affecté à un autre job pour cet inventaire
                existing_job_detail = self.repository.get_existing_job_detail_by_location_and_inventory_exclude_job(location, job.inventory, job)
                if existing_job_detail:
                    raise JobCreationError(f"L'emplacement {location.location_reference} est déjà affecté au job {existing_job_detail.job.reference}")
            
            # Créer de nouveaux JobDetail pour les emplacements fournis
            created_count = 0
            for emplacement_id in emplacement_ids:
                location = self.repository.get_location_by_id(emplacement_id)
                self.repository.create_job_detail(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    status='EN ATTENTE'
                )
                created_count += 1
            
            return {
                'job_id': job.id,
                'job_reference': job.reference,
                'added_emplacements_count': created_count
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de l'ajout des emplacements : {str(e)}")

    @transaction.atomic
    def delete_job(self, job_id):
        """
        Supprime définitivement un job
        """
        try:
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être supprimés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être supprimés. Statut actuel : {job.status}")
            
            # Récupérer les informations avant suppression pour la réponse
            job_reference = job.reference
            assignments = self.repository.get_assignments_by_job(job)
            assigments_count = len(assignments)
            job_details = self.repository.get_job_details_by_job(job)
            job_details_count = len(job_details)
            
            # Supprimer les Assigment liés au job
            self.repository.delete_assignments_by_job(job)
            
            # Supprimer les JobDetail liés au job
            self.repository.delete_job_details_by_job(job)
            
            # Supprimer le job lui-même
            self.repository.delete_job(job)
            
            return {
                'job_id': job_id,
                'job_reference': job_reference,
                'deleted_assigments_count': assigments_count,
                'deleted_job_details_count': job_details_count
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la suppression du job : {str(e)}")

    @transaction.atomic
    def validate_jobs(self, job_ids):
        """
        Valide des jobs en changeant leur statut de "EN ATTENTE" à "VALIDE"
        """
        try:
            # Vérifier que tous les jobs existent
            jobs = self.repository.get_jobs_by_ids(job_ids)
            found_job_ids = set(job.id for job in jobs)
            requested_job_ids = set(job_ids)
            
            # Identifier les jobs qui n'existent pas
            missing_job_ids = requested_job_ids - found_job_ids
            if missing_job_ids:
                missing_jobs_str = ', '.join(map(str, sorted(missing_job_ids)))
                found_jobs_references = [job.reference for job in jobs]
                found_jobs_str = ', '.join(found_jobs_references) if found_jobs_references else 'Aucun'
                raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}. Jobs trouvés : {found_jobs_str}")
            
            # Vérifier que tous les jobs sont en attente
            non_pending_jobs = [job for job in jobs if job.status != 'EN ATTENTE']
            if non_pending_jobs:
                invalid_jobs = [f"Job {job.reference} (statut: {job.status})" for job in non_pending_jobs]
                raise JobCreationError(f"Seuls les jobs en attente peuvent être validés. Jobs invalides : {', '.join(invalid_jobs)}")
            
            # Mettre à jour le statut et la date de validation
            current_time = timezone.now()
            
            updated_jobs = []
            for job in jobs:
                self.repository.update_job_status(job, 'VALIDE', valide_date=current_time)
                updated_jobs.append({
                    'job_id': job.id,
                    'job_reference': job.reference
                })
            
            return {
                'validated_jobs_count': len(updated_jobs),
                'validated_jobs': updated_jobs,
                'validation_date': current_time
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la validation des jobs : {str(e)}")

    @transaction.atomic
    def make_jobs_ready(self, job_ids):
        """
        Met les jobs affectés au statut "PRET"
        Seuls les jobs avec le statut "AFFECTE" peuvent être mis au statut "PRET"
        Note: Le statut AFFECTE est géré dans le modèle Assigment, pas dans Job
        """
        try:
            # Vérifier que tous les jobs existent
            jobs = self.repository.get_jobs_by_ids(job_ids)
            found_job_ids = set(job.id for job in jobs)
            requested_job_ids = set(job_ids)
            
            # Identifier les jobs qui n'existent pas
            missing_job_ids = requested_job_ids - found_job_ids
            if missing_job_ids:
                missing_jobs_str = ', '.join(map(str, sorted(missing_job_ids)))
                found_jobs_references = [job.reference for job in jobs]
                found_jobs_str = ', '.join(found_jobs_references) if found_jobs_references else 'Aucun'
                raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}. Jobs trouvés : {found_jobs_str}")
            
            # Vérifier que tous les jobs ont des affectations avec statut AFFECTE
            from ..models import Assigment
            non_assigned_jobs = []
            for job in jobs:
                assignments = Assigment.objects.filter(job=job, status='AFFECTE')
                if not assignments.exists():
                    non_assigned_jobs.append(job)
            
            if non_assigned_jobs:
                invalid_jobs = [f"Job {job.reference} (pas d'affectation AFFECTE)" for job in non_assigned_jobs]
                raise JobCreationError(f"Seuls les jobs affectés peuvent être mis au statut PRET. Jobs invalides : {', '.join(invalid_jobs)}")
            
            # Mettre à jour le statut des affectations à PRET
            current_time = timezone.now()
            
            updated_jobs = []
            for job in jobs:
                # Mettre à jour toutes les affectations du job au statut PRET
                assignments = Assigment.objects.filter(job=job)
                for assignment in assignments:
                    assignment.status = 'PRET'
                    assignment.pret_date = current_time
                    assignment.save()
                
                updated_jobs.append({
                    'job_id': job.id,
                    'job_reference': job.reference
                })
            
            return {
                'ready_jobs_count': len(updated_jobs),
                'ready_jobs': updated_jobs,
                'ready_date': current_time
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la mise en prêt des jobs : {str(e)}")

    def get_jobs_by_warehouse(self, warehouse_id, filters=None):
        """
        Récupère les jobs d'un warehouse avec filtres optionnels
        """
        try:
            return self.repository.get_jobs_with_filters(warehouse_id, filters)
        except Exception as e:
            raise JobCreationError(f"Erreur lors de la récupération des jobs du warehouse : {str(e)}")

    def get_job_by_id(self, job_id):
        """
        Récupère un job par son ID
        """
        return self.repository.get_job_by_id(job_id)

    def get_jobs_by_inventory(self, inventory_id):
        """
        Récupère tous les jobs d'un inventaire
        """
        try:
            return self.repository.get_jobs_by_inventory(inventory_id)
        except Exception as e:
            raise JobCreationError(f"Erreur lors de la récupération des jobs de l'inventaire : {str(e)}")

    @transaction.atomic
    def delete_multiple_jobs(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime définitivement plusieurs jobs dans une transaction
        Si un seul job ne peut pas être supprimé, toute l'opération est annulée
        """
        try:
            results = []
            for job_id in job_ids:
                result = self.delete_job(job_id)
                results.append({
                    'job_id': job_id,
                    'success': True,
                    'data': result
                })
            
            return {
                'success': True,
                'message': f'{len(results)} jobs supprimés avec succès',
                'results': results
            }
            
        except JobCreationError:
            # Si une erreur survient, la transaction est automatiquement annulée
            raise
        except Exception as e:
            # Si une erreur inattendue survient, la transaction est automatiquement annulée
            raise JobCreationError(f"Erreur inattendue lors de la suppression des jobs : {str(e)}")

    @transaction.atomic
    def make_jobs_ready_by_jobs_and_orders(self, job_ids: list, orders: list):
        """
        Met les assignements (job, counting) au statut PRET pour les jobs et ordres de comptage donnés
        Si un assignement existe mais n'est pas au statut 'AFFECTE', lever une exception explicite.
        """
        from ..models import Assigment, Counting
        current_time = timezone.now()
        updated_assignments = []
        for job_id in job_ids:
            for order in orders:
                assignment = Assigment.objects.select_related('counting').filter(job_id=job_id, counting__order=order).first()
                if not assignment:
                    raise JobCreationError(f"Aucune assignation trouvée pour le job {job_id} et le comptage d'ordre {order}.")
                if assignment.status == 'PRET':
                    raise JobCreationError(f"Le job {job_id} pour le comptage d'ordre {order} est déjà au statut PRET.")
                if assignment.status != 'AFFECTE':
                    raise JobCreationError(f"Le job {job_id} pour le comptage d'ordre {order} n'est pas au statut AFFECTE (statut actuel : {assignment.status}).")
                assignment.status = 'PRET'
                assignment.pret_date = current_time
                assignment.save()
                updated_assignments.append({'job_id': job_id, 'order': order, 'assignment_id': assignment.id})
        return {
            'updated_assignments': updated_assignments,
            'ready_date': current_time
        }

    @transaction.atomic
    def reset_jobs_assignments(self, job_ids: list):
        """
        Remet les assignements de plusieurs jobs en attente :
        - Met le statut des jobs à 'EN ATTENTE'
        - Vide les dates des autres statuts du job (valide_date, termine_date)
        - Supprime les affectations de session
        - Met le statut des assignements à 'EN ATTENTE'
        - Vide toutes les dates des assignements
        - Supprime tous les JobDetailRessource des jobs
        """
        from ..models import Assigment, JobDetailRessource
        
        # Vérifier que tous les jobs existent
        jobs = self.repository.get_jobs_by_ids(job_ids)
        found_job_ids = set(job.id for job in jobs)
        requested_job_ids = set(job_ids)
        
        # Identifier les jobs qui n'existent pas
        missing_job_ids = requested_job_ids - found_job_ids
        if missing_job_ids:
            missing_jobs_str = ', '.join(map(str, sorted(missing_job_ids)))
            raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}")
        
        # Mettre à jour le statut des jobs et vider les dates
        for job in jobs:
            job.status = 'EN ATTENTE'
            job.valide_date = None
            job.termine_date = None
            job.save()
        
        # Récupérer tous les assignements des jobs
        assignments = Assigment.objects.filter(job__in=jobs)
        
        # Mettre à jour tous les assignements
        updated_count = 0
        for assignment in assignments:
            assignment.session = None
            assignment.status = 'EN ATTENTE'
            # Vider toutes les dates
            assignment.affecte_date = None
            assignment.pret_date = None
            assignment.transfert_date = None
            assignment.entame_date = None
            assignment.save()
            updated_count += 1
        
        # Supprimer tous les JobDetailRessource des jobs
        ressources_deleted = JobDetailRessource.objects.filter(job__in=jobs).delete()[0]
        
        return {
            'jobs_processed': len(jobs),
            'assignments_reset': updated_count,
            'ressources_deleted': ressources_deleted,
            'message': f'Jobs et assignements remis en attente pour {len(jobs)} jobs, {ressources_deleted} ressources supprimées'
        } 