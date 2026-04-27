"""
Vue pour la generation de PDF des jobs d'inventaire
"""
import threading
from pathlib import PurePosixPath

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.db import close_old_connections
from django.utils import timezone
from ..serializers.job_serializer import InventoryJobsPdfRequestSerializer
from ..usecases.inventory_jobs_pdf import InventoryJobsPdfUseCase
from ..usecases.job_assignment_pdf import JobAssignmentPdfUseCase
from ..models import Inventory, Job, PdfTask, Assigment
from ..exceptions.pdf_exceptions import (
    PDFGenerationError,
    PDFValidationError,
    PDFNotFoundError,
    PDFEmptyContentError,
    PDFServiceError,
    PDFRepositoryError
)
import logging

logger = logging.getLogger(__name__)


def _normalize_output_subpath(output_subpath):
    """
    Normalise un sous-chemin relatif de sortie pour le FileField.
    Exemples valides:
      - JOB-0001/comptage-01.pdf
      - JOB-0001\\comptage-01.pdf
    """
    if not output_subpath:
        return None
    normalized = str(PurePosixPath(str(output_subpath).replace("\\", "/")))
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    return normalized or None


def enqueue_job_assignment_pdf_task(job_id, assignment_id, equipe_id=None, output_subpath=None):
    """
    Crée et lance une tâche asynchrone de génération PDF job/assignment.
    Retourne l'instance PdfTask créée.
    """
    task = PdfTask.objects.create(
        task_type=PdfTask.TYPE_JOB_ASSIGNMENT_PDF,
        params={
            "job_id": int(job_id),
            "assignment_id": int(assignment_id),
            "equipe_id": equipe_id,
            "output_subpath": _normalize_output_subpath(output_subpath),
        },
        status=PdfTask.STATUS_PENDING,
    )

    threading.Thread(target=_run_job_assignment_pdf_task, args=(task.id,), daemon=True).start()
    return task

def _parse_job_ids_from_request_data(data):
    """
    Récupère et normalise le paramètre optionnel job / job[].
    Retourne une liste d'entiers ou None.
    Lève ValueError si le format est invalide.
    """
    job_ids = data.get("job", None) or data.get("job[]", None)
    if not job_ids:
        return None
    if isinstance(job_ids, list):
        return [int(job_id) for job_id in job_ids]
    if isinstance(job_ids, str):
        return [int(job_id.strip()) for job_id in job_ids.split(",") if job_id.strip()]
    return [int(job_ids)]


def _run_inventory_jobs_pdf_task(task_id):
    """
    Exécute la génération PDF en arrière-plan.
    IMPORTANT: utilisé depuis un thread (sans Celery).
    """
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

        # Nom de fichier
        try:
            inventory = Inventory.objects.get(id=inventory_id)
            inventory_ref = inventory.reference
        except Inventory.DoesNotExist:
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

    except Exception as e:
        logger.error(f"Echec génération PDF async task={task_id}: {str(e)}", exc_info=True)
        task.status = PdfTask.STATUS_ERROR
        task.error_message = str(e)
        task.save(update_fields=["status", "error_message", "updated_at"])
    finally:
        close_old_connections()

def _run_job_assignment_pdf_task(task_id):
    """
    Exécute la génération du PDF job/assignment en arrière-plan.
    """
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

        try:
            job = Job.objects.get(id=job_id)
            job_reference = job.reference
        except Job.DoesNotExist:
            job_reference = f"job_{job_id}"

        output_subpath = _normalize_output_subpath(task.params.get("output_subpath"))
        filename = output_subpath or f"FICHE DE COMPTAGE : {job_reference}.pdf"
        task.result_file.save(filename, ContentFile(pdf_content))

        task.status = PdfTask.STATUS_SUCCESS
        task.save(update_fields=["status", "result_file", "updated_at"])

    except Exception as e:
        logger.error(f"Echec génération PDF job assignment async task={task_id}: {str(e)}", exc_info=True)
        task.status = PdfTask.STATUS_ERROR
        task.error_message = str(e)
        task.save(update_fields=["status", "error_message", "updated_at"])
    finally:
        close_old_connections()


