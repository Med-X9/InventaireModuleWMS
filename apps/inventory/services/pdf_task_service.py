"""
Service de tâches PDF asynchrones.

Découple la couche HTTP (views) de l'enqueueing des tâches PDF,
et fournit un point d'extension pour remplacer le runner thread
par Celery / Huey / django-db-queue sans changer les appelants.
"""
from __future__ import annotations

import logging
import threading
from pathlib import PurePosixPath
from typing import Any, Callable, List, Optional

from django.core.files.base import ContentFile
from django.db import close_old_connections
from django.utils import timezone

from apps.inventory.models import Assigment, Inventory, Job, PdfTask
from apps.inventory.exceptions.pdf_exceptions import (
    PDFEmptyContentError,
    PDFGenerationError,
)
from apps.inventory.usecases.inventory_jobs_pdf import InventoryJobsPdfUseCase
from apps.inventory.usecases.job_assignment_pdf import JobAssignmentPdfUseCase
from apps.inventory.services.inventory_service import InventoryService
from apps.inventory.services.assignment_service import AssignmentService
from apps.inventory.services.job_service import JobService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstraction runner (threads aujourd'hui, Celery demain)
# ---------------------------------------------------------------------------
TaskRunner = Callable[[Callable[..., Any], tuple], None]


def _thread_runner(target: Callable[..., Any], args: tuple) -> None:
    """Runner par défaut : thread daemon (compatible déploiement actuel)."""
    threading.Thread(target=target, args=args, daemon=True).start()


_default_runner: TaskRunner = _thread_runner


def set_task_runner(runner: TaskRunner) -> None:
    """
    Remplace le runner de tâches (tests, Celery, Huey…).

    Args:
        runner: Callable(target, args) qui planifie l'exécution.
    """
    global _default_runner
    _default_runner = runner


def get_task_runner() -> TaskRunner:
    """Retourne le runner de tâches courant."""
    return _default_runner


def normalize_output_subpath(output_subpath: Optional[str]) -> Optional[str]:
    """
    Normalise un sous-chemin relatif de sortie pour le FileField.
    """
    if not output_subpath:
        return None
    normalized = str(PurePosixPath(str(output_subpath).replace("\\", "/")))
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    return normalized or None


class PdfTaskService:
    """
    Orchestration des tâches PDF asynchrones (création + exécution).
    """

    def __init__(self, runner: Optional[TaskRunner] = None):
        self.runner = runner or get_task_runner()
        self.inventory_service = InventoryService()
        self.assignment_service = AssignmentService()
        self.job_service = JobService()

    def get_pdf_task_by_id(self, task_id: int) -> Optional[PdfTask]:
        """Récupère une tâche PDF par ID."""
        try:
            return PdfTask.objects.get(id=task_id)
        except PdfTask.DoesNotExist:
            return None

    def get_job_assignment_pdf_tasks(self):
        """Liste des tâches PDF job/assignment, les plus récentes en premier."""
        return PdfTask.objects.filter(
            task_type=PdfTask.TYPE_JOB_ASSIGNMENT_PDF
        ).order_by("-created_at")

    def get_finished_unprinted_assignments(
        self, inventory_id: int, warehouse_id: int
    ):
        """
        Assignments TERMINE non imprimés pour l'export PDF inventaire/entrepôt.
        """
        return self.assignment_service.get_finished_unprinted_assignments(
            inventory_id, warehouse_id
        )

    def get_inventory_reference_for_filename(self, inventory_id: int) -> str:
        """Référence inventaire pour nom de fichier PDF."""
        try:
            return self.inventory_service.get_inventory_by_id(inventory_id).reference
        except Exception:
            return str(inventory_id)

    def get_job_reference_for_filename(self, job_id: int) -> str:
        """Référence job pour nom de fichier PDF."""
        job = self.job_service.get_job_by_id(job_id)
        return job.reference if job else f"job_{job_id}"

    def enqueue_job_assignment_pdf_task(
        self,
        job_id: int,
        assignment_id: int,
        equipe_id: Optional[int] = None,
        output_subpath: Optional[str] = None,
    ) -> PdfTask:
        """
        Crée et lance une tâche asynchrone de génération PDF job/assignment.

        Returns:
            PdfTask: Instance créée (status PENDING).
        """
        task = PdfTask.objects.create(
            task_type=PdfTask.TYPE_JOB_ASSIGNMENT_PDF,
            params={
                "job_id": int(job_id),
                "assignment_id": int(assignment_id),
                "equipe_id": equipe_id,
                "output_subpath": normalize_output_subpath(output_subpath),
            },
            status=PdfTask.STATUS_PENDING,
        )
        self.runner(self.run_job_assignment_pdf_task, (task.id,))
        return task

    def enqueue_inventory_jobs_pdf_task(
        self,
        inventory_id: int,
        job_ids: Optional[List[int]] = None,
        assignment_statuses: Optional[List[str]] = None,
        job_statuses: Optional[List[str]] = None,
        assignment_ids_to_mark: Optional[List[int]] = None,
    ) -> PdfTask:
        """Crée et lance une tâche PDF jobs d'inventaire."""
        task = PdfTask.objects.create(
            task_type=PdfTask.TYPE_INVENTORY_JOBS_PDF,
            params={
                "inventory_id": int(inventory_id),
                "job_ids": job_ids,
                "assignment_statuses": assignment_statuses,
                "job_statuses": job_statuses,
                "assignment_ids_to_mark": assignment_ids_to_mark,
            },
            status=PdfTask.STATUS_PENDING,
        )
        self.runner(self.run_inventory_jobs_pdf_task, (task.id,))
        return task

    @staticmethod
    def run_inventory_jobs_pdf_task(task_id: int) -> None:
        """Exécute la génération PDF inventaire/jobs en arrière-plan."""
        close_old_connections()
        try:
            task = PdfTask.objects.get(id=task_id)
        except PdfTask.DoesNotExist:
            return

        task.status = PdfTask.STATUS_RUNNING
        task.error_message = None
        task.save(update_fields=["status", "error_message", "updated_at"])

        try:
            inventory_id = int(task.params.get("inventory_id"))
            job_ids = task.params.get("job_ids", None)
            assignment_statuses = task.params.get("assignment_statuses", None)
            job_statuses = task.params.get("job_statuses", None)
            assignment_ids_to_mark = task.params.get("assignment_ids_to_mark", None)

            if isinstance(job_ids, list):
                job_ids = [int(x) for x in job_ids]
            elif job_ids is None:
                job_ids = None
            else:
                job_ids = [int(job_ids)]

            if isinstance(assignment_statuses, str):
                assignment_statuses = [assignment_statuses]
            if isinstance(job_statuses, str):
                job_statuses = [job_statuses]
            if isinstance(assignment_ids_to_mark, list):
                assignment_ids_to_mark = [int(x) for x in assignment_ids_to_mark]
            else:
                assignment_ids_to_mark = None

            use_case = InventoryJobsPdfUseCase()
            result = use_case.execute(
                inventory_id,
                counting_id=None,
                job_ids=job_ids,
                assignment_statuses=assignment_statuses,
                job_statuses=job_statuses,
            )
            pdf_buffer = result["pdf_buffer"]
            pdf_content = pdf_buffer.getvalue()

            if not pdf_content or len(pdf_content) == 0:
                raise PDFEmptyContentError("Le PDF généré est vide")
            if not pdf_content.startswith(b"%PDF"):
                raise PDFGenerationError("Le contenu généré n'est pas un PDF valide")

            try:
                inventory_ref = PdfTaskService().get_inventory_reference_for_filename(
                    inventory_id
                )
            except Exception:
                inventory_ref = str(inventory_id)

            filename = f"Job inventaire ({inventory_ref}).pdf"
            task.result_file.save(filename, ContentFile(pdf_content))

            task.status = PdfTask.STATUS_SUCCESS
            task.save(update_fields=["status", "result_file", "updated_at"])

            if assignment_ids_to_mark:
                Assigment.objects.filter(
                    id__in=assignment_ids_to_mark,
                    imprime=False,
                ).update(imprime=True, imprime_date=timezone.now())

        except Exception as exc:
            logger.error(
                "Echec génération PDF async task=%s: %s",
                task_id,
                str(exc),
                exc_info=True,
            )
            task.status = PdfTask.STATUS_ERROR
            task.error_message = str(exc)
            task.save(update_fields=["status", "error_message", "updated_at"])
        finally:
            close_old_connections()

    @staticmethod
    def run_job_assignment_pdf_task(task_id: int) -> None:
        """Exécute la génération du PDF job/assignment en arrière-plan."""
        close_old_connections()
        try:
            task = PdfTask.objects.get(id=task_id)
        except PdfTask.DoesNotExist:
            return

        task.status = PdfTask.STATUS_RUNNING
        task.error_message = None
        task.save(update_fields=["status", "error_message", "updated_at"])

        try:
            job_id = int(task.params.get("job_id"))
            assignment_id = int(task.params.get("assignment_id"))
            equipe_id = task.params.get("equipe_id", None)
            if equipe_id in ("", None):
                equipe_id = None
            else:
                equipe_id = int(equipe_id)

            use_case = JobAssignmentPdfUseCase()
            result = use_case.execute(job_id, assignment_id, equipe_id)
            pdf_buffer = result["pdf_buffer"]
            pdf_content = pdf_buffer.getvalue()

            if not pdf_content or len(pdf_content) == 0:
                raise PDFEmptyContentError("Le PDF généré est vide")
            if not pdf_content.startswith(b"%PDF"):
                raise PDFGenerationError("Le contenu généré n'est pas un PDF valide")

            job_reference = PdfTaskService().get_job_reference_for_filename(job_id)

            output_subpath = normalize_output_subpath(
                task.params.get("output_subpath")
            )
            filename = output_subpath or f"FICHE DE COMPTAGE : {job_reference}.pdf"
            task.result_file.save(filename, ContentFile(pdf_content))

            task.status = PdfTask.STATUS_SUCCESS
            task.save(update_fields=["status", "result_file", "updated_at"])

        except Exception as exc:
            logger.error(
                "Echec génération PDF job assignment async task=%s: %s",
                task_id,
                str(exc),
                exc_info=True,
            )
            task.status = PdfTask.STATUS_ERROR
            task.error_message = str(exc)
            task.save(update_fields=["status", "error_message", "updated_at"])
        finally:
            close_old_connections()


# ---------------------------------------------------------------------------
# API module-level (rétrocompatibilité avec les imports existants)
# ---------------------------------------------------------------------------
_pdf_task_service = PdfTaskService()


def enqueue_job_assignment_pdf_task(
    job_id: int,
    assignment_id: int,
    equipe_id: Optional[int] = None,
    output_subpath: Optional[str] = None,
) -> PdfTask:
    """Facade module-level pour l'enqueue job/assignment PDF."""
    return _pdf_task_service.enqueue_job_assignment_pdf_task(
        job_id=job_id,
        assignment_id=assignment_id,
        equipe_id=equipe_id,
        output_subpath=output_subpath,
    )


def enqueue_inventory_jobs_pdf_task(**kwargs) -> PdfTask:
    """Facade module-level pour l'enqueue inventaire/jobs PDF."""
    return _pdf_task_service.enqueue_inventory_jobs_pdf_task(**kwargs)
