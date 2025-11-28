"""
Commande pour verifier et corriger la valeur de counting.dlc dans la base de donnees
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import Counting, Assignment


class Command(BaseCommand):
    help = 'Verifie et corrige la valeur de counting.dlc dans la base de donnees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assignment-id',
            type=int,
            help='ID de l\'assignment a verifier (optionnel)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corriger automatiquement les valeurs incorrectes',
        )
        parser.add_argument(
            '--counting-id',
            type=int,
            help='ID du counting a verifier (optionnel)',
        )

    def handle(self, *args, **options):
        assignment_id = options.get('assignment_id')
        counting_id = options.get('counting_id')
        fix = options.get('fix', False)

        if assignment_id:
            # Verifier un assignment specifique
            try:
                assignment = Assignment.objects.get(id=assignment_id)
                counting = assignment.counting
                if counting:
                    self.check_and_fix_counting(counting, fix, assignment_id)
                else:
                    self.stdout.write(self.style.ERROR(f'Assignment {assignment_id} n\'a pas de counting'))
            except Assignment.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Assignment {assignment_id} non trouve'))
        elif counting_id:
            # Verifier un counting specifique
            try:
                counting = Counting.objects.get(id=counting_id)
                self.check_and_fix_counting(counting, fix)
            except Counting.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Counting {counting_id} non trouve'))
        else:
            # Verifier tous les countings
            self.stdout.write(self.style.WARNING('Verification de tous les countings...'))
            countings = Counting.objects.all()
            for counting in countings:
                self.check_and_fix_counting(counting, fix)

    def check_and_fix_counting(self, counting, fix=False, assignment_id=None):
        """Verifie et corrige un counting"""
        self.stdout.write(f'\n--- Counting: {counting.reference} (ID: {counting.id}) ---')
        self.stdout.write(f'Mode de comptage: {counting.count_mode}')
        self.stdout.write(f'DLC actuel: {counting.dlc}')
        
        # Determiner si DLC devrait etre active
        should_have_dlc = self.should_have_dlc(counting)
        
        if counting.dlc != should_have_dlc:
            self.stdout.write(self.style.WARNING(
                f'PROBLEME: counting.dlc est {counting.dlc} mais devrait etre {should_have_dlc}'
            ))
            if assignment_id:
                self.stdout.write(self.style.WARNING(f'  Assignment ID: {assignment_id}'))
            
            if fix:
                counting.dlc = should_have_dlc
                counting.save()
                self.stdout.write(self.style.SUCCESS(f'  CORRIGE: counting.dlc mis a {should_have_dlc}'))
            else:
                self.stdout.write(self.style.WARNING(
                    '  Utilisez --fix pour corriger automatiquement'
                ))
        else:
            self.stdout.write(self.style.SUCCESS('  OK: La valeur de counting.dlc est correcte'))

    def should_have_dlc(self, counting):
        """
        Determine si un counting devrait avoir DLC active
        Retourne False pour les modes de comptage qui ne supportent pas DLC
        """
        # Si le mode de comptage contient "image" ou "vrac", ne pas avoir DLC
        if 'image' in counting.count_mode.lower():
            return False
        if 'vrac' in counting.count_mode.lower():
            return False
        # Par defaut, retourner la valeur actuelle (ne pas forcer de changement)
        # Mais on peut ajouter d'autres regles ici
        return counting.dlc

