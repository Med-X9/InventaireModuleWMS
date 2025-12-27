"""
Service pour calculer les écarts entre les comptages d'un job.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict
from django.db.models import Q
from ..repositories.job_repository import JobRepository
from ..models import Job, Assigment, CountingDetail, EcartComptage, ComptageSequence, JobDetail
from ..usecases.job_discrepancy_standardization import JobDiscrepancyStandardizationUseCase
import logging

logger = logging.getLogger(__name__)


class JobDiscrepancyService:
    """
    Service pour calculer les écarts entre les comptages.
    Contient la logique métier pour le calcul des écarts.
    """
    
    def __init__(
        self,
        job_repository: Optional[JobRepository] = None,
        standardization_use_case: Optional[JobDiscrepancyStandardizationUseCase] = None
    ):
        """
        Initialise le service avec un repository et un use case de standardisation.
        
        Args:
            job_repository: Repository pour l'accès aux données (injection de dépendance)
            standardization_use_case: Use case pour standardiser les comptages (injection de dépendance)
        """
        self.job_repository = job_repository or JobRepository()
        self.standardization_use_case = standardization_use_case or JobDiscrepancyStandardizationUseCase()
    
    def get_jobs_with_discrepancies(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs avec leurs assignments et calcule les écarts entre tous les comptages.
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Liste de dictionnaires contenant les informations des jobs avec écarts calculés
            et tous les comptages standardisés
            
        Raises:
            ValueError: Si l'inventaire ou le warehouse n'existe pas
        """
        # Vérifier que l'inventaire existe
        inventory = self.job_repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        
        # Vérifier que le warehouse existe
        warehouse = self.job_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        
        # Récupérer les jobs avec leurs assignments et counting details
        jobs = self.job_repository.get_jobs_with_assignments_and_counting_details(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        
        # Récupérer le nombre total d'emplacements pour chaque job
        from ..models import JobDetail
        job_ids = [job.id for job in jobs]
        job_details_count = {
            job_id: JobDetail.objects.filter(job_id=job_id).count()
            for job_id in job_ids
        }
        
        result = []
        for job in jobs:
            # Récupérer les assignments du job
            assignments = self.job_repository.get_assignments_by_job(job)
            
            # Récupérer tous les assignments (pas seulement 1 et 2)
            assignments_filtered = [
                assignment for assignment in assignments
                if assignment.counting
            ]
            
            # Calculer les écarts pour tous les comptages
            counting_details_by_order = getattr(job, '_counting_details_by_order', {})
            total_emplacements = job_details_count.get(job.id, 0)
            
            # Formater les assignments avec les informations d'écarts
            assignments_data = []
            for assignment in assignments_filtered:
                counting_order = assignment.counting.order if assignment.counting else None
            
                # Calculer les écarts pour ce comptage (par rapport au 1er comptage)
                discrepancy_info = self._calculate_discrepancy_with_first_counting(
                    counting_details_by_order,
                    counting_order,
                    total_emplacements
                )
                
                assignments_data.append({
                    'status': assignment.status,
                    'counting_reference': assignment.counting.reference if assignment.counting else None,
                    'counting_order': counting_order,
                    'username': assignment.session.username if assignment.session else None,
                    'discrepancy_count': discrepancy_info['discrepancy_count'],
                    'discrepancy_rate': discrepancy_info['discrepancy_rate'],
                })
            
            # Calculer les écarts entre le 1er et 2ème comptage (pour compatibilité avec l'ancien format)
            discrepancy_info_1_2 = self._calculate_discrepancies(job)
            
            result.append({
                'job_id': job.id,
                'job_reference': job.reference,
                'job_status': job.status,
                'assignments': assignments_data,
                'discrepancy_count': discrepancy_info_1_2['discrepancy_count'],
                'discrepancy_rate': discrepancy_info_1_2['discrepancy_rate'],
                'total_lines_counting_1': discrepancy_info_1_2['total_lines_counting_1'],
                'total_lines_counting_2': discrepancy_info_1_2['total_lines_counting_2'],
                'common_lines_count': discrepancy_info_1_2['common_lines_count'],
                'total_emplacements': total_emplacements,
            })
        
        # Standardiser les comptages pour tous les jobs
        standardized_result = self.standardization_use_case.standardize_jobs_countings(result)
        
        return standardized_result
    
    def _calculate_discrepancies(self, job: Job) -> Dict[str, Any]:
        """
        Calcule les écarts entre le 1er et le 2ème comptage pour un job.
        
        Args:
            job: Job avec les counting details préchargés
            
        Returns:
            Dictionnaire contenant:
            - discrepancy_count: Nombre de lignes avec écart (lignes communes avec quantités différentes)
            - discrepancy_rate: Taux d'écart (en pourcentage) basé sur les lignes communes aux deux comptages
            - total_lines_counting_1: Nombre total de lignes du 1er comptage
            - total_lines_counting_2: Nombre total de lignes du 2ème comptage
            - common_lines_count: Nombre de lignes communes aux deux comptages
        """
        # Récupérer les counting details depuis les attributs temporaires
        # Support de l'ancienne structure (_counting_details_1, _counting_details_2)
        # et de la nouvelle (_counting_details_by_order)
        counting_details_by_order = getattr(job, '_counting_details_by_order', {})
        
        if counting_details_by_order:
            # Nouvelle structure : utiliser _counting_details_by_order
            counting_details_1 = counting_details_by_order.get(1, {})
            counting_details_2 = counting_details_by_order.get(2, {})
        else:
            # Ancienne structure : utiliser _counting_details_1 et _counting_details_2
            counting_details_1 = getattr(job, '_counting_details_1', {})
            counting_details_2 = getattr(job, '_counting_details_2', {})
        
        # Calculer le nombre total de lignes pour chaque comptage (après avoir défini counting_details_1 et counting_details_2)
        total_lines_counting_1 = len(counting_details_1)
        total_lines_counting_2 = len(counting_details_2)
        
        # Créer un ensemble des clés communes aux deux comptages (intersection)
        # On ne compare que les lignes qui existent dans les deux comptages
        common_keys = set(counting_details_1.keys()) & set(counting_details_2.keys())
        
        discrepancy_count = 0
        
        # Comparer chaque ligne commune entre les deux comptages
        for key in common_keys:
            detail_1 = counting_details_1.get(key)
            detail_2 = counting_details_2.get(key)
            
            # Les deux détails existent forcément car on utilise l'intersection
            if detail_1 and detail_2:
                quantity_1 = detail_1.quantity_inventoried
                quantity_2 = detail_2.quantity_inventoried
            
                # Si les quantités diffèrent, c'est un écart
                if quantity_1 != quantity_2:
                    discrepancy_count += 1
        
        # Calculer le taux d'écart
        # Le taux est basé uniquement sur les lignes communes aux deux comptages
        common_lines_count = len(common_keys)
        if common_lines_count > 0:
            discrepancy_rate = (discrepancy_count / common_lines_count) * 100
        else:
            discrepancy_rate = 0.0
        
        return {
            'discrepancy_count': discrepancy_count,
            'discrepancy_rate': round(discrepancy_rate, 2),
            'total_lines_counting_1': total_lines_counting_1,
            'total_lines_counting_2': total_lines_counting_2,
            'common_lines_count': common_lines_count,
        }
    
    def _calculate_discrepancy_with_first_counting(
        self,
        counting_details_by_order: Dict[int, Dict],
        counting_order: Optional[int],
        total_emplacements: int
    ) -> Dict[str, Any]:
        """
        Calcule les écarts entre le 1er comptage et un comptage donné.
        
        Args:
            counting_details_by_order: Dictionnaire des counting details par ordre
            counting_order: Ordre du comptage à comparer avec le 1er (None si pas de comptage)
            total_emplacements: Nombre total d'emplacements du job
            
        Returns:
            Dictionnaire contenant:
            - discrepancy_count: Nombre de lignes avec écart
            - discrepancy_rate: Taux d'écart (nombre d'écarts / total des emplacements) * 100
        """
        if not counting_order or counting_order == 1:
            # Pas d'écart pour le 1er comptage
            return {
                'discrepancy_count': 0,
                'discrepancy_rate': 0.0,
            }
        
        # Récupérer les counting details du 1er comptage
        counting_details_1 = counting_details_by_order.get(1, {})
        
        # Récupérer les counting details du comptage à comparer
        counting_details_n = counting_details_by_order.get(counting_order, {})
        
        if not counting_details_1 or not counting_details_n:
            return {
                'discrepancy_count': 0,
                'discrepancy_rate': 0.0,
            }
        
        # Créer un ensemble des clés communes aux deux comptages
        common_keys = set(counting_details_1.keys()) & set(counting_details_n.keys())
        
        discrepancy_count = 0
        
        # Comparer chaque ligne commune entre les deux comptages
        for key in common_keys:
            detail_1 = counting_details_1.get(key)
            detail_n = counting_details_n.get(key)
            
            if detail_1 and detail_n:
                quantity_1 = detail_1.quantity_inventoried
                quantity_n = detail_n.quantity_inventoried
                
                # Si les quantités diffèrent, c'est un écart
                if quantity_1 != quantity_n:
                    discrepancy_count += 1
        
        # Calculer le taux d'écart = nombre d'écarts / total des emplacements * 100
        if total_emplacements > 0:
            discrepancy_rate = (discrepancy_count / total_emplacements) * 100
        else:
            discrepancy_rate = 0.0
        
        return {
            'discrepancy_count': discrepancy_count,
            'discrepancy_rate': round(discrepancy_rate, 2),
        }
    
    def get_jobs_with_unresolved_discrepancies_grouped_by_counting(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs nécessitant un prochain comptage à cause d'écarts avec résultat vide,
        regroupés par numéro de prochain comptage pour un inventaire et un entrepôt.

        LOGIQUE MÉTIER :
        1. Récupère les jobs avec statut 'ENTAME'
        2. Pour chaque job, analyse les comptages terminés et leurs écarts
        3. Si comptages 1&2 terminés avec écarts (final_result=None) → besoin comptage 3
        4. Si comptages 1&2&3 terminés avec écarts (final_result=None) → besoin comptage 4
        5. Et ainsi de suite...

        Un écart nécessite un nouveau comptage si :
        - final_result est NULL (résultat vide/non déterminé)

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt

        Returns:
            Liste groupée par prochain comptage à lancer :
            [
                {
                    "next_counting_order": 3,  // Prochain comptage à lancer
                    "jobs": [
                        {
                            "job_id": 1,
                            "job_reference": "JOB-0001",
                            "current_max_counting": 2,  // Max comptage terminé avec écarts
                            "has_unresolved_discrepancies": true,
                            "discrepancies_locations_count": 5  // Nombre d'emplacements avec écarts
                        }
                    ]
                }
            ]
        """
        # Vérifier que l'inventaire existe
        inventory = self.job_repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouvé")

        # Vérifier que le warehouse existe
        warehouse = self.job_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse avec l'ID {warehouse_id} non trouvé")

        # Récupérer les jobs ENTAME pour cet inventaire et entrepôt
        jobs = self.job_repository.get_jobs_by_status_and_location(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            status='ENTAME'
        )

        # Analyser chaque job pour déterminer le prochain comptage nécessaire
        jobs_needing_next_counting = defaultdict(list)

        for job in jobs:
            next_counting_order = self._determine_next_counting_order(job)
            if next_counting_order:
                # Récupérer le numéro maximum de comptage terminé pour ce job
                max_completed_counting = self._get_max_completed_counting_order(job)

                # Compter les emplacements avec écarts non résolus
                discrepancies_locations_count = self._count_discrepancies_locations_for_job(job)

                # Retourner le prochain comptage à lancer (next_counting_order)
                jobs_needing_next_counting[next_counting_order].append({
                    'job_id': job.id,
                    'job_reference': job.reference,
                    'current_max_counting': max_completed_counting,
                    'has_unresolved_discrepancies': True,
                    'discrepancies_locations_count': discrepancies_locations_count
                })

        # Formater le résultat trié par ordre de comptage
        result = []
        for counting_order in sorted(jobs_needing_next_counting.keys()):
            jobs_list = sorted(
                jobs_needing_next_counting[counting_order],
                key=lambda x: x['job_id']
            )

            result.append({
                'next_counting_order': counting_order,
                'jobs': jobs_list
            })

        return result

    def _determine_next_counting_order(self, job) -> Optional[int]:
        """
        Détermine le prochain comptage à lancer pour un job basé sur les écarts avec résultat vide.

        Logique :
        - Si comptages 1&2 terminés et contiennent écarts (final_result=None) → retourner 3
        - Si comptages 1&2&3 terminés et contiennent écarts (final_result=None) → retourner 4
        - Si comptages 1&2&3&4 terminés et contiennent écarts (final_result=None) → retourner 5
        - etc.
        - Si pas d'écarts avec résultat vide ou comptages pas terminés → retourner None

        Args:
            job: Instance du modèle Job

        Returns:
            Numéro du prochain comptage à lancer, ou None si pas nécessaire
        """
        # Récupérer tous les assignments du job triés par counting_order
        assignments = job.assigment_set.select_related('counting').order_by('counting__order')

        # Grouper par counting_order
        assignments_by_order = {}
        for assignment in assignments:
            if assignment.counting:
                order = assignment.counting.order
                assignments_by_order[order] = assignment

        # Si pas d'assignments, rien à faire
        if not assignments_by_order:
            return None

        # Trouver le numéro maximum de comptage terminé avec écarts
        max_order_with_discrepancies = 0

        for order in sorted(assignments_by_order.keys()):
            assignment = assignments_by_order[order]

            # Vérifier si ce comptage est terminé
            if assignment.status != 'TERMINE':
                break  # Les comptages suivants ne peuvent pas être terminés

            # Vérifier si ce comptage a des écarts non résolus
            has_unresolved_discrepancies = self._counting_has_unresolved_discrepancies(job, order)

            if has_unresolved_discrepancies:
                max_order_with_discrepancies = order

        # Si on a trouvé des écarts dans les derniers comptages terminés,
        # le prochain comptage à lancer est max_order_with_discrepancies + 1
        if max_order_with_discrepancies > 0:
            return max_order_with_discrepancies + 1

        return None

    def _get_max_completed_counting_order(self, job) -> int:
        """
        Retourne le numéro maximum de comptage terminé pour ce job.
        """
        max_order = 0
        for assignment in job.assigment_set.select_related('counting'):
            if assignment.status == 'TERMINE' and assignment.counting:
                max_order = max(max_order, assignment.counting.order)
        return max_order

    def _counting_has_unresolved_discrepancies(self, job, counting_order: int) -> bool:
        """
        Vérifie si un comptage spécifique a des écarts avec résultat vide (final_result=None).

        Args:
            job: Instance Job
            counting_order: Numéro d'ordre du comptage

        Returns:
            True si le comptage a des écarts avec résultat vide
        """
        # Récupérer les ComptageSequence pour ce job et ce comptage avec leurs écarts
        sequences_with_ecarts = ComptageSequence.objects.filter(
            counting_detail__job=job,
            counting_detail__counting__order=counting_order
        ).select_related('ecart_comptage')

        # Vérifier si au moins un écart a un résultat vide (final_result is None)
        for sequence in sequences_with_ecarts:
            ecart = sequence.ecart_comptage
            if ecart and ecart.final_result is None:
                return True

        return False

    def _count_discrepancies_locations_for_job(self, job) -> int:
        """
        Compte le nombre d'emplacements (locations) qui ont des écarts avec résultat vide
        pour ce job, peu importe le comptage.

        Args:
            job: Instance Job

        Returns:
            Nombre d'emplacements avec écarts (final_result=None)
        """
        # Récupérer tous les ComptageSequence pour ce job avec leurs écarts
        sequences_with_ecarts = ComptageSequence.objects.filter(
            counting_detail__job=job
        ).select_related('ecart_comptage', 'counting_detail')

        # Collecter les locations uniques qui ont des écarts non résolus
        locations_with_discrepancies = set()

        for sequence in sequences_with_ecarts:
            ecart = sequence.ecart_comptage
            if ecart and ecart.final_result is None:
                # Ajouter la location de ce counting_detail
                locations_with_discrepancies.add(sequence.counting_detail.location_id)

        return len(locations_with_discrepancies)

    def get_jobs_discrepancies_simplified(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs avec écarts simplifiés.

        Retourne uniquement :
        - Le taux d'écart entre 1er vs 2e comptage
        - Le nombre d'écarts dans les comptages suivants (final_result = null)

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt

        Returns:
            Liste simplifiée des jobs avec écarts
        """
        # Vérifier que l'inventaire existe
        inventory = self.job_repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouvé")

        # Vérifier que le warehouse existe
        warehouse = self.job_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse avec l'ID {warehouse_id} non trouvé")

        # Récupérer les jobs avec assignments
        jobs = self.job_repository.get_jobs_with_assignments_and_counting_details(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )

        result = []
        for job in jobs:
            # Récupérer les assignments du job
            assignments = self.job_repository.get_assignments_by_job(job)

            # Calculer l'écart entre 1er et 2e comptage
            counting_1_assignment = None
            counting_2_assignment = None

            for assignment in assignments:
                if assignment.counting.order == 1:
                    counting_1_assignment = assignment
                elif assignment.counting.order == 2:
                    counting_2_assignment = assignment

            # Calculer l'écart 1vs2 si les deux comptages existent et sont terminés
            ecart_1_vs_2_count = 0
            ecart_1_vs_2_rate = 0.0

            # Récupérer le nombre total de résultats liés au job avec counting_order 1 et 2
            total_results_1_2 = EcartComptage.objects.filter(
                inventory=job.inventory,
                counting_sequences__counting_detail__job=job,
                counting_sequences__counting_detail__counting__order__in=[1, 2]
            ).distinct().count()

            # Compter les résultats vides (final_result = null)
            ecart_1_vs_2_count = EcartComptage.objects.filter(
                inventory=job.inventory,
                counting_sequences__counting_detail__job=job,
                counting_sequences__counting_detail__counting__order__in=[1, 2],
                final_result__isnull=True
            ).distinct().count()

            # Calculer le taux
            if total_results_1_2 > 0:
                ecart_1_vs_2_rate = (ecart_1_vs_2_count / total_results_1_2) * 100
            else:
                ecart_1_vs_2_rate = 0.0

            # Déterminer tous les counting_orders existants pour ce job (depuis CountingDetail)
            counting_orders_in_job = set()
            counting_details = CountingDetail.objects.filter(job=job).select_related('counting')
            for counting_detail in counting_details:
                if counting_detail.counting:
                    counting_orders_in_job.add(counting_detail.counting.order)

            max_counting_order = max(counting_orders_in_job) if counting_orders_in_job else 0

            # Utiliser ecart_1_vs_2_count comme nombre_comptage
            nombre_comptage = ecart_1_vs_2_count

            # Calculer les écarts pour tous les counting_orders > 2
            ecarts_by_order = {}
            for counting_order in range(3, max_counting_order + 1):
                ecarts_count = EcartComptage.objects.filter(
                    inventory=job.inventory,
                    counting_sequences__counting_detail__job=job,
                    counting_sequences__counting_detail__counting__order=counting_order,
                    final_result__isnull=True
                ).distinct().count()
                ecarts_by_order[f"nombre_{counting_order}er"] = ecarts_count

            # Créer un dictionnaire des assignments existants par counting_order
            assignments_by_order = {}
            for assignment in assignments:
                if hasattr(assignment, 'counting') and assignment.counting:
                    counting_order = assignment.counting.order

                    # Calculer le nombre d'écarts pour ce counting_order
                    counting_details_with_ecarts = ComptageSequence.objects.filter(
                        counting_detail__job=job,
                        counting_detail__counting__order=counting_order,
                        ecart_comptage__final_result__isnull=True
                    ).values_list('counting_detail', flat=True).distinct()

                    ecarts_count = counting_details_with_ecarts.count()

                    # Récupérer le username de la session associée
                    session_username = ""
                    mobile_assignment = assignment.counting.assigment_set.filter(
                        session__isnull=False  # Assignment mobile (avec session)
                    ).first()
                    if mobile_assignment and mobile_assignment.session:
                        session_username = mobile_assignment.session.username or ""

                    assignments_by_order[counting_order] = {
                        'counting_order': counting_order,
                        'status': assignment.status or "",
                        'username': session_username
                    }

            # Standardiser : créer des assignments pour tous les counting_orders de 1 à max
            simplified_assignments = []
            for counting_order in range(1, max_counting_order + 1):
                if counting_order in assignments_by_order:
                    # Assignment existant
                    simplified_assignments.append(assignments_by_order[counting_order])
                else:
                    # Assignment manquant - calculer les écarts pour ce counting_order
                    # Nombre de CountingDetail distincts avec ce counting_order qui ont au moins une ComptageSequence avec final_result null
                    counting_details_with_ecarts = ComptageSequence.objects.filter(
                        counting_detail__job=job,
                        counting_detail__counting__order=counting_order,
                        ecart_comptage__final_result__isnull=True
                    ).values_list('counting_detail', flat=True).distinct()

                    ecarts_count = counting_details_with_ecarts.count()

                    simplified_assignments.append({
                        'counting_order': counting_order,
                        'status': "",  # Pas d'assignment
                        'username': ""  # Pas d'utilisateur assigné
                    })

            # Construire les données au format attendu par la vue
            job_data = {
                'job_id': job.id,
                'job_reference': job.reference,
                'job_status': job.status,
                'assignments': simplified_assignments,
                'nombre_comptage': nombre_comptage,  # ✅ Votre champ demandé
                'ecart_1_vs_2_count': ecart_1_vs_2_count,
                'ecart_1_vs_2_rate': round(ecart_1_vs_2_rate, 2),
                'nombre_ecart_3er': nombre_ecart_3er,
                'discrepancy_count': nombre_comptage,  # Pour compatibilité DataTable
                'discrepancy_rate': round(ecart_1_vs_2_rate, 2),  # Pour compatibilité DataTable
                'total_lines_counting_1': total_results_1_2,
                'total_lines_counting_2': total_results_1_2,
                'common_lines_count': total_results_1_2,
                'total_emplacements': total_results_1_2,
            }

            # Ajouter les écarts dynamiques (nombre_3er, nombre_4er, etc.)
            job_data.update(ecarts_by_order)

            result.append(job_data)

        return result

