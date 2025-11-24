from django.db import transaction
from ..repositories.job_repository import JobRepository
from ..exceptions.job_exceptions import JobCreationError
from ..models import Job, JobDetail, Assigment, JobDetailRessource, CountingDetail, Counting
from django.utils import timezone
from ..interfaces.job_interface import JobServiceInterface
from typing import List, Dict, Any
from django.db.models import Q, Count, Case, When, IntegerField

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
            counting1 = countings_to_use[0]  # 1er comptage
            counting2 = countings_to_use[1]  # 2ème comptage
            
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
            # La référence sera générée automatiquement par la méthode save() du modèle
            job = self.repository.create_job(
                status='EN ATTENTE',
                en_attente_date=timezone.now(),
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
            
            # Créer les assignements selon la configuration des comptages
            if counting1.count_mode == "image de stock":
                # Cas spécial : 1er comptage = image de stock
                # Créer seulement l'affectation pour le 2ème comptage (sans session)
                self.repository.create_assignment(
                    reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    job=job,
                    counting=counting2,
                    status='EN ATTENTE'  # Statut initial sans session
                )
            else:
                # Cas normal : Créer les affectations pour les deux comptages
                for counting in countings_to_use:
                    self.repository.create_assignment(
                        reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                        job=job,
                        counting=counting,
                        status='EN ATTENTE'
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
            
            # Vérifier que l'emplacement existe
            location = self.repository.get_location_by_id(emplacement_id)
            if not location:
                raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
            
            # Vérifier que l'emplacement appartient au job
            job_detail = self.repository.get_job_detail_by_job_and_location(job, location)
            if not job_detail:
                raise JobCreationError(f"L'emplacement {location.location_reference} n'appartient pas au job {job.reference}")
            
            # Supprimer le job detail
            self.repository.delete_job_detail(job_detail)
            
            return {
                'success': True,
                'message': f"Emplacement {location.location_reference} supprimé du job {job.reference}",
                'job_id': job_id,
                'emplacement_id': emplacement_id
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
            
            # Vérifier que tous les emplacements existent
            locations = []
            for emplacement_id in emplacement_ids:
                location = self.repository.get_location_by_id(emplacement_id)
                if not location:
                    raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
                
                # Vérifier que l'emplacement n'est pas déjà affecté à un autre job pour cet inventaire
                existing_job_detail = self.repository.get_existing_job_detail_by_location_and_inventory(location, job.inventory)
                if existing_job_detail and existing_job_detail.job.id != job_id:
                    raise JobCreationError(f"L'emplacement {location.location_reference} est déjà affecté au job {existing_job_detail.job.reference}")
                
                locations.append(location)
            
            # Créer les JobDetail pour tous les emplacements
            created_count = 0
            for location in locations:
                # Vérifier si l'emplacement n'est pas déjà dans le job
                existing_job_detail = self.repository.get_job_detail_by_job_and_location(job, location)
                if not existing_job_detail:
                    self.repository.create_job_detail(
                        reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                        location=location,
                        job=job,
                        status='EN ATTENTE'
                    )
                    created_count += 1
            
            return {
                'success': True,
                'message': f"{created_count} emplacements ajoutés au job {job.reference}",
                'job_id': job_id,
                'emplacements_added': created_count
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
            assignments_count = len(assignments)
            job_details = self.repository.get_job_details_by_job(job)
            job_details_count = len(job_details)
            
            # Supprimer les Assigment liés au job
            self.repository.delete_assignments_by_job(job)
            
            # Supprimer les JobDetail liés au job
            self.repository.delete_job_details_by_job(job)
            
            # Supprimer le job lui-même
            self.repository.delete_job(job)
            
            return {
                'success': True,
                'job_id': job_id,
                'job_reference': job_reference,
                'deleted_assignments_count': assignments_count,
                'deleted_job_details_count': job_details_count,
                'message': f"Job {job_reference} supprimé avec succès"
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de la suppression du job : {str(e)}")

    @transaction.atomic
    def validate_jobs(self, job_ids):
        """
        Valide les jobs en attente
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
                raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}")
            
            # Vérifier que tous les jobs ont le statut EN ATTENTE
            invalid_jobs = []
            for job in jobs:
                if job.status != 'EN ATTENTE':
                    invalid_jobs.append(f"Job {job.reference} (statut: {job.status})")
            
            if invalid_jobs:
                raise JobCreationError(
                    f"Seuls les jobs avec le statut EN ATTENTE peuvent être validés. "
                    f"Jobs invalides : {', '.join(invalid_jobs)}"
                )
            
            # Valider les jobs
            current_time = timezone.now()
            validated_jobs = []
            
            for job in jobs:
                job.status = 'VALIDE'
                job.valide_date = current_time
                job.save()
                
                validated_jobs.append({
                    'job_id': job.id,
                    'job_reference': job.reference
                })
            
            return {
                'success': True,
                'validated_jobs_count': len(validated_jobs),
                'validated_jobs': validated_jobs,
                'validation_date': current_time,
                'message': f'{len(validated_jobs)} jobs validés'
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
        updated_jobs = []
        for job_id in job_ids:
            job = Job.objects.filter(id=job_id).first()
            if not job:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé.")
            job_reference = job.reference
            
            for order in orders:
                assignment = Assigment.objects.select_related('counting').filter(job_id=job_id, counting__order=order).first()
                if not assignment:
                    raise JobCreationError(f"Aucune assignation trouvée pour le job {job_reference} et le comptage d'ordre {order}.")
                if assignment.status == 'PRET':
                    raise JobCreationError(f"Le job {job_reference} pour le comptage d'ordre {order} est déjà au statut PRET.")
                if assignment.status != 'AFFECTE':
                    raise JobCreationError(f"Le job {job_reference} pour le comptage d'ordre {order} n'est pas au statut AFFECTE (statut actuel : {assignment.status}).")
                assignment.status = 'PRET'
                assignment.pret_date = current_time
                assignment.save()
            
            # Ajouter le job une seule fois avec ses informations
            if not any(j.get('job_reference') == job_reference for j in updated_jobs):
                updated_jobs.append({
                    'job_reference': job_reference,
                    'counting_orders': [order for order in orders]
                })
        
        return {
            'updated_jobs': updated_jobs,
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
            'jobs_reset': len(jobs),
            'assignments_reset': updated_count,
            'ressources_deleted': ressources_deleted
        }

    @transaction.atomic
    def transfer_jobs_by_counting_order(self, job_ids: list, counting_order: int):
        """
        Transfère les jobs qui sont au statut PRET vers le statut TRANSFERT pour un ordre de comptage spécifique.
        
        Args:
            job_ids: Liste des IDs des jobs à transférer
            counting_order: Ordre du comptage pour lequel transférer les jobs
            
        Returns:
            Dict contenant les informations sur les jobs transférés
        """
        from ..models import Assigment, Counting
        
        current_time = timezone.now()
        transferred_jobs = []
        errors = []
        
        # Vérifier que le comptage existe
        counting = Counting.objects.filter(order=counting_order).first()
        if not counting:
            raise JobCreationError(f"Aucun comptage trouvé avec l'ordre {counting_order}")
        
        for job_id in job_ids:
            # Récupérer le job pour obtenir sa référence
            job = Job.objects.filter(id=job_id).first()
            if not job:
                errors.append(f"Job avec l'ID {job_id} non trouvé")
                continue
            job_reference = job.reference
            
            # Récupérer l'assignement pour ce job et cet ordre de comptage
            assignment = Assigment.objects.select_related('job', 'counting').filter(
                job_id=job_id, 
                counting__order=counting_order
            ).first()
            
            if not assignment:
                errors.append(f"Aucune assignation trouvée pour le job {job_reference} et le comptage d'ordre {counting_order}")
                continue
                
            # Vérifier que l'assignement est au statut PRET
            if assignment.status != 'PRET':
                errors.append(f"Le job {job_reference} pour le comptage d'ordre {counting_order} n'est pas au statut PRET (statut actuel : {assignment.status})")
                continue
            
            # Transférer l'assignement
            assignment.status = 'TRANSFERT'
            assignment.transfert_date = current_time
            assignment.save()
            
            # Transférer le job lui-même
            job.status = 'TRANSFERT'
            job.transfert_date = current_time
            job.save()
            
            # Ajouter le job une seule fois avec ses informations
            if not any(j.get('job_reference') == job.reference for j in transferred_jobs):
                transferred_jobs.append({
                    'job_reference': job.reference,
                    'counting_order': counting_order,
                    'counting_reference': assignment.counting.reference
                })
        
        # Si des erreurs ont été collectées, les lever
        if errors:
            error_message = " | ".join(errors)
            raise JobCreationError(f"Erreurs lors du transfert : {error_message}")
        
        return {
            'transferred_jobs': transferred_jobs,
            'transfer_date': current_time,
            'counting_order': counting_order,
            'total_transferred': len(transferred_jobs)
        }
    
    @transaction.atomic
    def transfer_jobs_by_counting_orders(self, job_ids: list, counting_orders: list):
        """
        Transfère les jobs qui sont au statut PRET vers le statut TRANSFERT pour plusieurs ordres de comptage.
        
        Args:
            job_ids: Liste des IDs des jobs à transférer
            counting_orders: Liste des ordres de comptage pour lesquels transférer les jobs
            
        Returns:
            Dict contenant les informations sur les jobs transférés
        """
        from ..models import Assigment, Counting
        
        current_time = timezone.now()
        transferred_jobs = []
        errors = []
        
        # Vérifier que tous les comptages existent
        countings = Counting.objects.filter(order__in=counting_orders).order_by('order')
        found_orders = set(countings.values_list('order', flat=True))
        requested_orders = set(counting_orders)
        missing_orders = requested_orders - found_orders
        
        if missing_orders:
            raise JobCreationError(f"Aucun comptage trouvé avec les ordres : {sorted(missing_orders)}")
        
        for job_id in job_ids:
            # Récupérer tous les assignments de ce job
            all_job_assignments = Assigment.objects.select_related('job', 'counting').filter(
                job_id=job_id
            )
            
            if not all_job_assignments.exists():
                errors.append(f"Aucune assignation trouvée pour le job {job_id}")
                continue
            
            # Vérifier que TOUS les assignments du job (qui ne sont pas déjà TRANSFERT) sont au statut PRET
            # Cela permet de transférer progressivement les assignments
            assignments_to_check = all_job_assignments.exclude(status='TRANSFERT')
            assignments_not_pret = assignments_to_check.exclude(status='PRET')
            
            # Récupérer le job pour obtenir sa référence
            job = all_job_assignments.first().job if all_job_assignments.exists() else None
            if not job:
                errors.append(f"Job avec l'ID {job_id} non trouvé")
                continue
            job_reference = job.reference
            
            if assignments_not_pret.exists():
                not_pret_details = [
                    f"comptage ordre {a.counting.order} (statut: {a.status})"
                    for a in assignments_not_pret.select_related('counting')
                ]
                errors.append(
                    f"Le job {job_reference} ne peut pas être transféré car certains comptages ne sont pas PRET : {', '.join(not_pret_details)}"
                )
                continue
            
            # Vérifier que les assignments demandés sont bien PRET (et non déjà TRANSFERT)
            for counting_order in counting_orders:
                assignment = all_job_assignments.filter(
                    counting__order=counting_order
                ).first()
                
                if not assignment:
                    errors.append(f"Aucune assignation trouvée pour le job {job_reference} et le comptage d'ordre {counting_order}")
                    continue
                
                if assignment.status != 'PRET':
                    errors.append(
                        f"Le job {job_reference} pour le comptage d'ordre {counting_order} n'est pas au statut PRET (statut actuel : {assignment.status})"
                    )
                    continue
            
            # Si toutes les vérifications passent, procéder au transfert
            job_transferred = False
            counting_references = []
            
            # Transférer les assignments pour les ordres de comptage demandés
            for counting_order in counting_orders:
                # Récupérer l'assignement pour ce job et cet ordre de comptage
                assignment = all_job_assignments.filter(
                    counting__order=counting_order
                ).first()
                
                # Transférer l'assignement
                assignment.status = 'TRANSFERT'
                assignment.transfert_date = current_time
                assignment.save()
                
                counting_references.append({
                    'counting_order': counting_order,
                    'counting_reference': assignment.counting.reference
                })
                
                # Transférer le job lui-même (une seule fois par job, même s'il est déjà TRANSFERT)
                if not job_transferred:
                    job.status = 'TRANSFERT'
                    job.transfert_date = current_time
                    job.save()
                    job_transferred = True
            
            # Ajouter le job une seule fois avec toutes ses informations de comptage
            transferred_jobs.append({
                'job_reference': job.reference,
                'counting_references': counting_references
            })
        
        # Si des erreurs ont été collectées, les lever
        if errors:
            error_message = " | ".join(errors)
            raise JobCreationError(f"Erreurs lors du transfert : {error_message}")
        
        return {
            'transferred_jobs': transferred_jobs,
            'transfer_date': current_time,
            'counting_orders': counting_orders,
            'total_transferred': len(transferred_jobs)
        }
    
    @transaction.atomic
    def transfer_assignments_by_jobs_and_counting_orders(self, job_ids: list, counting_orders: list):
        """
        Transfère les assignments qui sont au statut PRET vers le statut TRANSFERT 
        pour des jobs et ordres de comptage spécifiques.
        
        Récupère automatiquement les assignments correspondants à partir de job_ids et counting_orders.
        
        Règles métier :
        - Le job doit être au statut PRET, TRANSFERT ou ENTAME
        - Tous les assignments du job doivent avoir le statut PRET, TRANSFERT ou ENTAME pour permettre un traitement progressif
        - Seuls les assignments au statut PRET peuvent être transférés (pas ceux déjà en TRANSFERT ou ENTAME)
        - L'assignment doit correspondre au counting_order spécifié
        - Si le job est ENTAME, il reste ENTAME même après le transfert d'un comptage (ne change pas en TRANSFERT)
        - Si tous les assignments du job ne sont pas PRET, TRANSFERT ou ENTAME, ou si l'assignment ne correspond pas au counting_order, 
          retourner un message d'erreur avec la référence du job et la raison
        
        Args:
            job_ids: Liste des IDs des jobs pour lesquels transférer les assignments
            counting_orders: Liste des ordres de comptage pour lesquels transférer les assignments
            
        Returns:
            Dict contenant les informations sur les assignments transférés
            
        Raises:
            JobCreationError: Si des erreurs de validation sont détectées
        """
        from ..models import Assigment, Counting
        
        current_time = timezone.now()
        transferred_assignments = []
        errors = []
        
        # Vérifier que tous les comptages existent
        countings = Counting.objects.filter(order__in=counting_orders)
        found_orders = set(countings.values_list('order', flat=True))
        requested_orders = set(counting_orders)
        missing_orders = requested_orders - found_orders
        
        if missing_orders:
            raise JobCreationError(f"Aucun comptage trouvé avec les ordres : {sorted(missing_orders)}")
        
        # Récupérer tous les assignments correspondants aux jobs et counting_orders
        assignments = Assigment.objects.select_related(
            'job', 'counting'
        ).filter(
            job_id__in=job_ids,
            counting__order__in=counting_orders
        )
        
        # Grouper les assignments par job pour faciliter le traitement
        assignments_by_job = {}
        for assignment in assignments:
            job_id = assignment.job_id
            if job_id not in assignments_by_job:
                assignments_by_job[job_id] = []
            assignments_by_job[job_id].append(assignment)
        
        # Dictionnaire pour suivre les jobs qui ont au moins un assignment transféré
        jobs_to_transfer = {}
        
        # Traiter chaque job
        for job_id in job_ids:
            job_assignments = assignments_by_job.get(job_id, [])
            
            # Récupérer le job pour obtenir sa référence
            job = None
            if job_assignments:
                job = job_assignments[0].job
            else:
                # Si aucun assignment trouvé, essayer de récupérer le job directement
                try:
                    from ..models import Job
                    job = Job.objects.get(id=job_id)
                except Job.DoesNotExist:
                    errors.append(f"Job avec l'ID {job_id} non trouvé")
                    continue
            
            job_reference = job.reference if job else f"ID {job_id}"
            
            # Vérifier que le job est au statut PRET, TRANSFERT ou ENTAME
            # (permet un traitement progressif : le job peut déjà être TRANSFERT si un comptage précédent a été transféré)
            # Si le job est ENTAME, il reste ENTAME même après transfert d'un comptage
            if job.status not in ['PRET', 'TRANSFERT', 'ENTAME']:
                errors.append(
                    f"Job {job_reference} : statut actuel '{job.status}' (attendu: 'PRET', 'TRANSFERT' ou 'ENTAME')"
                )
                continue
            
            # Si aucun assignment trouvé pour ce job
            if not job_assignments:
                errors.append(
                    f"Job {job_reference} : Aucun assignment trouvé pour les ordres de comptage {counting_orders}"
                )
                continue
            
            # Vérifier que tous les assignments de ce job sont soit PRET, TRANSFERT ou ENTAME
            # (permet un traitement progressif : certains peuvent déjà être TRANSFERT ou ENTAME)
            all_job_assignments = Assigment.objects.filter(job=job)
            assignments_invalid_status = all_job_assignments.exclude(status__in=['PRET', 'TRANSFERT', 'ENTAME'])
            
            if assignments_invalid_status.exists():
                # Récupérer les références des assignments avec statut invalide pour le message d'erreur
                invalid_status_details = [
                    f"comptage ordre {a.counting.order} (statut: {a.status})"
                    for a in assignments_invalid_status.select_related('counting')
                ]
                errors.append(
                    f"Job {job_reference} : Tous les assignments doivent avoir le statut PRET, TRANSFERT ou ENTAME pour transférer le job. "
                    f"Assignments avec statut invalide : {', '.join(invalid_status_details)}"
                )
                continue
            
            # Traiter chaque counting_order demandé
            for counting_order in counting_orders:
                # Trouver l'assignment correspondant à ce job et ce counting_order
                assignment = None
                for ass in job_assignments:
                    if ass.counting.order == counting_order:
                        assignment = ass
                        break
                
                if not assignment:
                    errors.append(
                        f"Job {job_reference} : Aucun assignment trouvé pour le comptage d'ordre {counting_order}"
                    )
                    continue
                
                # Validation 1: Vérifier que l'assignment est au statut PRET
                if assignment.status != 'PRET':
                    errors.append(
                        f"Job {job_reference} : L'assignment pour le comptage d'ordre {counting_order} "
                        f"n'est pas au statut PRET (statut actuel : {assignment.status})"
                    )
                    continue
                
                # Si toutes les validations passent, procéder au transfert
                assignment.status = 'TRANSFERT'
                assignment.transfert_date = current_time
                assignment.save()
                
                # Marquer le job pour transfert (si au moins un assignment est transféré)
                if job_id not in jobs_to_transfer:
                    jobs_to_transfer[job_id] = job
                
                transferred_assignments.append({
                    'assignment_id': assignment.id,
                    'assignment_reference': assignment.reference,
                    'job_reference': job_reference,
                    'job_id': job.id if job else None,
                    'counting_order': counting_order,
                    'counting_reference': assignment.counting.reference
                })
        
        # Mettre à jour le statut des jobs qui ont au moins un assignment transféré
        # Si le job est déjà ENTAME, il reste ENTAME (ne pas le changer en TRANSFERT)
        for job_id, job in jobs_to_transfer.items():
            # Ne changer le statut que si le job n'est pas déjà ENTAME
            if job.status != 'ENTAME':
                job.status = 'TRANSFERT'
                job.transfert_date = current_time
            job.save()
        
        # Si des erreurs ont été collectées, les lever
        if errors:
            error_message = " | ".join(errors)
            raise JobCreationError(f"Erreurs lors du transfert : {error_message}")
        
        return {
            'transferred_assignments': transferred_assignments,
            'transfer_date': current_time,
            'counting_orders': counting_orders,
            'total_transferred': len(transferred_assignments)
        } 
    
    @transaction.atomic
    def set_manual_entry_status_by_jobs_and_counting_orders(self, job_ids: list, counting_orders: list):
        """
        Met les jobs et leurs assignments en statut SAISIE MANUELLE 
        pour des jobs et ordres de comptage spécifiques.
        
        Récupère automatiquement les assignments correspondants à partir de job_ids et counting_orders.
        
        Règles métier :
        - Le job doit être au statut PRET, TRANSFERT ou ENTAME
        - Tous les assignments du job doivent avoir le statut PRET, TRANSFERT ou ENTAME pour permettre un traitement progressif
        - Seuls les assignments au statut PRET, TRANSFERT ou ENTAME peuvent être mis en saisie manuelle
        - L'assignment doit correspondre au counting_order spécifié
        - Si le job est ENTAME, il reste ENTAME même après la mise en saisie manuelle d'un comptage (ne change pas en SAISIE MANUELLE)
        - Si tous les assignments du job ne sont pas PRET, TRANSFERT ou ENTAME, ou si l'assignment ne correspond pas au counting_order, 
          retourner un message d'erreur avec la référence du job et la raison
        
        Args:
            job_ids: Liste des IDs des jobs pour lesquels mettre en saisie manuelle
            counting_orders: Liste des ordres de comptage pour lesquels mettre en saisie manuelle
            
        Returns:
            Dict contenant les informations sur les jobs et assignments mis en saisie manuelle
            
        Raises:
            JobCreationError: Si des erreurs de validation sont détectées
        """
        from ..models import Assigment, Counting
        
        current_time = timezone.now()
        manual_entry_jobs = []
        manual_entry_assignments = []
        errors = []
        
        # Vérifier que tous les comptages existent
        countings = Counting.objects.filter(order__in=counting_orders)
        found_orders = set(countings.values_list('order', flat=True))
        requested_orders = set(counting_orders)
        missing_orders = requested_orders - found_orders
        
        if missing_orders:
            raise JobCreationError(f"Aucun comptage trouvé avec les ordres : {sorted(missing_orders)}")
        
        # Récupérer tous les assignments correspondants aux jobs et counting_orders
        assignments = Assigment.objects.select_related(
            'job', 'counting'
        ).filter(
            job_id__in=job_ids,
            counting__order__in=counting_orders
        )
        
        # Grouper les assignments par job pour faciliter le traitement
        assignments_by_job = {}
        for assignment in assignments:
            job_id = assignment.job_id
            if job_id not in assignments_by_job:
                assignments_by_job[job_id] = []
            assignments_by_job[job_id].append(assignment)
        
        # Dictionnaire pour suivre les jobs qui ont au moins un assignment mis en saisie manuelle
        jobs_to_update = {}
        
        # Traiter chaque job
        for job_id in job_ids:
            job_assignments = assignments_by_job.get(job_id, [])
            
            # Récupérer le job pour obtenir sa référence
            job = None
            if job_assignments:
                job = job_assignments[0].job
            else:
                # Si aucun assignment trouvé, essayer de récupérer le job directement
                try:
                    from ..models import Job
                    job = Job.objects.get(id=job_id)
                except Job.DoesNotExist:
                    errors.append(f"Job avec l'ID {job_id} non trouvé")
                    continue
            
            job_reference = job.reference if job else f"ID {job_id}"
            
            # Vérifier que le job est au statut PRET, TRANSFERT ou ENTAME
            if job.status not in ['PRET', 'TRANSFERT', 'ENTAME']:
                errors.append(
                    f"Job {job_reference} : statut actuel '{job.status}' (attendu: 'PRET', 'TRANSFERT' ou 'ENTAME')"
                )
                continue
            
            # Si aucun assignment trouvé pour ce job
            if not job_assignments:
                errors.append(
                    f"Job {job_reference} : Aucun assignment trouvé pour les ordres de comptage {counting_orders}"
                )
                continue
            
            # Vérifier que tous les assignments de ce job sont soit PRET, TRANSFERT ou ENTAME
            all_job_assignments = Assigment.objects.filter(job=job)
            assignments_invalid_status = all_job_assignments.exclude(status__in=['PRET', 'TRANSFERT', 'ENTAME'])
            
            if assignments_invalid_status.exists():
                # Récupérer les références des assignments avec statut invalide pour le message d'erreur
                invalid_status_details = [
                    f"comptage ordre {a.counting.order} (statut: {a.status})"
                    for a in assignments_invalid_status.select_related('counting')
                ]
                errors.append(
                    f"Job {job_reference} : Tous les assignments doivent avoir le statut PRET, TRANSFERT ou ENTAME pour mettre en saisie manuelle. "
                    f"Assignments avec statut invalide : {', '.join(invalid_status_details)}"
                )
                continue
            
            # Traiter chaque counting_order demandé
            for counting_order in counting_orders:
                # Trouver l'assignment correspondant à ce job et ce counting_order
                assignment = None
                for ass in job_assignments:
                    if ass.counting.order == counting_order:
                        assignment = ass
                        break
                
                if not assignment:
                    errors.append(
                        f"Job {job_reference} : Aucun assignment trouvé pour le comptage d'ordre {counting_order}"
                    )
                    continue
                
                # Validation: Vérifier que l'assignment est au statut PRET, TRANSFERT ou ENTAME
                if assignment.status not in ['PRET', 'TRANSFERT', 'ENTAME']:
                    errors.append(
                        f"Job {job_reference} : L'assignment pour le comptage d'ordre {counting_order} "
                        f"n'est pas au statut PRET, TRANSFERT ou ENTAME (statut actuel : {assignment.status})"
                    )
                    continue
                
                # Si toutes les validations passent, procéder à la mise en saisie manuelle
                # Note: Les assignments n'ont pas de statut SAISIE MANUELLE dans leur modèle,
                # donc on les laisse dans leur statut actuel mais on marque le job
                # Si besoin, on peut ajouter un champ ou un statut pour les assignments plus tard
                
                # Marquer le job pour mise à jour (si au moins un assignment est traité)
                if job_id not in jobs_to_update:
                    jobs_to_update[job_id] = job
                
                manual_entry_assignments.append({
                    'assignment_id': assignment.id,
                    'assignment_reference': assignment.reference,
                    'job_reference': job_reference,
                    'job_id': job.id if job else None,
                    'counting_order': counting_order,
                    'counting_reference': assignment.counting.reference,
                    'previous_status': assignment.status
                })
        
        # Mettre à jour le statut des jobs qui ont au moins un assignment traité
        # Si le job est déjà ENTAME, il reste ENTAME (ne pas le changer en SAISIE MANUELLE)
        for job_id, job in jobs_to_update.items():
            # Ne changer le statut que si le job n'est pas déjà ENTAME
            if job.status != 'ENTAME':
                job.status = 'SAISIE MANUELLE'
                job.saisie_manuelle_date = current_time
            job.save()
            
            manual_entry_jobs.append({
                'job_id': job.id,
                'job_reference': job.reference,
                'status': job.status,
                'saisie_manuelle_date': job.saisie_manuelle_date
            })
        
        # Si des erreurs ont été collectées, les lever
        if errors:
            error_message = " | ".join(errors)
            raise JobCreationError(f"Erreurs lors de la mise en saisie manuelle : {error_message}")
        
        return {
            'manual_entry_jobs': manual_entry_jobs,
            'manual_entry_assignments': manual_entry_assignments,
            'saisie_manuelle_date': current_time,
            'counting_orders': counting_orders,
            'total_jobs': len(manual_entry_jobs),
            'total_assignments': len(manual_entry_assignments)
        }

    def get_job_progress_by_counting(self, job_id: int) -> Dict[str, Any]:
        """
        Calcule l'avancement des emplacements par job et par counting
        """
        try:
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Récupérer tous les emplacements du job
            job_details = job.jobdetail_set.select_related(
                'location__sous_zone__zone'
            ).all()
            
            # Récupérer tous les countings de l'inventaire
            countings = job.inventory.countings.all().order_by('order')
            
            progress_data = []
            
            for counting in countings:
                # Récupérer les affectations pour ce counting
                assignments = job.assigment_set.filter(counting=counting)
                
                if not assignments.exists():
                    continue
                
                # Calculer l'avancement pour ce counting
                total_emplacements = job_details.count()
                completed_emplacements = 0
                emplacements_details = []
                
                for job_detail in job_details:
                    location = job_detail.location
                    
                    # Vérifier si des CountingDetail existent pour cette location et ce counting
                    counting_details = CountingDetail.objects.filter(
                        location=location,
                        counting=counting
                    )
                    
                    # Déterminer le statut de l'emplacement
                    if counting_details.exists():
                        status = "TERMINE"
                        completed_emplacements += 1
                    else:
                        status = "EN ATTENTE"
                    
                    # Récupérer les détails du comptage
                    counting_details_data = []
                    for cd in counting_details:
                        counting_details_data.append({
                            'id': cd.id,
                            'reference': cd.reference,
                            'quantity_inventoried': cd.quantity_inventoried,
                            'product_reference': cd.product.reference if cd.product else None,
                            'dlc': cd.dlc,
                            'n_lot': cd.n_lot,
                            'last_synced_at': cd.last_synced_at
                        })
                    
                    emplacement_detail = {
                        'location_id': location.id,
                        'location_reference': location.location_reference,
                        'sous_zone_name': location.sous_zone.sous_zone_name if location.sous_zone else None,
                        'zone_name': location.sous_zone.zone.zone_name if location.sous_zone and location.sous_zone.zone else None,
                        'status': status,
                        'counting_details': counting_details_data
                    }
                    emplacements_details.append(emplacement_detail)
                
                # Calculer le pourcentage de progression
                progress_percentage = (completed_emplacements / total_emplacements * 100) if total_emplacements > 0 else 0
                
                progress_info = {
                    'job_id': job.id,
                    'job_reference': job.reference,
                    'job_status': job.status,
                    'counting_order': counting.order,
                    'counting_reference': counting.reference,
                    'counting_count_mode': counting.count_mode,
                    'total_emplacements': total_emplacements,
                    'completed_emplacements': completed_emplacements,
                    'progress_percentage': round(progress_percentage, 2),
                    'emplacements_details': emplacements_details
                }
                
                progress_data.append(progress_info)
            
            return {
                'success': True,
                'job_id': job.id,
                'job_reference': job.reference,
                'inventory_reference': job.inventory.reference,
                'warehouse_name': job.warehouse.warehouse_name,
                'progress_by_counting': progress_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_inventory_progress_by_counting(self, inventory_id: int) -> Dict[str, Any]:
        """
        Calcule l'avancement global de tous les jobs d'un inventaire par counting
        """
        try:
            # Récupérer tous les jobs de l'inventaire
            jobs = self.repository.get_jobs_by_inventory(inventory_id)
            
            if not jobs:
                return {
                    'success': False,
                    'error': f"Aucun job trouvé pour l'inventaire {inventory_id}"
                }
            
            # Récupérer tous les countings de l'inventaire
            countings = jobs[0].inventory.countings.all().order_by('order')
            
            inventory_progress = []
            
            for counting in countings:
                total_emplacements = 0
                completed_emplacements = 0
                jobs_progress = []
                
                for job in jobs:
                    job_progress = self.get_job_progress_by_counting(job.id)
                    
                    if job_progress['success']:
                        for progress in job_progress['progress_by_counting']:
                            if progress['counting_order'] == counting.order:
                                total_emplacements += progress['total_emplacements']
                                completed_emplacements += progress['completed_emplacements']
                                jobs_progress.append({
                                    'job_id': job.id,
                                    'job_reference': job.reference,
                                    'job_status': job.status,
                                    'total_emplacements': progress['total_emplacements'],
                                    'completed_emplacements': progress['completed_emplacements'],
                                    'progress_percentage': progress['progress_percentage']
                                })
                
                progress_percentage = (completed_emplacements / total_emplacements * 100) if total_emplacements > 0 else 0
                
                counting_progress = {
                    'counting_order': counting.order,
                    'counting_reference': counting.reference,
                    'counting_count_mode': counting.count_mode,
                    'total_emplacements': total_emplacements,
                    'completed_emplacements': completed_emplacements,
                    'progress_percentage': round(progress_percentage, 2),
                    'jobs_progress': jobs_progress
                }
                
                inventory_progress.append(counting_progress)
            
            return {
                'success': True,
                'inventory_id': inventory_id,
                'inventory_reference': jobs[0].inventory.reference,
                'total_jobs': len(jobs),
                'progress_by_counting': inventory_progress
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 