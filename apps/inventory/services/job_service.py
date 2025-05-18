from django.utils import timezone
from ..models import Job, Planning, Pda, JobDetail, Location, Inventory, Warehouse
from apps.users.models import UserWeb
from ..exceptions import (
    JobCreationError,
    PlanningCreationError,
    PdaCreationError,
    JobDetailCreationError
)
from ..serializers.job_serializer import InventoryJobRetrieveSerializer
import logging
from django.db import connection, transaction

logger = logging.getLogger(__name__)

class JobService:
    @staticmethod
    def create_inventory_jobs(data):
        """
        Crée un planning, des PDAs et des jobs avec leurs détails
        """
        # Utiliser une transaction pour s'assurer que soit tout est créé, soit rien n'est créé
        with transaction.atomic():
            try:
                # 1. Validation initiale des données
                if not data.get('date'):
                    raise PlanningCreationError("La date est obligatoire")
                if not data.get('warehouse'):
                    raise PlanningCreationError("L'ID de l'entrepôt est obligatoire")
                if not data.get('inventory'):
                    raise PlanningCreationError("L'ID de l'inventaire est obligatoire")
                if not data.get('pda'):
                    raise PdaCreationError("Au moins un PDA est requis")
                if not data.get('jobs'):
                    raise JobCreationError("Au moins un job est requis")

                # 2. Récupération et validation des instances
                try:
                    warehouse = Warehouse.objects.get(id=data['warehouse'])
                except Warehouse.DoesNotExist:
                    raise PlanningCreationError(f"Entrepôt avec l'ID {data['warehouse']} non trouvé")

                try:
                    inventory = Inventory.objects.get(id=data['inventory'])
                except Inventory.DoesNotExist:
                    raise PlanningCreationError(f"Inventaire avec l'ID {data['inventory']} non trouvé")

                # 3. Validation des utilisateurs pour les PDAs
                session_users = {}
                for pda_data in data['pda']:
                    try:
                        session_user = UserWeb.objects.get(id=pda_data['session'])
                        session_users[pda_data['session']] = session_user
                    except UserWeb.DoesNotExist:
                        raise PdaCreationError(f"Utilisateur avec l'ID {pda_data['session']} non trouvé")

                # 4. Validation des emplacements pour les jobs
                locations = {}
                for job_data in data['jobs']:
                    for emplacement_id in job_data['emplacements']:
                        if emplacement_id not in locations:
                            try:
                                location = Location.objects.get(id=emplacement_id)
                                locations[emplacement_id] = location
                            except Location.DoesNotExist:
                                raise JobCreationError(f"Emplacement {emplacement_id} non trouvé")

                # 5. Création du planning
                existing_planning = Planning.objects.filter(
                    start_date=data['date'],
                    inventory=inventory
                ).first()

                if existing_planning:
                    planning = existing_planning
                else:
                    planning = Planning.objects.create(
                        start_date=data['date'],
                        warehouse=warehouse,
                        inventory=inventory
                    )

                # 6. Création des PDAs
                pda_objects = []
                for pda_data in data['pda']:
                    pda = Pda.objects.create(
                        lebel=pda_data['nom'],
                        session=session_users[pda_data['session']],
                        inventory=inventory
                    )
                    pda_objects.append(pda)

                # 7. Création des jobs et leurs détails
                jobs = []
                job_detail_objects = []
                for job_data in data['jobs']:
                    job = Job.objects.create(
                        status='LAUNCH',
                        lunch_date=timezone.now(),
                        warehouse=warehouse
                    )
                    jobs.append(job)

                    for emplacement_id in job_data['emplacements']:
                        job_detail = JobDetail.objects.create(
                            location=locations[emplacement_id],
                            job=job,
                            status='PENDING'
                        )
                        job_detail_objects.append(job_detail)

                # 8. Préparation des données pour la sérialisation
                jobs_data = []
                for job in jobs:
                    emplacements = JobDetail.objects.filter(job=job).values_list('location_id', flat=True)
                    jobs_data.append({
                        'emplacements': list(emplacements)
                    })

                response_data = {
                    'date': planning.start_date,
                    'jobs': jobs_data,
                    'pda': [{'id': pda.id, 'nom': pda.lebel, 'session': pda.session.id} for pda in pda_objects]
                }

                # 9. Sérialisation des données
                serializer = InventoryJobRetrieveSerializer(response_data)
                return serializer.data

            except (PlanningCreationError, PdaCreationError, JobCreationError, JobDetailCreationError) as e:
                # Ces erreurs sont déjà bien formatées, on les relance telles quelles
                raise e
            except Exception as e:
                # Pour toute autre erreur, on la transforme en JobCreationError
                raise JobCreationError(f"Erreur inattendue lors de la création des jobs: {str(e)}")

    @staticmethod
    def get_inventory_jobs(inventory_id, warehouse_id):
        """
        Récupère les jobs d'inventaire pour un inventaire et un warehouse spécifiques
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            
        Returns:
            dict: Les données des jobs d'inventaire
            
        Raises:
            JobCreationError: Si une erreur survient lors de la récupération des données
        """
        try:
            # Récupérer l'inventaire et le warehouse
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)

            # Récupérer le planning
            planning = Planning.objects.get(inventory=inventory, warehouse=warehouse)

            # Récupérer les jobs non supprimés
            jobs = Job.objects.filter(warehouse=warehouse, is_deleted=False)

            # Récupérer les PDAs
            pdas = Pda.objects.filter(inventory=inventory)

            # Préparer les données pour la sérialisation
            jobs_data = []
            for job in jobs:
                emplacements = JobDetail.objects.filter(job=job, is_deleted=False).values_list('location_id', flat=True)
                jobs_data.append({
                    'emplacements': list(emplacements)
                })

            data = {
                'date': planning.start_date,
                'jobs': jobs_data,
                'pda': [{'id': pda.id, 'nom': pda.lebel, 'session': pda.session.id} for pda in pdas]
            }

            # Sérialiser les données
            serializer = InventoryJobRetrieveSerializer(data)
            return serializer.data

        except Inventory.DoesNotExist:
            raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        except Planning.DoesNotExist:
            raise JobCreationError(f"Planning non trouvé pour l'inventaire {inventory_id} et le warehouse {warehouse_id}")
        except Exception as e:
            raise JobCreationError(f"Erreur lors de la récupération des jobs: {str(e)}")

    @staticmethod
    def update_inventory_jobs(inventory_id, warehouse_id, data):
        """
        Met à jour les jobs d'inventaire pour un inventaire et un warehouse spécifiques
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            data: Les données de mise à jour
            
        Returns:
            dict: Les données mises à jour des jobs d'inventaire
            
        Raises:
            JobCreationError: Si une erreur survient lors de la mise à jour
        """
        try:
            # Récupérer l'inventaire et le warehouse
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)

            # Mettre à jour le planning
            try:
                planning = Planning.objects.get(inventory=inventory, warehouse=warehouse)
                planning.start_date = data['date']
                planning.save()
            except Planning.DoesNotExist:
                planning = Planning.objects.create(
                    start_date=data['date'],
                    warehouse=warehouse,
                    inventory=inventory
                )

            # Supprimer les jobs existants et leurs détails
            existing_jobs = Job.objects.filter(warehouse=warehouse)
            JobDetail.objects.filter(job__in=existing_jobs).delete()
            existing_jobs.delete()

            # Créer les nouveaux jobs et leurs détails
            jobs = []
            for job_data in data['jobs']:
                try:
                    job = Job.objects.create(
                        status='LAUNCH',
                        lunch_date=timezone.now(),
                        warehouse=warehouse
                    )
                    jobs.append(job)

                    # Créer les job details pour chaque emplacement
                    for emplacement_id in job_data['emplacements']:
                        try:
                            location = Location.objects.get(id=emplacement_id)
                        except Location.DoesNotExist:
                            raise JobCreationError(f"Emplacement {emplacement_id} non trouvé")

                        # Créer un seul job detail par emplacement
                        try:
                            JobDetail.objects.create(
                                location=location,
                                job=job,
                                status='PENDING'
                            )
                        except Exception as e:
                            raise JobDetailCreationError(f"Erreur lors de la création du job detail: {str(e)}")

                except Exception as e:
                    raise JobCreationError(f"Erreur lors de la création du job: {str(e)}")

            # Mettre à jour les PDAs si fournis
            if 'pda' in data:
                for pda_data in data['pda']:
                    try:
                        pda = Pda.objects.get(id=pda_data['id'])
                        pda.lebel = pda_data['nom']
                        pda.session_id = pda_data['session']
                        pda.save()
                    except Pda.DoesNotExist:
                        raise JobCreationError(f"PDA avec l'ID {pda_data['id']} non trouvé")
                    except Exception as e:
                        raise JobCreationError(f"Erreur lors de la mise à jour du PDA {pda_data['id']}: {str(e)}")

            # Récupérer les PDAs mis à jour
            pdas = Pda.objects.filter(inventory=inventory)

            # Préparer les données pour la sérialisation
            jobs_data = []
            for job in jobs:
                emplacements = JobDetail.objects.filter(job=job).values_list('location_id', flat=True)
                jobs_data.append({
                    'emplacements': list(emplacements)
                })

            response_data = {
                'date': planning.start_date,
                'jobs': jobs_data,
                'pda': [{'id': pda.id, 'nom': pda.lebel, 'session': pda.session.id} for pda in pdas]
            }

            # Sérialiser les données
            serializer = InventoryJobRetrieveSerializer(response_data)
            return serializer.data

        except Inventory.DoesNotExist:
            raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        except Exception as e:
            raise JobCreationError(f"Erreur lors de la mise à jour des jobs: {str(e)}")

    @staticmethod
    def delete_inventory_jobs(inventory_id, warehouse_id):
        """
        Supprime (soft delete) les jobs d'inventaire et toutes les entités associées pour un inventaire et un warehouse spécifiques
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            
        Returns:
            bool: True si la suppression a réussi
            
        Raises:
            JobCreationError: Si une erreur survient lors de la suppression
        """
        try:
            # Récupérer l'inventaire et le warehouse
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)

            # Soft delete du planning
            try:
                planning = Planning.objects.get(inventory=inventory, warehouse=warehouse)
                planning.soft_delete()
            except Planning.DoesNotExist:
                pass  # Le planning n'existe pas, on continue

            # Soft delete des PDAs
            pdas = Pda.objects.filter(inventory=inventory)
            for pda in pdas:
                pda.soft_delete()

            # Soft delete des jobs
            jobs = Job.objects.filter(warehouse=warehouse)
            for job in jobs:
                job.soft_delete()

            # Soft delete des job details associés
            current_time = timezone.now()
            
            # Utiliser une requête SQL directe pour la mise à jour
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE inventory_jobdetail 
                    SET is_deleted = TRUE, 
                        deleted_at = %s 
                    WHERE job_id IN (
                        SELECT id FROM inventory_job 
                        WHERE warehouse_id = %s
                    )
                """, [current_time, warehouse_id])

            return True

        except Inventory.DoesNotExist:
            raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        except Exception as e:
            raise JobCreationError(f"Erreur lors de la suppression des jobs: {str(e)}") 