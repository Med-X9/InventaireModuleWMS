"""
Commande Django pour vérifier le statut d'un ImportTask
"""
from django.core.management.base import BaseCommand
from apps.masterdata.models import ImportTask, ImportError


class Command(BaseCommand):
    help = 'Vérifie le statut d\'un ImportTask et ses erreurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--import-task-id',
            type=int,
            required=True,
            help='ID de la tâche d\'import à vérifier',
        )

    def handle(self, *args, **options):
        import_task_id = options.get('import_task_id')

        try:
            task = ImportTask.objects.get(id=import_task_id)
            
            self.stdout.write(f"\n=== Import Task ID {import_task_id} ===")
            self.stdout.write(f"Status: {task.status}")
            self.stdout.write(f"Error message: {task.error_message}")
            self.stdout.write(f"Imported: {task.imported_count}")
            self.stdout.write(f"Updated: {task.updated_count}")
            self.stdout.write(f"Error count: {task.error_count}")
            self.stdout.write(f"Total rows: {task.total_rows}")
            self.stdout.write(f"Validated rows: {task.validated_rows}")
            self.stdout.write(f"Processed rows: {task.processed_rows}")
            self.stdout.write(f"Created at: {task.created_at}")
            self.stdout.write(f"Updated at: {task.updated_at}")
            
            errors = ImportError.objects.filter(import_task=task)
            self.stdout.write(f"\nNombre d'erreurs enregistrées: {errors.count()}")
            if errors.exists():
                self.stdout.write("\nPremières erreurs:")
                for e in errors[:20]:
                    self.stdout.write(f"  Ligne {e.row_number}: [{e.error_type}] {e.error_message}")
                    if e.field_name:
                        self.stdout.write(f"    Champ: {e.field_name}, Valeur: {e.field_value}")
            else:
                self.stdout.write(self.style.WARNING("Aucune erreur enregistrée dans ImportError"))
                    
        except ImportTask.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"ImportTask ID {import_task_id} n'existe pas"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {str(e)}"))
            import traceback
            traceback.print_exc()
