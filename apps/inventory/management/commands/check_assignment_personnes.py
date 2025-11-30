"""
Commande pour vérifier les assignments et leurs personnes dans la base de données
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import Assigment, Personne
from django.db.models import Q


class Command(BaseCommand):
    help = 'Vérifie les assignments et leurs personnes associées dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assignment-id',
            type=int,
            help='ID de l\'assignment à vérifier spécifiquement',
        )
        parser.add_argument(
            '--job-id',
            type=int,
            help='ID du job pour filtrer les assignments',
        )

    def handle(self, *args, **options):
        assignment_id = options.get('assignment_id')
        job_id = options.get('job_id')

        self.stdout.write(self.style.SUCCESS('=== Vérification des Assignments et Personnes ===\n'))

        # Construire la requête
        queryset = Assigment.objects.select_related(
            'personne',
            'personne_two',
            'job',
            'counting',
            'session'
        ).all()

        if assignment_id:
            queryset = queryset.filter(id=assignment_id)
            self.stdout.write(f'Filtrage par assignment ID: {assignment_id}\n')
        
        if job_id:
            queryset = queryset.filter(job_id=job_id)
            self.stdout.write(f'Filtrage par job ID: {job_id}\n')

        assignments = queryset.order_by('-id')[:50]  # Limiter à 50 pour l'affichage

        if not assignments:
            self.stdout.write(self.style.WARNING('Aucun assignment trouvé.'))
            return

        self.stdout.write(f'Nombre d\'assignments trouvés: {len(assignments)}\n')
        self.stdout.write('-' * 100)

        for assignment in assignments:
            self.stdout.write(f'\nAssignment ID: {assignment.id}')
            self.stdout.write(f'  Référence: {assignment.reference}')
            self.stdout.write(f'  Statut: {assignment.status}')
            self.stdout.write(f'  Job ID: {assignment.job_id} - {assignment.job.reference if assignment.job else "N/A"}')
            self.stdout.write(f'  Counting: {assignment.counting.reference if assignment.counting else "N/A"} (Ordre: {assignment.counting.order if assignment.counting else "N/A"})')
            self.stdout.write(f'  Session: {assignment.session.username if assignment.session else "NULL"}')
            
            # Vérifier personne
            if assignment.personne:
                self.stdout.write(self.style.SUCCESS(f'  Personne 1: ID={assignment.personne.id}, Nom="{assignment.personne.nom}", Prénom="{assignment.personne.prenom}"'))
                self.stdout.write(f'    Nom complet: "{assignment.personne.nom} {assignment.personne.prenom}"')
            else:
                self.stdout.write(self.style.WARNING('  Personne 1: NULL'))
            
            # Vérifier personne_two
            if assignment.personne_two:
                self.stdout.write(self.style.SUCCESS(f'  Personne 2: ID={assignment.personne_two.id}, Nom="{assignment.personne_two.nom}", Prénom="{assignment.personne_two.prenom}"'))
                self.stdout.write(f'    Nom complet: "{assignment.personne_two.nom} {assignment.personne_two.prenom}"')
            else:
                self.stdout.write(self.style.WARNING('  Personne 2: NULL'))
            
            # Vérifier si les noms commencent par AGL ou L'Oréal
            if assignment.personne:
                nom_complet = f"{assignment.personne.nom} {assignment.personne.prenom}".strip()
                nom_seul = assignment.personne.nom or ''
                if nom_seul.lower().startswith('agl') or nom_complet.lower().startswith('agl'):
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Personne 1 commence par AGL'))
                elif nom_seul.lower().startswith(('l\'oreal', 'loreal', 'oreal', 'l\'oréal', 'loréal')) or nom_complet.lower().startswith(('l\'oreal', 'loreal', 'oreal', 'l\'oréal', 'loréal')):
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Personne 1 commence par L\'Oréal'))
                else:
                    self.stdout.write(self.style.WARNING(f'    ✗ Personne 1 ne commence ni par AGL ni par L\'Oréal'))
            
            if assignment.personne_two:
                nom_complet = f"{assignment.personne_two.nom} {assignment.personne_two.prenom}".strip()
                nom_seul = assignment.personne_two.nom or ''
                if nom_seul.lower().startswith('agl') or nom_complet.lower().startswith('agl'):
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Personne 2 commence par AGL'))
                elif nom_seul.lower().startswith(('l\'oreal', 'loreal', 'oreal', 'l\'oréal', 'loréal')) or nom_complet.lower().startswith(('l\'oreal', 'loreal', 'oreal', 'l\'oréal', 'loréal')):
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Personne 2 commence par L\'Oréal'))
                else:
                    self.stdout.write(self.style.WARNING(f'    ✗ Personne 2 ne commence ni par AGL ni par L\'Oréal'))
            
            self.stdout.write('-' * 100)

        # Statistiques
        total = Assigment.objects.count()
        with_personne = Assigment.objects.exclude(personne__isnull=True).count()
        with_personne_two = Assigment.objects.exclude(personne_two__isnull=True).count()
        with_both = Assigment.objects.exclude(personne__isnull=True).exclude(personne_two__isnull=True).count()
        without_any = Assigment.objects.filter(personne__isnull=True, personne_two__isnull=True).count()

        self.stdout.write(f'\n=== Statistiques ===')
        self.stdout.write(f'Total assignments: {total}')
        self.stdout.write(f'  Avec personne 1: {with_personne} ({with_personne*100/total:.1f}%)')
        self.stdout.write(f'  Avec personne 2: {with_personne_two} ({with_personne_two*100/total:.1f}%)')
        self.stdout.write(f'  Avec les deux: {with_both} ({with_both*100/total:.1f}%)')
        self.stdout.write(f'  Sans aucune personne: {without_any} ({without_any*100/total:.1f}%)')

        # Vérifier les personnes avec AGL ou L'Oréal dans leur nom
        personnes_agl = Personne.objects.filter(
            Q(nom__istartswith='AGL') | Q(nom__istartswith='agl')
        ).count()
        personnes_loreal = Personne.objects.filter(
            Q(nom__istartswith='L\'Oréal') | Q(nom__istartswith='L\'oreal') | 
            Q(nom__istartswith='Loreal') | Q(nom__istartswith='loreal') |
            Q(nom__istartswith='Oreal') | Q(nom__istartswith='oreal') |
            Q(nom__istartswith='L\'oréal') | Q(nom__istartswith='Loréal')
        ).count()

        self.stdout.write(f'\nPersonnes dans la base:')
        self.stdout.write(f'  Commençant par AGL: {personnes_agl}')
        self.stdout.write(f'  Commençant par L\'Oréal: {personnes_loreal}')

