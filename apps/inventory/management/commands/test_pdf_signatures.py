"""
Commande pour tester la génération du PDF et voir les logs des signatures
"""
from django.core.management.base import BaseCommand
from apps.inventory.services.pdf_service import PDFService
import logging
import sys

# Configurer le logging pour afficher tous les messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Command(BaseCommand):
    help = 'Teste la génération du PDF et affiche les logs des signatures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=int,
            required=True,
            help='ID du job',
        )
        parser.add_argument(
            '--assignment-id',
            type=int,
            required=True,
            help='ID de l\'assignment',
        )

    def handle(self, *args, **options):
        job_id = options['job_id']
        assignment_id = options['assignment_id']
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Test de génération du PDF avec signatures'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'Job ID: {job_id}')
        self.stdout.write(f'Assignment ID: {assignment_id}')
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        try:
            pdf_service = PDFService()
            pdf_buffer = pdf_service.generate_job_assignment_pdf(
                job_id=job_id,
                assignment_id=assignment_id,
                equipe_id=None
            )
            
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            self.stdout.write(self.style.SUCCESS('PDF généré avec succès!'))
            self.stdout.write(f'Taille du buffer: {len(pdf_buffer.getvalue())} bytes')
            self.stdout.write('=' * 80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERREUR lors de la génération: {str(e)}'))
            import traceback
            traceback.print_exc()

