from apps.inventory.models import Job, Assigment, Counting, Inventory, Warehouse, Location, JobDetail
from django.db import transaction
from apps.inventory.exceptions.job_exceptions import JobCreationError

class JobService:
    @staticmethod
    @transaction.atomic
    def create_jobs_for_inventory_warehouse(inventory_id, warehouse_id, emplacements):
        try:
            # Vérifier que l'inventaire existe
            try:
                inventory = Inventory.objects.get(id=inventory_id)
            except Inventory.DoesNotExist:
                raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Vérifier que le warehouse existe
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
            
            # Vérifier qu'il y a au moins deux comptages pour cet inventaire
            countings = Counting.objects.filter(inventory=inventory).order_by('order')
            if countings.count() < 2:
                raise JobCreationError(f"Il faut au moins deux comptages pour l'inventaire {inventory.reference}. Comptages trouvés : {countings.count()}")
            
            # Prendre les deux premiers comptages
            countings_to_use = countings[:2]
            
            jobs = []
            for emplacement_id in emplacements:
                # Vérifier que l'emplacement existe
                try:
                    location = Location.objects.get(id=emplacement_id)
                except Location.DoesNotExist:
                    raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
                
                # Vérifier que l'emplacement appartient au warehouse
                if location.warehouse_id != warehouse_id:
                    raise JobCreationError(f"L'emplacement {location.location_code} n'appartient pas au warehouse {warehouse.warehouse_name}")
                
                # Créer le job
                job = Job.objects.create(
                    reference=Job().generate_reference(Job.REFERENCE_PREFIX),
                    status='EN ATTENTE',
                    warehouse=warehouse,
                    inventory=inventory
                )
                
                # Créer le JobDetail pour cet emplacement
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    status='EN ATTENTE'
                )
                
                # Créer les assignements pour les deux comptages
                for counting in countings_to_use:
                    Assigment.objects.create(
                        reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                        job=job,
                        counting=counting
                    )
                
                jobs.append(job)
            
            return jobs
            
        except JobCreationError:
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de la création des jobs : {str(e)}")

    @staticmethod
    def get_pending_jobs_references(warehouse_id):
        """
        Récupère les références et IDs des jobs en attente pour un warehouse
        """
        try:
            # Vérifier que le warehouse existe
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
            
            # Récupérer les jobs en attente pour ce warehouse
            pending_jobs = Job.objects.filter(
                warehouse=warehouse,
                status='EN ATTENTE'
            ).values('id', 'reference').order_by('created_at')
            
            return list(pending_jobs)
            
        except JobCreationError:
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de la récupération des jobs en attente : {str(e)}")

    @staticmethod
    @transaction.atomic
    def remove_job_emplacements(job_id, emplacement_ids):
        """
        Supprime des emplacements d'un job
        """
        try:
            # Vérifier que le job existe
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être modifiés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être modifiés. Statut actuel : {job.status}")
            
            # Vérifier que tous les emplacements existent dans le job
            existing_job_details = JobDetail.objects.filter(job=job, location_id__in=emplacement_ids)
            if existing_job_details.count() != len(emplacement_ids):
                raise JobCreationError("Certains emplacements ne sont pas associés à ce job")
            
            # Supprimer les JobDetail pour les emplacements spécifiés
            deleted_count = existing_job_details.delete()[0]
            
            return {
                'job_id': job.id,
                'job_reference': job.reference,
                'deleted_emplacements_count': deleted_count
            }
            
        except JobCreationError:
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de la suppression des emplacements : {str(e)}")

    @staticmethod
    @transaction.atomic
    def add_job_emplacements(job_id, emplacement_ids):
        """
        Ajoute des emplacements à un job
        """
        try:
            # Vérifier que le job existe
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être modifiés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être modifiés. Statut actuel : {job.status}")
            
            # Vérifier que tous les emplacements existent
            for emplacement_id in emplacement_ids:
                try:
                    location = Location.objects.get(id=emplacement_id)
                except Location.DoesNotExist:
                    raise JobCreationError(f"Emplacement avec l'ID {emplacement_id} non trouvé")
                
                # Vérifier que l'emplacement appartient au warehouse du job
                if location.warehouse_id != job.warehouse_id:
                    raise JobCreationError(f"L'emplacement {location.location_code} n'appartient pas au warehouse {job.warehouse.warehouse_name}")
                
                # Vérifier que l'emplacement n'est pas déjà associé au job
                if JobDetail.objects.filter(job=job, location=location).exists():
                    raise JobCreationError(f"L'emplacement {location.location_code} est déjà associé à ce job")
            
            # Créer de nouveaux JobDetail pour les emplacements fournis
            created_count = 0
            for emplacement_id in emplacement_ids:
                location = Location.objects.get(id=emplacement_id)
                JobDetail.objects.create(
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
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de l'ajout des emplacements : {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_job(job_id):
        """
        Supprime définitivement un job avec toutes ses relations (Assigment et JobDetail)
        """
        try:
            # Vérifier que le job existe
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job est en attente (seuls les jobs en attente peuvent être supprimés)
            if job.status != 'EN ATTENTE':
                raise JobCreationError(f"Seuls les jobs en attente peuvent être supprimés. Statut actuel : {job.status}")
            
            # Récupérer les informations avant suppression pour la réponse
            job_reference = job.reference
            assigments_count = Assigment.objects.filter(job=job).count()
            job_details_count = JobDetail.objects.filter(job=job).count()
            
            # Supprimer les Assigment liés au job
            Assigment.objects.filter(job=job).delete()
            
            # Supprimer les JobDetail liés au job
            JobDetail.objects.filter(job=job).delete()
            
            # Supprimer le job lui-même
            job.delete()
            
            return {
                'job_id': job_id,
                'job_reference': job_reference,
                'deleted_assigments_count': assigments_count,
                'deleted_job_details_count': job_details_count
            }
            
        except JobCreationError:
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de la suppression du job : {str(e)}")

    @staticmethod
    @transaction.atomic
    def validate_jobs(job_ids):
        """
        Valide des jobs en changeant leur statut de "EN ATTENTE" à "VALIDE"
        """
        try:
            # Vérifier que tous les jobs existent
            jobs = Job.objects.filter(id__in=job_ids)
            if jobs.count() != len(job_ids):
                raise JobCreationError("Certains jobs n'existent pas")
            
            # Vérifier que tous les jobs sont en attente
            non_pending_jobs = jobs.exclude(status='EN ATTENTE')
            if non_pending_jobs.exists():
                invalid_jobs = [f"Job {job.reference} (statut: {job.status})" for job in non_pending_jobs]
                raise JobCreationError(f"Seuls les jobs en attente peuvent être validés. Jobs invalides : {', '.join(invalid_jobs)}")
            
            # Mettre à jour le statut et la date de validation
            from django.utils import timezone
            current_time = timezone.now()
            
            updated_jobs = []
            for job in jobs:
                job.status = 'VALIDE'
                job.valide_date = current_time
                job.save()
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
            # Re-raise les exceptions métier
            raise
        except Exception as e:
            # Capturer les autres exceptions et les transformer en JobCreationError
            raise JobCreationError(f"Erreur inattendue lors de la validation des jobs : {str(e)}") 