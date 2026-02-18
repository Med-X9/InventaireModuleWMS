"""
Repository pour la récupération des jobs dans l'application mobile.
"""
from apps.inventory.models import Job, Assigment


class JobRepository:
    """Repository pour les jobs (contexte mobile)."""

    def get_jobs_with_both_countings_terminated(
        self,
        inventory_id=None,
        warehouse_id=None,
    ):
        """
        Récupère les jobs dont le 1er et le 2ème comptage sont terminés (assignments TERMINE).

        Un job est retourné s'il possède au moins un assignment TERMINE pour le comptage
        d'ordre 1 ET au moins un assignment TERMINE pour le comptage d'ordre 2.

        Args:
            inventory_id: Filtre optionnel par ID d'inventaire.
            warehouse_id: Filtre optionnel par ID d'entrepôt.

        Returns:
            Queryset des Job avec select_related pour warehouse et inventory.
        """
        job_ids_counting_1 = Assigment.objects.filter(
            counting__order=1,
            status='TERMINE',
        ).values_list('job_id', flat=True)

        job_ids_counting_2 = Assigment.objects.filter(
            counting__order=2,
            status='TERMINE',
        ).values_list('job_id', flat=True)

        # Jobs présents dans les deux listes
        job_ids_both = set(job_ids_counting_1) & set(job_ids_counting_2)

        queryset = Job.objects.filter(id__in=job_ids_both).select_related(
            'warehouse',
            'inventory',
        ).order_by('reference')

        if inventory_id is not None:
            queryset = queryset.filter(inventory_id=inventory_id)
        if warehouse_id is not None:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return queryset
