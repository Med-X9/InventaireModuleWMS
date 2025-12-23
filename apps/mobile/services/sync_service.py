from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.inventory.models import Assigment
from apps.mobile.repositories.sync_repository import SyncRepository
from apps.mobile.exceptions.sync_exceptions import (
    SyncDataException,
    UploadDataException
)
from apps.mobile.exceptions.inventory_exceptions import (
    DatabaseConnectionException,
    DataValidationException
)


class SyncService:
    """Service pour la synchronisation"""
    
    def __init__(self):
        self.repository = SyncRepository()
    
    def sync_data(self, user_id, inventory_id=None):
        """
        Synchronise toutes les données nécessaires.
        
        Args:
            user_id: ID de l'utilisateur authentifié
            inventory_id: ID de l'inventaire pour filtrer (optionnel)
        """
        try:
            # Récupérer les inventaires pour référence (mais ne pas les retourner)
            if user_id:
                inventories = self.repository.get_inventories_by_user_assignments(user_id)
                # Filtrer par inventory_id si fourni
                if inventory_id:
                    inventories = inventories.filter(id=inventory_id)
            else:
                inventories = self.repository.get_inventories_in_realisation()
                if inventory_id:
                    inventories = inventories.filter(id=inventory_id)
            
            # Préparer la réponse (sans inventaires)
            response_data = {
                'jobs': [],
                'assignments': [],
                'countings': []
            }

            # Récupérer et traiter les jobs
            jobs = []
            try:
                if user_id:
                    # Filtrer les jobs par assignments de l'utilisateur
                    jobs = self.repository.get_jobs_by_inventories_and_user(inventories, user_id, inventory_id)
                else:
                    # Récupérer tous les jobs des inventaires
                    jobs = self.repository.get_jobs_by_inventories(inventories)

                for job in jobs:
                    try:
                        # Passer user_id pour filtrer les job_details par assignments
                        # format_job_data retourne maintenant une liste de jobs fusionnés (un par job_detail)
                        jobs_fused = self.repository.format_job_data(job, user_id=user_id if user_id else None)
                        # Ajouter tous les jobs fusionnés à la réponse
                        response_data['jobs'].extend(jobs_fused)
                    except Exception as e:
                        print(f"Erreur lors du traitement du job {job.id}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Erreur lors de la récupération des jobs: {str(e)}")
            
            # Récupérer et traiter les assignations (seulement si on a des jobs)
            if jobs:
                try:
                    # Filtrer par utilisateur si user_id est fourni
                    if user_id:
                        assignments = self.repository.get_assignments_by_jobs_and_user(jobs, user_id)
                    else:
                        assignments = self.repository.get_assignments_by_jobs(jobs)
                    
                    for assignment in assignments:
                        try:
                            assignment_data = self.repository.format_assignment_data(assignment)
                            response_data['assignments'].append(assignment_data)
                        except Exception as e:
                            print(f"Erreur lors du traitement de l'assignation {assignment.id}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Erreur lors de la récupération des assignations: {str(e)}")
            else:
                print("Aucun job trouvé, donc aucune assignation à récupérer")
            
            # Récupérer et traiter les comptages
            try:
                if user_id:
                    # Récupérer uniquement les countings liés aux assignments de l'utilisateur
                    countings = self.repository.get_countings_by_user_assignments(user_id, inventory_id)
                else:
                    # Récupérer tous les countings des inventaires
                    countings = self.repository.get_countings_by_inventories(inventories)
                    if inventory_id:
                        countings = countings.filter(inventory_id=inventory_id)
                
                for counting in countings:
                    try:
                        counting_data = self.repository.format_counting_data(counting)
                        response_data['countings'].append(counting_data)
                    except Exception as e:
                        print(f"Erreur lors du traitement du comptage {counting.id}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Erreur lors de la récupération des comptages: {str(e)}")
            
            # Logger la synchronisation
            print(f"Synchronisation réussie: {len(response_data['jobs'])} jobs, {len(response_data['assignments'])} assignments, {len(response_data['countings'])} countings")
            
            return response_data
            
        except Exception as e:
            print(f"Erreur de synchronisation: {str(e)}")
            raise SyncDataException(f"Erreur de synchronisation: {str(e)}")
    
    def upload_data(self, sync_id, countings=None, assignments=None):
        """Upload des données de synchronisation"""
        try:
            response_data = {
                'success': True,
                # 'sync_id': sync_id,
                'uploaded_count': 0,
                'errors': [],
                'conflicts': []
            }
            
            with transaction.atomic():
                # Traiter les comptages
                if countings:
                    for counting_data in countings:
                        try:
                            # Note: Cette partie nécessite les modèles Product et Location
                            # qui ont été supprimés de l'API sync_data
                            # Pour l'instant, on skip le traitement des comptages
                            response_data['errors'].append(f"Traitement des comptages temporairement désactivé")
                            
                        except Exception as e:
                            response_data['errors'].append(f"Erreur comptage {counting_data.get('detail_id', 'unknown')}: {str(e)}")
                
                # Traiter les statuts d'assignation
                if assignments:
                    for assignment_data in assignments:
                        try:
                            assignment = get_object_or_404(Assigment, id=assignment_data['assignment_web_id'])
                            assignment.status = assignment_data['status']
                            assignment.entame_date = assignment_data.get('entame_date')
                            assignment.date_start = assignment_data.get('date_start')
                            assignment.save()
                            
                            response_data['uploaded_count'] += 1
                            
                        except Exception as e:
                            response_data['errors'].append(f"Erreur assignation {assignment_data.get('assignment_web_id', 'unknown')}: {str(e)}")
            
            # Logger l'upload
            print(f"Upload réussi: {response_data['uploaded_count']} éléments")
            
            return response_data
            
        except Exception as e:
            print(f"Erreur d'upload: {str(e)}")
            raise UploadDataException(f"Erreur d'upload: {str(e)}") 