class InventoryJobsPdfView(APIView):
    """Vue pour generer le PDF des jobs d'inventaire"""
    
    def post(self, request, inventory_id):
        """
        Genere un PDF des jobs d'un inventaire
        
        URL params:
            inventory_id: ID de l'inventaire
        
        Body params (optionnel):
            job: Liste des IDs de jobs à exporter (si fourni, exporte uniquement ces jobs avec assignments PRET ou TRANSFERT)
        
        Returns:
            PDF file
        """
        # Pas de counting_id - on génère pour tous les comptages
        counting_id = None
        
        # Récupérer le paramètre optionnel job[] depuis le body
        # Supporte 'job' et 'job[]' comme noms de paramètre
        try:
            job_ids = _parse_job_ids_from_request_data(request.data)
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur lors de la conversion des job IDs: {str(e)}")
            return Response(
                {"success": False, "message": "job doit être une liste d'entiers ou un entier"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Valider l'inventory_id
        if not inventory_id:
            return Response({
                'success': False,
                'message': 'inventory_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logger.info(f"Début de la génération du PDF pour l'inventaire {inventory_id}")
            if job_ids:
                logger.info(f"Filtrage par job IDs: {job_ids}")
            else:
                logger.info("Export de tous les jobs avec assignments PRET ou TRANSFERT")
            
            # Executer le use case
            use_case = InventoryJobsPdfUseCase()
            result = use_case.execute(inventory_id, counting_id, job_ids=job_ids)
            
            if result['success']:
                # Retourner le PDF
                pdf_buffer = result['pdf_buffer']
                
                # Vérifier que le buffer contient des données
                pdf_content = pdf_buffer.getvalue()
                pdf_size = len(pdf_content)
                
                logger.info(f"PDF généré avec succès. Taille: {pdf_size} bytes")
                
                if pdf_size == 0:
                    logger.error(f"Le PDF généré est vide pour l'inventaire {inventory_id}")
                    return Response({
                        'success': False,
                        'message': 'Le PDF généré est vide. Vérifiez qu\'il y a des jobs avec des données pour cet inventaire.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Vérifier que c'est bien un PDF (commence par %PDF)
                if not pdf_content.startswith(b'%PDF'):
                    logger.error(f"Le contenu généré n'est pas un PDF valide pour l'inventaire {inventory_id}")
                    return Response({
                        'success': False,
                        'message': 'Le contenu généré n\'est pas un PDF valide'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Récupérer la référence de l'inventaire pour le nom du fichier
                try:
                    inventory = Inventory.objects.get(id=inventory_id)
                    inventory_ref = inventory.reference
                except Inventory.DoesNotExist:
                    inventory_ref = str(inventory_id)
                
                # Definir le nom du fichier au format "Job inventaire (ref d'inventaire)"
                filename = f"Job inventaire ({inventory_ref}).pdf"
                
                # Creer la reponse HTTP avec le PDF
                response = HttpResponse(
                    pdf_content,
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = str(pdf_size)
                
                logger.info(f"PDF retourné avec succès. Nom: {filename}, Taille: {pdf_size} bytes")
                
                return response
            else:
                logger.error(f"Le use case a retourné success=False pour l'inventaire {inventory_id}")
                return Response({
                    'success': False,
                    'message': 'Erreur lors de la generation du PDF'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except (ValueError, PDFValidationError) as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return Response({
                'success': False,
                'message': str(e),
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except PDFNotFoundError as e:
            logger.warning(f"Ressource non trouvée: {str(e)}")
            return Response({
                'success': False,
                'message': str(e),
                'error_type': 'not_found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except PDFEmptyContentError as e:
            logger.warning(f"Aucun contenu à générer: {str(e)}")
            return Response({
                'success': False,
                'message': str(e),
                'error_type': 'empty_content'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (PDFServiceError, PDFRepositoryError) as e:
            logger.error(f"Erreur de service/repository: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f"Erreur lors de la génération du PDF: {str(e)}",
                'error_type': 'service_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except PDFGenerationError as e:
            logger.error(f"Erreur de génération PDF: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e),
                'error_type': 'generation_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except DjangoValidationError as e:
            logger.error(f"Erreur de validation Django: {str(e)}")
            error_message = str(e)
            if hasattr(e, 'message_dict'):
                error_message = ', '.join([f"{k}: {v}" for k, v in e.message_dict.items()])
            return Response({
                'success': False,
                'message': f"Erreur de validation: {error_message}",
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la generation du PDF: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Une erreur inattendue s\'est produite lors de la génération du PDF',
                'error_type': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InventoryJobsPdfAsyncStartView(APIView):
    """
    Lance une génération PDF asynchrone et retourne un task_id.
    """

    def post(self, request, inventory_id):
        if not inventory_id:
            return Response(
                {"success": False, "message": "inventory_id est requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job_ids = _parse_job_ids_from_request_data(request.data)
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur lors de la conversion des job IDs: {str(e)}")
            return Response(
                {"success": False, "message": "job doit être une liste d'entiers ou un entier"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = PdfTask.objects.create(
            task_type=PdfTask.TYPE_INVENTORY_JOBS_PDF,
            params={"inventory_id": int(inventory_id), "job_ids": job_ids},
            status=PdfTask.STATUS_PENDING,
        )

        threading.Thread(target=_run_inventory_jobs_pdf_task, args=(task.id,), daemon=True).start()

        return Response(
            {"success": True, "task_id": str(task.id), "status": task.status},
            status=status.HTTP_202_ACCEPTED,
        )


class InventoryWarehouseFinishedAssignmentsPdfAsyncStartView(APIView):
    """
    Lance une génération PDF asynchrone pour les jobs d'un inventaire/entrepôt
    dont les assignments sont TERMINE et non imprimés.
    """

    def post(self, request, inventory_id, warehouse_id):
        if not inventory_id or not warehouse_id:
            return Response(
                {"success": False, "message": "inventory_id et warehouse_id sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignments = Assigment.objects.filter(
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id,
            status="TERMINE",
            imprime=False,
        ).select_related("job")

        if not assignments.exists():
            return Response(
                {
                    "success": False,
                    "message": "Aucun assignment TERMINE non imprimé trouvé pour cet inventaire et entrepôt",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment_ids = list(assignments.values_list("id", flat=True))
        job_ids = list(assignments.values_list("job_id", flat=True).distinct())

        task = PdfTask.objects.create(
            task_type=PdfTask.TYPE_INVENTORY_JOBS_PDF,
            params={
                "inventory_id": int(inventory_id),
                "warehouse_id": int(warehouse_id),
                "job_ids": job_ids,
                "assignment_statuses": ["TERMINE"],
                "job_statuses": [],
                "assignment_ids_to_mark": assignment_ids,
            },
            status=PdfTask.STATUS_PENDING,
        )

        threading.Thread(target=_run_inventory_jobs_pdf_task, args=(task.id,), daemon=True).start()

        return Response(
            {
                "success": True,
                "task_id": str(task.id),
                "status": task.status,
                "jobs_count": len(job_ids),
                "assignments_count": len(assignment_ids),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class JobAssignmentPdfAsyncStartView(APIView):
    """
    Lance une génération PDF job/assignment en asynchrone et retourne un task_id.
    """

    def post(self, request, job_id, assignment_id):
        if not job_id or not assignment_id:
            return Response(
                {"success": False, "message": "job_id et assignment_id sont requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        equipe_id = request.data.get("equipe_id", None)
        if equipe_id not in ("", None):
            try:
                equipe_id = int(equipe_id)
            except (ValueError, TypeError):
                return Response(
                    {"success": False, "message": "equipe_id doit etre un nombre entier"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        task = enqueue_job_assignment_pdf_task(
            job_id=job_id,
            assignment_id=assignment_id,
            equipe_id=equipe_id,
        )

        return Response(
            {"success": True, "task_id": str(task.id), "status": task.status},
            status=status.HTTP_202_ACCEPTED,
        )


class PdfTaskStatusView(APIView):
    """
    Retourne le statut d'une tâche PDF et l'URL de téléchargement si prête.
    """

    def get(self, request, task_id):
        try:
            task = PdfTask.objects.get(id=task_id)
        except PdfTask.DoesNotExist:
            return Response(
                {"success": False, "message": "Tâche PDF introuvable"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "success": True,
            "task_id": str(task.id),
            "task_type": task.task_type,
            "status": task.status,
            "error_message": task.error_message,
        }

        if task.status == PdfTask.STATUS_SUCCESS and task.result_file:
            data["download_url"] = request.build_absolute_uri(task.result_file.url)

        return Response(data, status=status.HTTP_200_OK)


class AssignmentGeneratedPdfListView(APIView):
    """
    Liste les PDFs générés pour les assignments terminés, triés par référence job.
    """

    def get(self, request):
        tasks = PdfTask.objects.filter(
            task_type=PdfTask.TYPE_JOB_ASSIGNMENT_PDF
        ).order_by("-created_at")

        assignment_ids = set()
        task_assignment_map = {}
        for task in tasks:
            assignment_id = task.params.get("assignment_id")
            try:
                assignment_id = int(assignment_id)
            except (TypeError, ValueError):
                assignment_id = None
            task_assignment_map[task.id] = assignment_id
            if assignment_id is not None:
                assignment_ids.add(assignment_id)

        assignments = Assigment.objects.filter(
            id__in=assignment_ids,
            status="TERMINE",
        ).select_related("job", "counting")
        assignments_map = {assignment.id: assignment for assignment in assignments}

        grouped = {}
        for task in tasks:
            assignment_id = task_assignment_map.get(task.id)
            if assignment_id is None:
                continue

            assignment = assignments_map.get(assignment_id)
            if not assignment:
                continue

            job_key = assignment.job_id
            if job_key not in grouped:
                grouped[job_key] = {
                    "job": {
                        "id": assignment.job_id,
                        "reference": assignment.job.reference,
                        "status": assignment.job.status,
                    },
                    "pdfs": [],
                }

            item = {
                "task_id": str(task.id),
                "task_status": task.status,
                "task_type": task.task_type,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "error_message": task.error_message,
                "assignment": {
                    "id": assignment.id,
                    "reference": assignment.reference,
                    "status": assignment.status,
                    "counting_order": assignment.counting.order if assignment.counting else None,
                },
                "pdf_path": task.result_file.name if task.result_file else None,
                "download_url": None,
            }

            if task.status == PdfTask.STATUS_SUCCESS and task.result_file:
                item["download_url"] = request.build_absolute_uri(task.result_file.url)

            grouped[job_key]["pdfs"].append(item)

        results = list(grouped.values())
        for group in results:
            group["pdfs"].sort(key=lambda x: (x["assignment"]["counting_order"] or 0, x["created_at"] or ""))

        results.sort(key=lambda x: (x["job"]["reference"] or ""))

        return Response(
            {
                "success": True,
                "count_jobs": len(results),
                "count_pdfs": sum(len(group["pdfs"]) for group in results),
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class JobAssignmentPdfView(APIView):
    """Vue pour generer le PDF d'un job/assignment/equipe"""
    
    def post(self, request, job_id, assignment_id):
        """
        Genere un PDF pour un job/assignment/equipe specifique
        
        URL params:
            job_id: ID du job
            assignment_id: ID de l'assignment
        
        Body params (optionnel):
            equipe_id: ID de l'equipe (personne ou personne_two)
        
        Returns:
            PDF file
        """
        # Recuperer equipe_id depuis le body si fourni
        equipe_id = request.data.get('equipe_id', None)
        if equipe_id:
            try:
                equipe_id = int(equipe_id)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'equipe_id doit etre un nombre entier'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider les parametres
        if not job_id:
            return Response({
                'success': False,
                'message': 'job_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not assignment_id:
            return Response({
                'success': False,
                'message': 'assignment_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Executer le use case
            use_case = JobAssignmentPdfUseCase()
            result = use_case.execute(job_id, assignment_id, equipe_id)
            
            if result['success']:
                # Retourner le PDF
                pdf_buffer = result['pdf_buffer']
                
                # Récupérer le job pour obtenir sa référence (pour le titre)
                try:
                    job = Job.objects.get(id=job_id)
                    job_reference = job.reference
                except Job.DoesNotExist:
                    job_reference = f"job_{job_id}"
                
                # Definir le nom du fichier avec le titre "FICHE DE COMPTAGE : {job_reference}"
                filename = f"FICHE DE COMPTAGE : {job_reference}.pdf"
                
                # Creer la reponse HTTP avec le PDF
                response = HttpResponse(
                    pdf_buffer.getvalue(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de la generation du PDF'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la generation du PDF: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
