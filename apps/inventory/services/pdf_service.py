"""
Service pour la generation de PDF des jobs d'inventaire
"""
from typing import Optional, List
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether, Image
from django.conf import settings
import os
import logging
from django.utils import timezone
from ..interfaces.pdf_interface import PDFServiceInterface
from ..repositories.pdf_repository import PDFRepository
from ..exceptions.pdf_exceptions import (
    PDFValidationError,
    PDFNotFoundError,
    PDFEmptyContentError,
    PDFServiceError,
    PDFRepositoryError
)

logger = logging.getLogger(__name__)


class PDFService(PDFServiceInterface):
    """Service pour la generation de PDF"""
    
    def __init__(self):
        self.repository = PDFRepository()
    
    def _should_show_dlc(self, counting, counting_details=None):
        """
        Determine si la colonne DLC doit etre affichee
        
        Logique STRICTE:
        - La colonne DLC s'affiche seulement si counting.dlc == True
        - ET si au moins un produit dans counting_details ou products a DLC activé (product.dlc == True)
        - Certains modes de comptage ne supportent pas DLC (ex: 'image de stock')
        
        Args:
            counting: L'objet Counting
            counting_details: Liste optionnelle de CountingDetail ou Product pour verification supplementaire
            
        Returns:
            bool: True si la colonne DLC doit etre affichee, False sinon
        """
        # Verifier que counting.dlc existe et est True
        if not hasattr(counting, 'dlc'):
            return False
        if not counting.dlc:
            return False
        
        # Ne pas afficher DLC pour certains modes de comptage
        count_mode_lower = counting.count_mode.lower()
        if 'image' in count_mode_lower:
            return False
        if 'vrac' in count_mode_lower and 'article' not in count_mode_lower:
            # Mode vrac pur ne supporte pas DLC
            return False
        
        # LOGIQUE STRICTE: Si counting_details est fourni, verifier si au moins un produit supporte DLC
        # Si aucun produit n'a DLC activé, ne pas afficher la colonne même si counting.dlc est True
        if counting_details:
            has_product_with_dlc = False
            for item in counting_details:
                # Accepter soit CountingDetail (avec .product) soit Product directement
                if hasattr(item, 'product'):
                    # C'est un CountingDetail
                    product = item.product
                else:
                    # C'est un Product directement
                    product = item
                
                if product and hasattr(product, 'dlc') and product.dlc:
                    has_product_with_dlc = True
                    break
            # Si aucun produit ne supporte DLC, ne pas afficher la colonne
            if not has_product_with_dlc:
                return False
        
        return True
    
    def generate_inventory_jobs_pdf(
        self, 
        inventory_id: int, 
        counting_id: Optional[int] = None,
        job_ids: Optional[List[int]] = None
    ) -> BytesIO:
        """
        Genere un PDF des jobs d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel) - non utilise, on genere pour tous
            job_ids: Liste optionnelle des IDs de jobs à exporter (si None, exporte tous les jobs avec assignments PRET ou TRANSFERT)
            
        Returns:
            BytesIO: Le contenu du PDF en memoire
        """
        try:
            # Recuperer l'inventaire
            inventory = self.repository.get_inventory_by_id(inventory_id)
            if not inventory:
                raise PDFNotFoundError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            
            # Recuperer tous les comptages de l'inventaire
            all_countings = self.repository.get_countings_by_inventory(inventory)
            
            if not all_countings:
                raise PDFNotFoundError(f"Aucun comptage trouvé pour l'inventaire {inventory_id}")
            
            # Utiliser tous les comptages (pas de restriction d'ordre)
            target_countings = all_countings
        except PDFRepositoryError:
            # Re-propaguer les erreurs du repository
            raise
        except PDFNotFoundError:
            # Re-propaguer les erreurs de ressources non trouvées
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de base: {str(e)}", exc_info=True)
            raise PDFServiceError(f"Erreur lors de la récupération des données: {str(e)}")
        
        # Trier par ordre
        target_countings.sort(key=lambda x: x.order)
        
        # Utiliser tous les comptages triés par ordre
        countings = target_countings
        
        if not countings:
            raise PDFNotFoundError(f"Aucun comptage trouvé pour l'inventaire {inventory_id}")
        
        try:
            # Recuperer les infos de l'inventaire (warehouse, account)
            warehouse_info = self._get_warehouse_info(inventory)
            account_info = self._get_account_info(inventory)
            
            # Nouvelle logique : récupérer tous les assignments de l'inventaire avec counting.order et session
            # Si job_ids est fourni, filtrer uniquement les assignments de ces jobs
            all_assignments = self.repository.get_assignments_by_inventory(inventory, job_ids=job_ids)
        except PDFRepositoryError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des assignments: {str(e)}", exc_info=True)
            raise PDFServiceError(f"Erreur lors de la récupération des assignments: {str(e)}")
        
        # Filtrer les assignments selon les comptages valides
        valid_counting_ids = [c.id for c in countings]
        assignments = [a for a in all_assignments if a.counting_id in valid_counting_ids]
        
        # Grouper les assignments par job
        assignments_by_job = {}
        for assignment in assignments:
            job = assignment.job
            if job not in assignments_by_job:
                assignments_by_job[job] = []
            assignments_by_job[job].append(assignment)
        
        # Calculer la pagination avant de construire le contenu
        page_info_map = {}
        page_counter = 0
        
        for job, job_assignments in assignments_by_job.items():
            # Récupérer les emplacements via JobDetail
            all_job_details = self.repository.get_job_details_by_job(job)
            
            # Pour chaque assignment du job, traiter avec son counting
            for assignment in job_assignments:
                counting = assignment.counting
                session = assignment.session
                user = session.username if session else None
                
                # Filtrer les job_details pour ce counting
                job_details = [jd for jd in all_job_details if jd.counting_id is None or jd.counting_id == counting.id]
                
                if job_details:
                    all_table_rows = self._prepare_inventory_jobs_table_rows(job_details, counting, job)
                    if all_table_rows:
                        lines_per_page = 40  # Meme design que job-assignment-pdf
                        total_pages = 1  # Une seule page par job (meme design)
                        page_counter += 1
                        page_info_map[page_counter] = {
                            'current': 1,
                            'total': 1,
                            'job_ref': job.reference
                        }
        
        # Creer le buffer PDF
        buffer = BytesIO()
        
        # Construire le contenu
        story = []
        
        # Log pour diagnostiquer
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Génération PDF pour inventaire {inventory_id}: {len(assignments)} assignments trouvés")
        logger.info(f"Jobs distincts: {len(assignments_by_job)}")
        
        # Pour chaque job et ses assignments
        for job, job_assignments in assignments_by_job.items():
            # Récupérer les emplacements via JobDetail
            all_job_details = self.repository.get_job_details_by_job(job)
            
            # Pour chaque assignment du job
            for assignment in job_assignments:
                counting = assignment.counting
                session = assignment.session
                user = session.username if session else None
                
                logger.info(f"Traitement Job {job.reference}, Counting ordre {counting.order}, Session: {user}")
                
                # Filtrer les job_details pour ce counting
                job_details = [jd for jd in all_job_details if jd.counting_id is None or jd.counting_id == counting.id]
                
                if job_details:
                    # Construire les pages pour ce job avec la logique spécifique à l'inventaire
                    job_pages = self._build_inventory_jobs_pages(
                        job, counting, user, inventory, warehouse_info, account_info
                    )
                    if job_pages:
                        story.extend(job_pages)
                        logger.info(f"Job {job.reference} (ordre {counting.order}): {len(job_pages)} éléments ajoutés au PDF")
                    else:
                        logger.warning(f"Job {job.reference} (ordre {counting.order}): aucun élément généré (pas de job_details ou données vides)")
                else:
                    logger.warning(f"Job {job.reference} (ordre {counting.order}): aucun job_detail trouvé")
        
        logger.info(f"Total éléments dans le PDF: {len(story)}")
        
        # Vérifier qu'il y a du contenu à générer
        if not story:
            raise PDFEmptyContentError(
                f"Aucun contenu à générer pour l'inventaire {inventory_id}. "
                f"Vérifiez qu'il y a des jobs avec statut PRET ou TRANSFERT "
                f"et des job_details associés pour les comptages."
            )
        
        try:
            # Creer le document PDF avec marges ajustees (meme design que job-assignment-pdf)
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.1*cm,
                leftMargin=0.1*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm  # Espace pour les signatures
            )
            
            # Stocker les infos de pagination dans le document
            doc.page_info_map = page_info_map
            
            # Stocker les informations de l'inventaire pour le footer (meme design que job-assignment-pdf)
            doc.inventory_info = {
                'reference': inventory.reference,
                'account_name': account_info['name'],
                'warehouse_name': warehouse_info['name'],
                'inventory_type': inventory.inventory_type,
                'date': inventory.date.strftime('%d/%m/%Y') if inventory.date else '-',
                'date_debut': None,  # Pas de date de début pour l'inventaire global
                'date_fin': None,  # Pas de date de fin pour l'inventaire global
                'job_reference': '-'  # Sera remplacé par page_info_map pour chaque page
            }
            
            # Pas de personnes pour l'inventaire global (signatures vides)
            doc.personne_info = {
                'personne': None,
                'personne_nom': None,
                'personne_two': None,
                'personne_two_nom': None
            }
            
            # Construire le PDF avec header (texte centré) et footer (pagination + signatures) personnalises pour inventory-jobs-pdf
            doc.build(story, 
                     onFirstPage=self._add_page_header_and_footer_inventory_jobs_pdf, 
                     onLaterPages=self._add_page_header_and_footer_inventory_jobs_pdf)
            
        except (AttributeError, TypeError, ValueError, IOError) as e:
            # Erreurs courantes lors de la génération PDF avec ReportLab
            logger.error(f"Erreur lors de la génération du PDF: {str(e)}", exc_info=True)
            raise PDFServiceError(f"Erreur lors de la génération du PDF: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la construction du PDF: {str(e)}", exc_info=True)
            raise PDFServiceError(f"Erreur lors de la construction du PDF: {str(e)}")
        
        # Reinitialiser le buffer
        buffer.seek(0)
        
        # Vérifier que le buffer contient des données
        buffer_content = buffer.getvalue()
        if len(buffer_content) == 0:
            raise PDFEmptyContentError("Le PDF généré est vide")
        
        return buffer
    
    def _get_warehouse_info(self, inventory):
        """Récupère les informations du warehouse via les jobs ou settings"""
        from ..models import Job
        # Essayer via les jobs
        jobs = Job.objects.filter(inventory=inventory).select_related('warehouse').first()
        if jobs and jobs.warehouse:
            return {
                'name': jobs.warehouse.warehouse_name,
                'reference': jobs.warehouse.warehouse_reference if hasattr(jobs.warehouse, 'warehouse_reference') else None
            }
        # Sinon via settings
        settings = inventory.awi_links.select_related('warehouse').first()
        if settings and settings.warehouse:
            return {
                'name': settings.warehouse.warehouse_name,
                'reference': settings.warehouse.warehouse_reference if hasattr(settings.warehouse, 'warehouse_reference') else None
            }
        return {'name': '-', 'reference': None}
    
    def _get_account_info(self, inventory):
        """Récupère les informations du compte via settings"""
        settings = inventory.awi_links.select_related('account').first()
        if settings and settings.account:
            return {
                'name': settings.account.account_name,
                'reference': settings.account.account_reference if hasattr(settings.account, 'account_reference') else None
            }
        return {'name': '-', 'reference': None}
    
    def _get_logo_path(self):
        """Récupère le chemin du logo"""
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo_app.png')
        if os.path.exists(logo_path):
            return logo_path
        # Fallback vers staticfiles
        logo_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'logo_app.png')
        if os.path.exists(logo_path):
            return logo_path
        return None
    
    def _add_page_header_and_footer(self, canvas_obj, doc):
        """Ajoute le logo en haut à gauche et la pagination en bas à droite"""
        # Ajouter le logo en haut à gauche (position absolue - maximum gauche et haut)
        logo_path = self._get_logo_path()
        if logo_path:
            try:
                canvas_obj.saveState()
                # Dimensions du logo agrandies
                logo_width = 4*cm  # Agrandi de 3cm à 5cm
                logo_height = 2*cm  # Agrandi de 1.5cm à 2.5cm
                
                # Position: maximum à gauche et en haut (0.2cm de marge minimale + 1.5cm vers le bas)
                x = 0.02*cm  # Presque au bord gauche
                y = doc.pagesize[1] - 0.2*cm - logo_height - 1.5*cm  # Déplacé de 1.5 cm vers le bas
                
                canvas_obj.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                canvas_obj.restoreState()
            except Exception as e:
                # Si erreur de chargement du logo, continuer sans logo
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible de charger le logo: {str(e)}")
        
        # Ajouter la pagination en bas à droite
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            # Positionner en bas à droite (0 du bas, aligné à droite)
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            # Position: largeur page - marge droite - largeur texte, y=0.5cm du bas
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            x = doc.pagesize[0] - doc.rightMargin - text_width
            y = 0.5*cm  # 0.5cm du bas absolu
            
            canvas_obj.drawString(x, y, text)
            canvas_obj.restoreState()
    
    def _add_page_header_and_footer_inventory_jobs_pdf(self, canvas_obj, doc):
        """
        Ajoute le header et footer pour l'API inventory/<int:inventory_id>/jobs/pdf/
        Texte "FICHE DE COMPTAGE" centré en haut
        """
        canvas_obj.saveState()
        
        # Ajouter le titre "FICHE DE COMPTAGE : {job_reference}" centré en haut
        inventory_info = getattr(doc, 'inventory_info', {})
        # Utiliser page_info_map pour obtenir le job_reference de la page actuelle
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        job_reference = page_info.get('job_ref', inventory_info.get('job_reference', '-'))
        
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.setFillColor(colors.black)
        
        # Titre "FICHE DE COMPTAGE : {job_reference}" centré horizontalement
        title_text = f"FICHE DE COMPTAGE : {job_reference}"
        title_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 12)
        # Centrer le titre horizontalement
        x_title = (doc.pagesize[0] - title_width) / 2
        # Positionner avec un espace en haut (plus bas que la marge supérieure)
        y_header = doc.pagesize[1] - doc.topMargin - 0.5*cm
        canvas_obj.drawString(x_title, y_header, title_text)
        
        # Ajouter les informations dans le footer (référence inventaire, compte, type magasin, date)
        # Positionnées en bas à gauche
        if inventory_info:
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            # Positionner les infos centrées en bas (1.5cm du bas pour laisser place aux signatures)
            footer_y = 0.5*cm
            
            # Construire le texte du footer (sans dates pour inventory-jobs-pdf)
            reference = inventory_info.get('reference', '-')
            account = inventory_info.get('account_name', '-')
            warehouse = inventory_info.get('warehouse_name', '-')
            
            # Construire le footer
            footer_parts = [f"Réf. Inventaire: {reference}", f"Compte: {account}", f"Magasin: {warehouse}"]
            footer_text = "-".join(footer_parts)
            
            # Centrer le footer horizontalement
            footer_width = canvas_obj.stringWidth(footer_text, "Helvetica", 8)
            footer_x = (doc.pagesize[0] - footer_width) / 2
            canvas_obj.drawString(footer_x, footer_y, footer_text)
            
            # Afficher les labels de dates séparés
            # Positionner les labels entre le footer et les signatures (2.8cm du bas)
            date_line_y = 2.8*cm
            signature_margin = 0.5*cm
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.setFillColor(colors.black)
            
            # Label Date début (à gauche, aligné avec Signature L'Oréal)
            date_debut_x = doc.leftMargin + signature_margin
            canvas_obj.drawString(date_debut_x, date_line_y, "Date début:")
            
            # Label Date fin (à droite, aligné avec Signature AGL)
            label_text_fin = "Date fin :"
            label_fin_width = canvas_obj.stringWidth(label_text_fin, "Helvetica", 10)
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle
            # Calculer la position de la même manière que la signature AGL
            date_fin_label_x = doc.pagesize[0] - doc.rightMargin - label_fin_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(date_fin_label_x, date_line_y, label_text_fin)
        
        # Ajouter la pagination à droite (même hauteur que le footer)
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            # Positionner la pagination à droite
            footer_margin = 0.5*cm
            x = doc.pagesize[0] - doc.rightMargin - text_width - footer_margin
            y = 0.5*cm  # Même hauteur que le footer
            canvas_obj.drawString(x, y, text)
        
        # Ajouter les signatures en bas de page
        personne_info = getattr(doc, 'personne_info', {})
        personne = personne_info.get('personne')
        personne_two = personne_info.get('personne_two')
        
        # Debug: logger les valeurs récupérées
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== RÉCUPÉRATION PERSONNE_INFO (inventory-jobs-pdf) ===")
        logger.info(f"personne_info complet: {personne_info}")
        logger.info(f"personne='{personne}' (type: {type(personne)}, bool: {bool(personne)})")
        logger.info(f"personne_two='{personne_two}' (type: {type(personne_two)}, bool: {bool(personne_two)})")
        
        # Toujours afficher les signatures (même si vides)
        # Vérifier si on a des personnes (même si ce sont des chaînes vides, on les considère comme valides)
        has_personne = personne and str(personne).strip()
        has_personne_two = personne_two and str(personne_two).strip()
        
        # Toujours afficher les signatures (avec valeurs vides si nécessaire)
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.black)
        
        # Hauteur pour le texte des labels (2.3cm du bas)
        text_y = 2*cm
            
        # Fonction pour vérifier si le nom commence par AGL ou L'Oréal
        def starts_with_agl(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            return name_lower.startswith('agl')
        
        def starts_with_loreal(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            return (name_lower.startswith('l\'oreal') or 
                    name_lower.startswith('l\'oréal') or
                    name_lower.startswith("l'oréal") or
                    name_lower.startswith("l'oreal") or
                    name_lower.startswith('loreal') or 
                    name_lower.startswith('loréal') or
                    name_lower.startswith('oreal') or
                    (len(name_lower) >= 7 and ('l\'oréal' in name_lower[:8] or 'l\'oreal' in name_lower[:8] or "l'oréal" in name_lower[:8] or "l'oreal" in name_lower[:8])))
        
        # Récupérer les noms complets et les noms seuls
        personne_nom = personne_info.get('personne_nom')
        personne_two_nom = personne_info.get('personne_two_nom')
        
        # Déterminer quelle personne va où selon leur nom
        personne_loreal = None
        personne_agl = None
        
        # Vérifier d'abord le nom seul, puis la chaîne complète "nom prenom"
        if has_personne:
            personne_str = str(personne).strip() if personne else ''
            personne_nom_str = str(personne_nom).strip() if personne_nom else ''
            
            if starts_with_loreal(personne_nom_str) or starts_with_loreal(personne_str):
                personne_loreal = personne
            elif starts_with_agl(personne_nom_str) or starts_with_agl(personne_str):
                personne_agl = personne
        
        if has_personne_two:
            personne_two_str = str(personne_two).strip() if personne_two else ''
            personne_two_nom_str = str(personne_two_nom).strip() if personne_two_nom else ''
            
            if starts_with_loreal(personne_two_nom_str) or starts_with_loreal(personne_two_str):
                personne_loreal = personne_two
            elif starts_with_agl(personne_two_nom_str) or starts_with_agl(personne_two_str):
                personne_agl = personne_two
        
        # Toujours afficher les signatures si on a au moins une personne
        if personne_loreal and personne_agl:
            # Signature L'Oréal à gauche avec le nom de la personne
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            if personne_nom_text.startswith("LOREAL ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x1, text_y, label_text)
            
            # Signature AGL à droite avec le nom de la personne
            canvas_obj.setFont("Helvetica", 10)
            personne_agl_nom_text = str(personne_agl).strip() if personne_agl else ''
            if personne_agl_nom_text.startswith("AGL "):
                personne_agl_nom_text = personne_agl_nom_text.split(" ", 1)[1] if " " in personne_agl_nom_text else personne_agl_nom_text
            elif personne_agl_nom_text.startswith("AGL-"):
                personne_agl_nom_text = personne_agl_nom_text.split("-", 1)[1] if "-" in personne_agl_nom_text else personne_agl_nom_text
            label_text_agl = f"Signature AGL : {personne_agl_nom_text}"
            full_text_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm
            x2 = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
        elif personne_loreal:
            # Une seule personne L'Oréal, à gauche avec le nom
            signature_margin = 0.5*cm
            x = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            if personne_nom_text.startswith("L'Oréal ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x, text_y, label_text)
        elif personne_agl:
            # Une seule personne AGL, à droite avec le nom
            canvas_obj.setFont("Helvetica", 10)
            personne_nom_text = str(personne_agl).strip() if personne_agl else ''
            if personne_nom_text.startswith("AGL "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("AGL-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            label_text = f"Signature AGL : {personne_nom_text}"
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm
            full_text_width = canvas_obj.stringWidth(label_text, "Helvetica", 10)
            x = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x, text_y, label_text)
        else:
            # Toujours afficher les signatures (même vides)
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            label_text = "Signature L'Oréal :"
            canvas_obj.drawString(x1, text_y, label_text)
            
            # Signature AGL à droite (vide)
            canvas_obj.setFont("Helvetica", 10)
            label_text_agl = "Signature AGL :"
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm
            label_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            x2 = doc.pagesize[0] - doc.rightMargin - label_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
        
        canvas_obj.restoreState()
    
    def _add_page_header_and_footer_job_assignment_pdf(self, canvas_obj, doc):
        """
        Ajoute le header et footer pour l'API jobs/<int:job_id>/assignments/<int:assignment_id>/pdf/
        Texte "FICHE DE COMPTAGE" centré en haut
        """
        canvas_obj.saveState()
        
        # Ajouter le titre "FICHE DE COMPTAGE : {job_reference}" centré en haut
        inventory_info = getattr(doc, 'inventory_info', {})
        # Utiliser page_info_map pour obtenir le job_reference de la page actuelle
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        job_reference = page_info.get('job_ref', inventory_info.get('job_reference', '-'))
        
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.setFillColor(colors.black)
        
        # Titre "FICHE DE COMPTAGE : {job_reference}" centré horizontalement
        title_text = f"FICHE DE COMPTAGE : {job_reference}"
        title_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 12)
        # Centrer le titre horizontalement
        x_title = (doc.pagesize[0] - title_width) / 2
        # Positionner avec un espace en haut (plus bas que la marge supérieure)
        y_header = doc.pagesize[1] - doc.topMargin - 0.5*cm
        canvas_obj.drawString(x_title, y_header, title_text)
        
        # Ajouter les informations dans le footer (référence inventaire, compte, type magasin, date)
        # Positionnées en bas à gauche
        if inventory_info:
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            # Positionner les infos centrées en bas (1.5cm du bas pour laisser place aux signatures)
            footer_y = 1*cm
            
            # Construire le texte du footer (avec date début et date fin pour job-assignment-pdf)
            reference = inventory_info.get('reference', '-')
            account = inventory_info.get('account_name', '-')
            warehouse = inventory_info.get('warehouse_name', '-')
            inv_type = inventory_info.get('inventory_type', '-')
            # Récupérer les dates
            date_debut = inventory_info.get('date_debut')
            date_fin = inventory_info.get('date_fin')
            
            # Construire le footer
            footer_parts = [f"Réf. Inventaire: {reference}", f"Compte: {account}", f"Magasin: {warehouse}"]
            
            # Ajouter les dates seulement si elles ont des valeurs réelles (pas None et pas '-')
            if date_debut and date_debut != '-' and date_debut is not None:
                footer_parts.append(f"Date début: {date_debut}")
            if date_fin and date_fin != '-' and date_fin is not None:
                footer_parts.append(f"Date fin: {date_fin}")
            
            footer_text = "-".join(footer_parts)
            
            # Centrer le footer horizontalement
            footer_width = canvas_obj.stringWidth(footer_text, "Helvetica", 8)
            footer_x = (doc.pagesize[0] - footer_width) / 2
            canvas_obj.drawString(footer_x, footer_y, footer_text)
        
        # Ajouter la pagination à droite (même hauteur que le footer)
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            # Positionner la pagination à droite
            footer_margin = 0.5*cm
            x = doc.pagesize[0] - doc.rightMargin - text_width - footer_margin
            y = 0.5*cm  # Même hauteur que le footer
            canvas_obj.drawString(x, y, text)
        
        # Ajouter les signatures en bas de page
        personne_info = getattr(doc, 'personne_info', {})
        personne = personne_info.get('personne')
        personne_two = personne_info.get('personne_two')
        
        # Debug: logger les valeurs récupérées
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== RÉCUPÉRATION PERSONNE_INFO (job-assignment-pdf) ===")
        logger.info(f"personne_info complet: {personne_info}")
        logger.info(f"personne='{personne}' (type: {type(personne)}, bool: {bool(personne)})")
        logger.info(f"personne_two='{personne_two}' (type: {type(personne_two)}, bool: {bool(personne_two)})")
        
        # Toujours afficher les signatures (même si vides)
        # Vérifier si on a des personnes (même si ce sont des chaînes vides, on les considère comme valides)
        has_personne = personne and str(personne).strip()
        has_personne_two = personne_two and str(personne_two).strip()
        logger.info(f"has_personne: {has_personne}, has_personne_two: {has_personne_two}")
        
        # Toujours afficher les signatures (avec valeurs vides si nécessaire)
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.black)
        
        # Hauteur pour le texte des labels (2.3cm du bas)
        text_y = 2*cm
            
        # Fonction pour vérifier si le nom commence par AGL ou L'Oréal
        def starts_with_agl(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            # Vérifier si ça commence par "agl" (ex: "AGL BELAZZAB")
            return name_lower.startswith('agl')
        
        def starts_with_loreal(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            # Vérifier différentes variations de L'Oréal (ex: "L'Oréal BOUFENZI")
            # Vérifier avec apostrophe droite (') et apostrophe typographique (')
            # Vérifier aussi sans apostrophe
            return (name_lower.startswith('l\'oreal') or 
                    name_lower.startswith('l\'oréal') or
                    name_lower.startswith("l'oréal") or
                    name_lower.startswith("l'oreal") or
                    name_lower.startswith('loreal') or 
                    name_lower.startswith('loréal') or
                    name_lower.startswith('oreal') or
                    # Vérifier si "l'oréal" ou "l'oreal" apparaît dans les premiers caractères
                    (len(name_lower) >= 7 and ('l\'oréal' in name_lower[:8] or 'l\'oreal' in name_lower[:8] or "l'oréal" in name_lower[:8] or "l'oreal" in name_lower[:8])))
        
        # Récupérer les noms complets et les noms seuls
        personne_nom = personne_info.get('personne_nom')
        personne_two_nom = personne_info.get('personne_two_nom')
        
        # Debug: logger les valeurs pour comprendre
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== DEBUG SIGNATURES ===")
        logger.info(f"Personne 1 complète: '{personne}', Nom seul: '{personne_nom}'")
        logger.info(f"Personne 2 complète: '{personne_two}', Nom seul: '{personne_two_nom}'")
        logger.info(f"Type personne: {type(personne)}, Type personne_two: {type(personne_two)}")
        
        # Déterminer quelle personne va où selon leur nom
        personne_loreal = None
        personne_agl = None
        
        # Vérifier d'abord le nom seul, puis la chaîne complète "nom prenom"
        if has_personne:
            personne_str = str(personne).strip() if personne else ''
            personne_nom_str = str(personne_nom).strip() if personne_nom else ''
            
            logger.info(f"Vérification Personne 1 - Nom complet: '{personne_str}', Nom seul: '{personne_nom_str}'")
            logger.info(f"  starts_with_loreal(nom_seul): {starts_with_loreal(personne_nom_str)}")
            logger.info(f"  starts_with_loreal(complet): {starts_with_loreal(personne_str)}")
            logger.info(f"  starts_with_agl(nom_seul): {starts_with_agl(personne_nom_str)}")
            logger.info(f"  starts_with_agl(complet): {starts_with_agl(personne_str)}")
            
            # Vérifier d'abord le nom seul, puis la chaîne complète
            if starts_with_loreal(personne_nom_str) or starts_with_loreal(personne_str):
                personne_loreal = personne
                logger.info(f"[OK] Personne 1 assignee a L'Oreal: {personne}")
            elif starts_with_agl(personne_nom_str) or starts_with_agl(personne_str):
                personne_agl = personne
                logger.info(f"[OK] Personne 1 assignee a AGL: {personne}")
            else:
                logger.warning(f"[KO] Personne 1 ne correspond a aucun critere")
        
        if has_personne_two:
            personne_two_str = str(personne_two).strip() if personne_two else ''
            personne_two_nom_str = str(personne_two_nom).strip() if personne_two_nom else ''
            
            logger.info(f"Vérification Personne 2 - Nom complet: '{personne_two_str}', Nom seul: '{personne_two_nom_str}'")
            logger.info(f"  starts_with_loreal(nom_seul): {starts_with_loreal(personne_two_nom_str)}")
            logger.info(f"  starts_with_loreal(complet): {starts_with_loreal(personne_two_str)}")
            logger.info(f"  starts_with_agl(nom_seul): {starts_with_agl(personne_two_nom_str)}")
            logger.info(f"  starts_with_agl(complet): {starts_with_agl(personne_two_str)}")
            
            # Vérifier d'abord le nom seul, puis la chaîne complète
            if starts_with_loreal(personne_two_nom_str) or starts_with_loreal(personne_two_str):
                personne_loreal = personne_two
                logger.info(f"[OK] Personne 2 assignee a L'Oreal: {personne_two}")
            elif starts_with_agl(personne_two_nom_str) or starts_with_agl(personne_two_str):
                personne_agl = personne_two
                logger.info(f"[OK] Personne 2 assignee a AGL: {personne_two}")
            else:
                logger.warning(f"[KO] Personne 2 ne correspond a aucun critere")
        
        logger.info(f"Resultat final - personne_loreal: {personne_loreal}, personne_agl: {personne_agl}")
        
        # Toujours afficher les signatures si on a au moins une personne
        # Si deux personnes, les placer côte à côte
        if personne_loreal and personne_agl:
            logger.info(f"[AFFICHAGE] Deux signatures: L'Oreal a gauche, AGL a droite")
            # Signature L'Oréal à gauche avec le nom de la personne
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            # Extraire juste le nom (sans le préfixe L'Oréal si présent - avec espace ou tiret)
            if personne_nom_text.startswith("L'Oréal ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x1, text_y, label_text)
            logger.info(f"[AFFICHAGE] Signature L'Oreal a x={x1}, y={text_y}, texte: {label_text}")
            
            # Signature AGL à droite avec le nom de la personne
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_agl_nom_text = str(personne_agl).strip() if personne_agl else ''
            # Extraire juste le nom (sans le préfixe AGL si présent - avec espace ou tiret)
            if personne_agl_nom_text.startswith("AGL "):
                personne_agl_nom_text = personne_agl_nom_text.split(" ", 1)[1] if " " in personne_agl_nom_text else personne_agl_nom_text
            elif personne_agl_nom_text.startswith("AGL-"):
                personne_agl_nom_text = personne_agl_nom_text.split("-", 1)[1] if "-" in personne_agl_nom_text else personne_agl_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text_agl = f"Signature AGL : {personne_agl_nom_text}"
            # Calculer la position avec espace pour la saisie manuelle (déplacer vers la gauche)
            full_text_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            x2 = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
            logger.info(f"[AFFICHAGE] Signature AGL a x={x2}, y={text_y}, texte: {label_text_agl}")
        elif personne_loreal:
            # Une seule personne L'Oréal, à gauche avec le nom
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            # Extraire juste le nom (sans le préfixe L'Oréal si présent - avec espace ou tiret)
            if personne_nom_text.startswith("L'Oréal ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x, text_y, label_text)
        elif personne_agl:
            # Une seule personne AGL, à droite avec le nom
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_agl).strip() if personne_agl else ''
            # Extraire juste le nom (sans le préfixe AGL si présent - avec espace ou tiret)
            if personne_nom_text.startswith("AGL "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("AGL-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature AGL : {personne_nom_text}"
            # Calculer la position en fonction de la largeur du texte et de la marge droite
            # Ajouter une marge latérale pour les signatures et espace pour la saisie manuelle
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            full_text_width = canvas_obj.stringWidth(label_text, "Helvetica", 10)
            x = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x, text_y, label_text)
        else:
            # Toujours afficher les signatures (même vides)
            # Si aucune personne ne correspond aux critères ou si personne_info est vide, afficher des signatures vides
            logger.info("Affichage des signatures vides")
            # Signature L'Oréal à gauche (vide)
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            label_text = "Signature L'Oréal :"
            canvas_obj.drawString(x1, text_y, label_text)
            
            # Signature AGL à droite (vide)
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            label_text_agl = "Signature AGL :"
            # Calculer la position en fonction de la largeur du texte et de la marge droite
            # Ajouter une marge latérale pour les signatures et espace pour la saisie manuelle
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            label_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            x2 = doc.pagesize[0] - doc.rightMargin - label_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
        
        canvas_obj.restoreState()
    
    def _add_page_header_and_footer_with_signatures(self, canvas_obj, doc):
        """Ajoute le texte Inventaire en haut, la pagination, les infos dans le footer et les signatures"""
        canvas_obj.saveState()
        
        # Ajouter le titre "FICHE DE COMPTAGE - job-1" centré en haut
        inventory_info = getattr(doc, 'inventory_info', {})
        # Utiliser page_info_map pour obtenir le job_reference de la page actuelle
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        job_reference = page_info.get('job_ref', inventory_info.get('job_reference', '-'))
        
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.setFillColor(colors.black)
        
        # Titre "FICHE DE COMPTAGE - job-1" centré
        title_text = f"FICHE DE COMPTAGE : {job_reference}"
        title_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 12)
        # Centrer le titre horizontalement
        x_title = (doc.pagesize[0] - title_width) / 2
        # Positionner avec un espace en haut (plus bas que la marge supérieure)
        y_header = doc.pagesize[1] - doc.topMargin - 0.5*cm
        canvas_obj.drawString(x_title, y_header, title_text)
        
        # Ajouter les informations dans le footer (référence inventaire, compte, type magasin, date)
        # Positionnées en bas à gauche
        if inventory_info:
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            # Positionner les infos en bas à gauche (1.5cm du bas pour laisser place aux signatures)
            # Ajouter une marge latérale pour le footer
            footer_margin = 0.5*cm
            footer_y = 1*cm
            footer_x = doc.leftMargin + footer_margin
            
            # Construire le texte du footer (avec date début et date fin si disponibles)
            reference = inventory_info.get('reference', '-')
            account = inventory_info.get('account_name', '-')
            warehouse = inventory_info.get('warehouse_name', '-')
            inv_type = inventory_info.get('inventory_type', '-')
            # Récupérer les dates
            date_debut = inventory_info.get('date_debut')
            date_fin = inventory_info.get('date_fin')
            
            # Vérifier si c'est l'API inventory-jobs-pdf (dates None ou '-')
            is_inventory_jobs_pdf = (date_debut is None or date_debut == '-') and (date_fin is None or date_fin == '-')
            
            # Construire le footer
            footer_parts = [f"Réf. Inventaire: {reference}", f"Compte: {account}", f"Magasin: {warehouse}"]
            
            # Pour l'API job-assignment-pdf, ajouter les dates dans le footer
            # Pour l'API inventory-jobs-pdf, les dates seront affichées séparément
            if not is_inventory_jobs_pdf:
                # Ajouter les dates seulement si elles ont des valeurs réelles (pas None et pas '-')
                if date_debut and date_debut != '-' and date_debut is not None:
                    footer_parts.append(f"Date début: {date_debut}")
                if date_fin and date_fin != '-' and date_fin is not None:
                    footer_parts.append(f"Date fin: {date_fin}")
            
            footer_text = "-".join(footer_parts)
            canvas_obj.drawString(footer_x, footer_y, footer_text)
            
            # Pour l'API inventory-jobs-pdf, afficher les labels de dates séparés
            if is_inventory_jobs_pdf:
                # Positionner les labels entre le footer et les signatures (2.8cm du bas)
                date_line_y = 2.8*cm
                signature_margin = 0.5*cm
                canvas_obj.setFont("Helvetica", 10)
                canvas_obj.setFillColor(colors.black)
                
                # Label Date début (à gauche, aligné avec Signature L'Oréal)
                date_debut_x = doc.leftMargin + signature_margin
                canvas_obj.drawString(date_debut_x, date_line_y, "Date début:")
                
                # Label Date fin (à droite, aligné avec Signature AGL)
                label_text_fin = "Date fin :"
                label_fin_width = canvas_obj.stringWidth(label_text_fin, "Helvetica", 10)
                space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle
                # Calculer la position de la même manière que la signature AGL
                date_fin_label_x = doc.pagesize[0] - doc.rightMargin - label_fin_width - signature_margin - space_for_manual_entry
                canvas_obj.drawString(date_fin_label_x, date_line_y, label_text_fin)
        
        # Ajouter la pagination en bas à droite (même hauteur que le footer)
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            # Ajouter une marge latérale pour la pagination
            footer_margin = 0.5*cm
            x = doc.pagesize[0] - doc.rightMargin - text_width - footer_margin
            y = 1.5*cm  # Même hauteur que le footer
            canvas_obj.drawString(x, y, text)
        
        # Ajouter les signatures en bas de page
        personne_info = getattr(doc, 'personne_info', {})
        personne = personne_info.get('personne')
        personne_two = personne_info.get('personne_two')
        
        # Debug: logger les valeurs récupérées
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== RÉCUPÉRATION PERSONNE_INFO ===")
        logger.info(f"personne_info complet: {personne_info}")
        logger.info(f"personne='{personne}' (type: {type(personne)}, bool: {bool(personne)})")
        logger.info(f"personne_two='{personne_two}' (type: {type(personne_two)}, bool: {bool(personne_two)})")
        logger.info(f"Toutes les clés personne_info: {list(personne_info.keys())}")
        
        # Toujours afficher les signatures (même si vides)
        # Vérifier si on a des personnes (même si ce sont des chaînes vides, on les considère comme valides)
        has_personne = personne and str(personne).strip()
        has_personne_two = personne_two and str(personne_two).strip()
        logger.info(f"has_personne: {has_personne}, has_personne_two: {has_personne_two}")
        
        # Toujours afficher les signatures (avec valeurs vides si nécessaire)
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.black)
        
        # Hauteur pour le texte des labels (2.3cm du bas)
        text_y = 2*cm
            
        # Fonction pour vérifier si le nom commence par AGL ou L'Oréal
        def starts_with_agl(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            # Vérifier si ça commence par "agl" (ex: "AGL BELAZZAB")
            return name_lower.startswith('agl')
        
        def starts_with_loreal(name):
            if not name:
                return False
            name_lower = name.lower().strip()
            # Vérifier différentes variations de L'Oréal (ex: "L'Oréal BOUFENZI")
            # Vérifier avec apostrophe droite (') et apostrophe typographique (')
            # Vérifier aussi sans apostrophe
            return (name_lower.startswith('l\'oreal') or 
                    name_lower.startswith('l\'oréal') or
                    name_lower.startswith("l'oréal") or
                    name_lower.startswith("l'oreal") or
                    name_lower.startswith('loreal') or 
                    name_lower.startswith('loréal') or
                    name_lower.startswith('oreal') or
                    # Vérifier si "l'oréal" ou "l'oreal" apparaît dans les premiers caractères
                    (len(name_lower) >= 7 and ('l\'oréal' in name_lower[:8] or 'l\'oreal' in name_lower[:8] or "l'oréal" in name_lower[:8] or "l'oreal" in name_lower[:8])))
        
        # Récupérer les noms complets et les noms seuls
        personne_nom = personne_info.get('personne_nom')
        personne_two_nom = personne_info.get('personne_two_nom')
        
        # Debug: logger les valeurs pour comprendre
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== DEBUG SIGNATURES ===")
        logger.info(f"Personne 1 complète: '{personne}', Nom seul: '{personne_nom}'")
        logger.info(f"Personne 2 complète: '{personne_two}', Nom seul: '{personne_two_nom}'")
        logger.info(f"Type personne: {type(personne)}, Type personne_two: {type(personne_two)}")
        
        # Déterminer quelle personne va où selon leur nom
        personne_loreal = None
        personne_agl = None
        
        # Vérifier d'abord le nom seul, puis la chaîne complète "nom prenom"
        if has_personne:
            personne_str = str(personne).strip() if personne else ''
            personne_nom_str = str(personne_nom).strip() if personne_nom else ''
            
            logger.info(f"Vérification Personne 1 - Nom complet: '{personne_str}', Nom seul: '{personne_nom_str}'")
            logger.info(f"  starts_with_loreal(nom_seul): {starts_with_loreal(personne_nom_str)}")
            logger.info(f"  starts_with_loreal(complet): {starts_with_loreal(personne_str)}")
            logger.info(f"  starts_with_agl(nom_seul): {starts_with_agl(personne_nom_str)}")
            logger.info(f"  starts_with_agl(complet): {starts_with_agl(personne_str)}")
            
            # Vérifier d'abord le nom seul, puis la chaîne complète
            if starts_with_loreal(personne_nom_str) or starts_with_loreal(personne_str):
                personne_loreal = personne
                logger.info(f"[OK] Personne 1 assignee a L'Oreal: {personne}")
            elif starts_with_agl(personne_nom_str) or starts_with_agl(personne_str):
                personne_agl = personne
                logger.info(f"[OK] Personne 1 assignee a AGL: {personne}")
            else:
                logger.warning(f"[KO] Personne 1 ne correspond a aucun critere")
        
        if has_personne_two:
            personne_two_str = str(personne_two).strip() if personne_two else ''
            personne_two_nom_str = str(personne_two_nom).strip() if personne_two_nom else ''
            
            logger.info(f"Vérification Personne 2 - Nom complet: '{personne_two_str}', Nom seul: '{personne_two_nom_str}'")
            logger.info(f"  starts_with_loreal(nom_seul): {starts_with_loreal(personne_two_nom_str)}")
            logger.info(f"  starts_with_loreal(complet): {starts_with_loreal(personne_two_str)}")
            logger.info(f"  starts_with_agl(nom_seul): {starts_with_agl(personne_two_nom_str)}")
            logger.info(f"  starts_with_agl(complet): {starts_with_agl(personne_two_str)}")
            
            # Vérifier d'abord le nom seul, puis la chaîne complète
            if starts_with_loreal(personne_two_nom_str) or starts_with_loreal(personne_two_str):
                personne_loreal = personne_two
                logger.info(f"[OK] Personne 2 assignee a L'Oreal: {personne_two}")
            elif starts_with_agl(personne_two_nom_str) or starts_with_agl(personne_two_str):
                personne_agl = personne_two
                logger.info(f"[OK] Personne 2 assignee a AGL: {personne_two}")
            else:
                logger.warning(f"[KO] Personne 2 ne correspond a aucun critere")
        
        logger.info(f"Resultat final - personne_loreal: {personne_loreal}, personne_agl: {personne_agl}")
        
        # Toujours afficher les signatures si on a au moins une personne
        # Si deux personnes, les placer côte à côte
        if personne_loreal and personne_agl:
            logger.info(f"[AFFICHAGE] Deux signatures: L'Oreal a gauche, AGL a droite")
            # Signature L'Oréal à gauche avec le nom de la personne
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            # Extraire juste le nom (sans le préfixe L'Oréal si présent - avec espace ou tiret)
            if personne_nom_text.startswith("L'Oréal ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x1, text_y, label_text)
            logger.info(f"[AFFICHAGE] Signature L'Oreal a x={x1}, y={text_y}, texte: {label_text}")
            
            # Signature AGL à droite avec le nom de la personne
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_agl_nom_text = str(personne_agl).strip() if personne_agl else ''
            # Extraire juste le nom (sans le préfixe AGL si présent - avec espace ou tiret)
            if personne_agl_nom_text.startswith("AGL "):
                personne_agl_nom_text = personne_agl_nom_text.split(" ", 1)[1] if " " in personne_agl_nom_text else personne_agl_nom_text
            elif personne_agl_nom_text.startswith("AGL-"):
                personne_agl_nom_text = personne_agl_nom_text.split("-", 1)[1] if "-" in personne_agl_nom_text else personne_agl_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text_agl = f"Signature AGL : {personne_agl_nom_text}"
            # Calculer la position avec espace pour la saisie manuelle (déplacer vers la gauche)
            full_text_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            x2 = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
            logger.info(f"[AFFICHAGE] Signature AGL a x={x2}, y={text_y}, texte: {label_text_agl}")
        elif personne_loreal:
            # Une seule personne L'Oréal, à gauche avec le nom
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_loreal).strip() if personne_loreal else ''
            # Extraire juste le nom (sans le préfixe L'Oréal si présent - avec espace ou tiret)
            if personne_nom_text.startswith("L'Oréal ") or personne_nom_text.startswith("L'Oreal "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("L'Oréal-") or personne_nom_text.startswith("L'Oreal-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature L'Oréal : {personne_nom_text}"
            canvas_obj.drawString(x, text_y, label_text)
        elif personne_agl:
            # Une seule personne AGL, à droite avec le nom
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            # Extraire le nom de la personne
            personne_nom_text = str(personne_agl).strip() if personne_agl else ''
            # Extraire juste le nom (sans le préfixe AGL si présent - avec espace ou tiret)
            if personne_nom_text.startswith("AGL "):
                personne_nom_text = personne_nom_text.split(" ", 1)[1] if " " in personne_nom_text else personne_nom_text
            elif personne_nom_text.startswith("AGL-"):
                personne_nom_text = personne_nom_text.split("-", 1)[1] if "-" in personne_nom_text else personne_nom_text
            # Afficher le label avec le nom de la personne sur la même ligne
            label_text = f"Signature AGL : {personne_nom_text}"
            # Calculer la position en fonction de la largeur du texte et de la marge droite
            # Ajouter une marge latérale pour les signatures et espace pour la saisie manuelle
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            full_text_width = canvas_obj.stringWidth(label_text, "Helvetica", 10)
            x = doc.pagesize[0] - doc.rightMargin - full_text_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x, text_y, label_text)
        else:
            # Toujours afficher les signatures (même vides)
            # Si aucune personne ne correspond aux critères ou si personne_info est vide, afficher des signatures vides
            logger.info("Affichage des signatures vides")
            # Signature L'Oréal à gauche (vide)
            # Ajouter une marge latérale pour les signatures
            signature_margin = 0.5*cm
            x1 = doc.leftMargin + signature_margin
            canvas_obj.setFont("Helvetica", 10)
            label_text = "Signature L'Oréal :"
            canvas_obj.drawString(x1, text_y, label_text)
            
            # Signature AGL à droite (vide)
            # Adapter selon la configuration de la page (utiliser la largeur disponible)
            canvas_obj.setFont("Helvetica", 10)
            label_text_agl = "Signature AGL :"
            # Calculer la position en fonction de la largeur du texte et de la marge droite
            # Ajouter une marge latérale pour les signatures et espace pour la saisie manuelle
            signature_margin = 0.5*cm
            space_for_manual_entry = 4*cm  # Espace pour la saisie manuelle du nom et prénom
            label_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
            x2 = doc.pagesize[0] - doc.rightMargin - label_width - signature_margin - space_for_manual_entry
            canvas_obj.drawString(x2, text_y, label_text_agl)
        
        canvas_obj.restoreState()
    
    def _build_inventory_jobs_pages(self, job, counting, user, inventory, warehouse_info, account_info):
        """
        Construit les pages pour un job dans le contexte d'un inventaire
        Utilise le meme design que job-assignment-pdf (40 lignes, une seule page)
        Logique spécifique à l'API inventory/<int:inventory_id>/jobs/pdf/
        """
        elements = []
        
        # Récupérer tous les job details du job pour ce counting
        all_job_details = self.repository.get_job_details_by_job(job)
        job_details = []
        for jd in all_job_details:
            if jd.counting_id is None or jd.counting_id == counting.id:
                job_details.append(jd)
        
        if not job_details:
            return elements
        
        # Construire toutes les lignes du tableau d'abord
        all_table_rows = self._prepare_inventory_jobs_table_rows(job_details, counting, job)
        
        if not all_table_rows:
            return elements
        
        # Meme design que job-assignment-pdf: 40 lignes maximum, une seule page
        lines_per_page = 40
        total_pages = 1  # Un seul tableau = une seule page
        
        # Prendre seulement les 40 premières lignes (ignorer le reste)
        page_rows = all_table_rows[:lines_per_page]
        
        # Ajouter des lignes vides pour compléter jusqu'à 40 lignes
        num_data_rows = len(page_rows)
        num_empty_rows_needed = lines_per_page - num_data_rows
        
        if num_empty_rows_needed > 0:
            # Déterminer si DLC est présent dans les lignes existantes
            has_dlc = any('dlc' in row for row in page_rows)
            
            # Créer des lignes vides avec la même structure
            empty_rows = self._create_empty_rows_for_inventory_jobs(
                num_empty_rows_needed, counting, has_dlc
            )
            page_rows.extend(empty_rows)
        
        # Construire l'en-tête de la page (une seule fois) - utiliser le design de job assignment
        header_elements = self._build_job_assignment_page_header(
            inventory, job, user, counting, warehouse_info, account_info, 1, total_pages
        )
        
        # Construire un SEUL tableau avec exactement 40 lignes (ou moins) - utiliser le design de job assignment
        table_elements = self._build_job_assignment_table_from_rows(page_rows, counting, 1, total_pages)
        
        # Garder l'en-tête et le tableau ensemble sur une seule page (meme design)
        all_elements = header_elements + table_elements
        elements.append(KeepTogether(all_elements))
        
        return elements
    
    def _prepare_inventory_jobs_table_rows(self, job_details, counting, job):
        """
        Prépare toutes les lignes du tableau pour l'API inventory jobs
        Utilise JobDetail + Stock comme source de données
        """
        rows = []
        
        # Récupérer tous les stocks pour vérifier si au moins un produit supporte DLC
        all_stocks = []
        for job_detail in job_details:
            location = job_detail.location
            stocks = self.repository.get_stocks_by_location_and_inventory(location, job.inventory)
            if stocks:
                all_stocks.extend(stocks)
        
        # Créer une liste de produits pour vérifier DLC (même logique que counting_details)
        products_with_dlc = []
        for stock in all_stocks:
            if stock.product and hasattr(stock.product, 'dlc') and stock.product.dlc:
                products_with_dlc.append(stock.product)
        
        for job_detail in job_details:
            location = job_detail.location
            stocks = self.repository.get_stocks_by_location_and_inventory(location, job.inventory)
            has_stock_for_location = len(stocks) > 0 if stocks else False
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock_for_location and stocks:
                    # Une ligne par produit
                    for stock in stocks:
                        row = {
                            'location': location.location_reference,
                            'internal_product_code': stock.product.Internal_Product_Code if stock.product and stock.product.Internal_Product_Code else '-',
                            'barcode': stock.product.Barcode if stock.product and stock.product.Barcode else '-',
                            'designation': stock.product.Short_Description if stock.product else '-',
                            'quantite_theorique': stock.quantity_available,
                            'quantite_physique': '',  # Vide pour saisie manuelle
                            'n_lot': stock.product and stock.product.n_lot if stock.product else False,
                        }
                        # Ajouter DLC seulement si le comptage le supporte ET si le produit supporte DLC
                        # Utiliser la même logique que _prepare_job_assignment_table_rows avec _should_show_dlc
                        # Pour Stock, on vérifie si le produit a DLC activé et si counting supporte DLC
                        if self._should_show_dlc(counting, products_with_dlc):
                            # Stock n'a pas de champ dlc directement, donc on met '-' pour l'inventaire jobs
                            # (car on n'a pas de date DLC dans Stock, seulement le flag product.dlc)
                            row['dlc'] = '-'  # Pas de date DLC disponible dans Stock
                        rows.append(row)
                else:
                    # Pas de stock - une ligne vide
                    row = {
                        'location': location.location_reference,
                        'internal_product_code': ' ',
                        'barcode': ' ',
                        'designation': ' ',
                        'quantite_theorique': ' ',
                        'quantite_physique': '',  # Vide pour saisie
                        'n_lot': False,
                    }
                    # Ajouter DLC seulement si nécessaire (même logique que ci-dessus)
                    if self._should_show_dlc(counting, products_with_dlc):
                        row['dlc'] = '-'
                    rows.append(row)
        
        return rows
    
    def _create_empty_rows_for_inventory_jobs(self, num_rows, counting, has_dlc):
        """
        Crée des lignes vides pour compléter le tableau jusqu'à 40 lignes
        Structure identique aux lignes de données
        Utilise '-' pour toutes les colonnes sauf quantite_physique (vide pour saisie)
        """
        empty_rows = []
        
        for _ in range(num_rows):
            row = {
                'location': ' ',
                'internal_product_code': ' ',
                'barcode': ' ',
                'designation': ' ',
                'quantite_theorique': ' ',
                'quantite_physique': '',  # Vide pour saisie manuelle
                'n_lot': False,
            }
            # Ajouter DLC seulement si présent dans les autres lignes
            if has_dlc:
                row['dlc'] = '-'
            empty_rows.append(row)
        
        return empty_rows
    
    def _build_inventory_jobs_table_from_rows(self, rows, counting, page_num, total_pages):
        """
        Construit le tableau pour l'API inventory jobs à partir des rows préparées
        Utilise le même design que _build_job_assignment_table_from_rows
        """
        elements = []
        styles = getSampleStyleSheet()
        
        # Style pour la désignation (permet le retour à la ligne)
        designation_style = ParagraphStyle(
            'Designation',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#000000')
        )
        
        # Vérifier si on affiche la quantité théorique
        show_theorique = counting.show_theorique if hasattr(counting, 'show_theorique') else False
        
        # Déterminer si on affiche DLC en utilisant la méthode helper
        # Vérifier dans les rows si au moins un produit a DLC activé
        # Extraire les produits des rows pour vérification
        has_product_with_dlc = False
        if rows and len(rows) > 0:
            # Les rows contiennent des dictionnaires avec les données
            # Vérifier si 'dlc' est présent dans au moins un row (signifie que le produit supporte DLC)
            for row in rows:
                if 'dlc' in row:
                    has_product_with_dlc = True
                    break
        
        # Si aucun produit n'a DLC dans les rows, ne pas afficher la colonne
        # même si counting.dlc est True
        show_dlc = self._should_show_dlc(counting) if has_product_with_dlc else False
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article - toujours afficher Article et Désignation pour le PDF
            headers.append('Article')  # Internal_Product_Code
            headers.append('CAB')  # Barcode
            headers.append('Désignation')
            headers.append('QTE')  # Toujours présent
            
            if show_theorique:
                headers.append('QTE théorique')
            
            # Colonnes optionnelles - Ne pas afficher DLC si show_dlc est False
            if show_dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
        else:
                # Mode vrac
                if has_stock_for_location and stocks:
                    total_quantite_theorique = sum(s.quantity_available for s in stocks)
                    row = {
                        'location': location.location_reference,
                        'quantite_theorique': total_quantite_theorique,
                        'quantite_physique': '',  # Vide pour saisie manuelle
                    }
                else:
                    row = {
                        'location': location.location_reference,
                        'quantite_theorique': '-',
                        'quantite_physique': '',  # Vide pour saisie
                    }
                rows.append(row)
        
        return rows
    
    def _build_inventory_jobs_table_from_rows(self, rows, counting, page_num, total_pages):
        """
        Construit le tableau pour l'API inventory jobs
        Logique spécifique à l'API inventory/<int:inventory_id>/jobs/pdf/
        """
        elements = []
        styles = getSampleStyleSheet()
        
        # Style pour la désignation avec retour à la ligne automatique
        designation_style = ParagraphStyle(
            'DesignationStyle',
            parent=styles['Normal'],
            fontSize=9,  # Réduit pour économiser l'espace
            textColor=colors.black,
            fontName='Arial',
            alignment=0,  # Left align
            leading=8,  # Modéré pour plus d'espace vertical sans dépasser
            spaceBefore=0,
            spaceAfter=0,
            wordWrap='CJK',  # Permet le retour à la ligne automatique
        )
        
        # Déterminer si on affiche la quantité théorique
        show_theorique = counting.quantity_show or counting.stock_situation
        
        # Déterminer si on affiche DLC en utilisant la méthode helper
        # Vérifier dans les rows si au moins un produit a DLC activé
        # Extraire les produits des rows pour vérification
        has_product_with_dlc = False
        if rows and len(rows) > 0:
            # Les rows contiennent des dictionnaires avec les données
            # Vérifier si 'dlc' est présent dans au moins un row (signifie que le produit supporte DLC)
            for row in rows:
                if 'dlc' in row:
                    has_product_with_dlc = True
                    break
        
        # Si aucun produit n'a DLC dans les rows, ne pas afficher la colonne
        # même si counting.dlc est True
        show_dlc = self._should_show_dlc(counting) if has_product_with_dlc else False
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article - toujours afficher Article et Désignation pour le PDF
            headers.append('Article')  # Internal_Product_Code
            headers.append('CAB')  # Barcode
            headers.append('Désignation')
            headers.append('QTE')  # Toujours présent
            
            if show_theorique:
                headers.append('QTE théorique')
            
            # Colonnes optionnelles - Ne pas afficher DLC si show_dlc est False
            if show_dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
        else:
            # Mode vrac
            headers.append('QTE')  # Toujours présent
            
            if show_theorique:
                headers.append('QTE théorique')
        
        # Trouver l'index de la colonne Désignation
        designation_index = headers.index('Désignation') if 'Désignation' in headers else None
        
        # Construire les données
        data = [headers]
        
        for row in rows:
            table_row = [row['location']]
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article - toujours afficher Article et Désignation pour le PDF
                # Article (Internal_Product_Code)
                table_row.append(row.get('internal_product_code', '-'))
                # Code à barre (Barcode)
                table_row.append(row.get('barcode', '-'))
                # Désignation - utiliser Paragraph pour permettre le retour à la ligne
                designation_text = row.get('designation', '-')
                # Échapper les caractères spéciaux pour XML/HTML
                designation_text = str(designation_text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                table_row.append(Paragraph(designation_text, designation_style))
                
                # Quantité (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
                
                # Colonnes optionnelles - ajouter seulement si show_dlc est True (même logique que job-assignment)
                if show_dlc:
                    # DLC est déjà formatée comme date ou '-' dans _prepare_inventory_jobs_table_rows
                    dlc_value = row.get('dlc', '-')
                    # Convertir False en '-' pour éviter d'afficher "False"
                    if dlc_value is False or dlc_value == False or str(dlc_value).lower() == 'false':
                        dlc_value = '-'
                    table_row.append(str(dlc_value) if dlc_value else '-')
                if counting.n_lot:
                    # n_lot est déjà la valeur ou '-' dans _prepare_table_rows_from_counting_details
                    table_row.append(row.get('n_lot', '-'))
            else:
                # Mode vrac
                # Quantité (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
            
            data.append(table_row)
        
        if len(data) == 1:  # Seulement les headers
            return elements
        
        # Créer le tableau - pas de répétition de l'en-tête (repeatRows=0)
        # Permettre la division du tableau si nécessaire (splitByRow=1)
        # Aligner le tableau avec le pied de page (mêmes marges que le footer des deux côtés)
        footer_margin = 0.5*cm  # Marge du footer (identique à celle utilisée dans le footer)
        document_left_margin = 0.1*cm  # leftMargin du document
        document_right_margin = 0.1*cm  # rightMargin du document
        # Footer commence à: doc.leftMargin + footer_margin = 0.1 + 0.5 = 0.6cm
        # Footer se termine à: A4[0] - doc.rightMargin - footer_margin = 21.0 - 0.1 - 0.5 = 20.4cm
        # Tableau doit avoir exactement les mêmes marges que le footer
        # Largeur totale disponible dans le document = A4[0] - document_left_margin - document_right_margin
        # = 21.0 - 0.1 - 0.1 = 20.8cm
        # Pour avoir les mêmes marges que le footer, on doit ajouter 0.5cm à gauche et 0.5cm à droite
        # Largeur disponible pour le tableau de données = 20.8 - 0.5 - 0.5 = 19.8cm
        footer_margin = 0.5*cm
        document_left_margin = 0.1*cm
        document_right_margin = 0.1*cm
        total_document_width = A4[0] - document_left_margin - document_right_margin  # 20.8cm
        available_table_width = total_document_width - footer_margin - footer_margin  # 19.8cm
        col_widths = self._calculate_merged_column_widths(headers, available_table_width, margins=0*cm)
        
        # Style du tableau
        table_style = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Augmenter la taille de l'en-tête
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),  # Réduit pour économiser l'espace
            ('TOPPADDING', (0, 0), (-1, 0), 3),  # Réduit pour économiser l'espace
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Centrer verticalement l'en-tête
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),  # Mettre en gras
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Augmenter la taille
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),  # Toutes les valeurs centrées horizontalement
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # Centrer verticalement le corps
        ]
        
        # Aligner la colonne Désignation au centre si elle existe
        if designation_index is not None:
            table_style.append(('ALIGN', (designation_index, 1), (designation_index, -1), 'CENTER'))  # Centrer aussi la désignation
        
        # Ajouter les lignes de séparation entre toutes les colonnes
        # Padding modéré pour augmenter la hauteur et la largeur sans dépasser la page
        table_style.extend([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Ligne plus épaisse sous l'en-tête
            ('TOPPADDING', (0, 1), (-1, -1), 1.5),  # Réduit pour économiser l'espace
            ('BOTTOMPADDING', (0, 1), (-1, -1), 1.5),  # Réduit pour économiser l'espace
            ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Réduit pour augmenter la largeur du tableau
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Réduit pour augmenter la largeur du tableau
        ])
        
        # Ajuster le padding de la colonne Désignation pour mieux gérer les retours à la ligne
        if designation_index is not None:
            table_style.append(('TOPPADDING', (designation_index, 1), (designation_index, -1), 1.5))
            table_style.append(('BOTTOMPADDING', (designation_index, 1), (designation_index, -1), 1.5))
        
        # Ajouter des colonnes vides au début et à la fin pour créer les marges identiques au footer
        # Le footer a les mêmes marges des deux côtés: doc.leftMargin + footer_margin = 0.6cm
        # et doc.rightMargin + footer_margin = 0.6cm
        footer_margin = 0.5*cm
        document_left_margin = 0.1*cm
        document_right_margin = 0.1*cm
        # Le spacer gauche doit compenser la différence entre la marge du footer et la marge du document
        # Footer position gauche: 0.6cm, Document margin: 0.1cm, donc spacer = 0.5cm
        left_spacer = footer_margin  # 0.5cm pour arriver à 0.6cm total (0.1 + 0.5)
        # Le spacer droit doit être identique au spacer gauche pour avoir les mêmes marges
        right_spacer = footer_margin  # 0.5cm pour arriver à 0.6cm total (0.1 + 0.5)
        
        # Ajouter une colonne vide au début et à la fin de chaque ligne pour créer les marges
        extended_data = []
        for row in data:
            extended_row = [''] + list(row) + ['']
            extended_data.append(extended_row)
        
        # Créer les largeurs de colonnes avec les spacers
        # Vérifier que la somme des largeurs correspond à la largeur disponible dans le document
        extended_col_widths = [left_spacer] + col_widths + [right_spacer]
        total_width = sum(extended_col_widths)
        expected_width = A4[0] - document_left_margin - document_right_margin  # 20.8cm
        
        # Ajuster si nécessaire pour s'assurer que le tableau occupe toute la largeur disponible
        # IMPORTANT: Garder les marges gauche et droite IDENTIQUES en ajustant les colonnes de données
        if abs(total_width - expected_width) > 0.01*cm:
            width_diff = expected_width - total_width
            # Ajuster les colonnes de données proportionnellement pour garder les marges identiques
            if sum(col_widths) > 0:
                ratio = (sum(col_widths) + width_diff) / sum(col_widths)
                col_widths = [w * ratio for w in col_widths]
                # Recalculer avec les nouvelles largeurs, en gardant les marges identiques
                extended_col_widths = [left_spacer] + col_widths + [right_spacer]
        
        # Créer le tableau étendu avec les marges
        extended_table = Table(extended_data, colWidths=extended_col_widths, repeatRows=0, splitByRow=1)
        
        # Créer un nouveau style pour le tableau étendu
        # Les colonnes de données sont maintenant aux indices 1 à -2 (colonne 0 et -1 sont vides)
        extended_table_style = []
        
        # Appliquer le style original aux colonnes de données seulement (1 à -2)
        # En-tête
        extended_table_style.extend([
            ('BACKGROUND', (1, 0), (-2, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (1, 0), (-2, 0), colors.black),
            ('ALIGN', (1, 0), (-2, 0), 'CENTER'),
            ('FONTNAME', (1, 0), (-2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (-2, 0), 9),
            ('BOTTOMPADDING', (1, 0), (-2, 0), 3),
            ('TOPPADDING', (1, 0), (-2, 0), 3),
            ('VALIGN', (1, 0), (-2, 0), 'MIDDLE'),
        ])
        
        # Corps
        extended_table_style.extend([
            ('BACKGROUND', (1, 1), (-2, -1), colors.white),
            ('TEXTCOLOR', (1, 1), (-2, -1), colors.black),
            ('FONTNAME', (1, 1), (-2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (-2, -1), 8),
            ('ALIGN', (1, 1), (-2, -1), 'CENTER'),
            ('VALIGN', (1, 1), (-2, -1), 'MIDDLE'),
        ])
        
        # Aligner la colonne Désignation au centre si elle existe (décaler l'index de +1)
        if designation_index is not None:
            extended_table_style.append(('ALIGN', (designation_index + 1, 1), (designation_index + 1, -1), 'CENTER'))
        
        # Ajouter les lignes de séparation et le padding
        extended_table_style.extend([
            ('GRID', (1, 0), (-2, -1), 0.5, colors.black),
            ('LINEBELOW', (1, 0), (-2, 0), 1, colors.black),
            ('TOPPADDING', (1, 1), (-2, -1), 1.5),
            ('BOTTOMPADDING', (1, 1), (-2, -1), 1.5),
            ('LEFTPADDING', (1, 0), (-2, -1), 2),
            ('RIGHTPADDING', (1, 0), (-2, -1), 2),
        ])
        
        # Ajuster le padding de la colonne Désignation
        if designation_index is not None:
            extended_table_style.append(('TOPPADDING', (designation_index + 1, 1), (designation_index + 1, -1), 1.5))
            extended_table_style.append(('BOTTOMPADDING', (designation_index + 1, 1), (designation_index + 1, -1), 1.5))
        
        # Style pour les colonnes vides (première et dernière) - les rendre complètement invisibles
        extended_table_style.extend([
            ('BACKGROUND', (0, 0), (0, -1), colors.white),  # Colonne gauche vide
            ('BACKGROUND', (-1, 0), (-1, -1), colors.white),  # Colonne droite vide
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),  # Texte blanc (invisible)
            ('TEXTCOLOR', (-1, 0), (-1, -1), colors.white),  # Texte blanc (invisible)
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 0),
            ('LEFTPADDING', (-1, 0), (-1, -1), 0),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (0, -1), 0),
            ('BOTTOMPADDING', (0, 0), (0, -1), 0),
            ('TOPPADDING', (-1, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (-1, 0), (-1, -1), 0),
            # Masquer toutes les bordures des colonnes vides
            ('LINELEFT', (0, 0), (0, -1), 0, colors.white),
            ('LINERIGHT', (0, 0), (0, -1), 0, colors.white),
            ('LINETOP', (0, 0), (0, 0), 0, colors.white),
            ('LINEBOTTOM', (0, -1), (0, -1), 0, colors.white),
            ('LINELEFT', (-1, 0), (-1, -1), 0, colors.white),
            ('LINERIGHT', (-1, 0), (-1, -1), 0, colors.white),
            ('LINETOP', (-1, 0), (-1, 0), 0, colors.white),
            ('LINEBOTTOM', (-1, -1), (-1, -1), 0, colors.white),
        ])
        
        extended_table.setStyle(TableStyle(extended_table_style))
        
        elements.append(extended_table)
        
        # Pas de pagination ici, elle sera dans le footer fixe
        return elements
    
    def _build_inventory_jobs_page_header(self, inventory, job, user, counting, warehouse_info, account_info, page_num, total_pages):
        """
        Construit l'en-tête de page pour l'API inventory jobs
        Logique spécifique à l'API inventory/<int:inventory_id>/jobs/pdf/
        """
        elements = []
        styles = getSampleStyleSheet()
        
        # Ajouter un espace en haut de la page
        elements.append(Spacer(1, 0.5*cm))
        
        # Style pour les labels (en gras) - aligné à gauche
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=0,  # Left
        )
        
        # Style pour les labels alignés à droite
        label_style_right = ParagraphStyle(
            'LabelStyleRight',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=2,  # Right
        )
        
        # Informations sur une seule ligne: Ordre de comptage à gauche | Équipe affectée à droite
        info_row_data = [
            Paragraph(f"<b>comptage :</b> {counting.order}", label_style),
            Paragraph(f"<b>Équipe :</b> {user if user else 'Non affecté'}", label_style_right),
        ]
        
        info_table = Table([info_row_data], colWidths=[8*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Première colonne à gauche
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Deuxième colonne à droite
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(info_table)
        # Ajouter un espace entre les informations et le tableau
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_job_details_table(self, job_details, counting, job):
        """Construit le tableau des détails du job (JobDetail)"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        has_stock = self._inventory_has_stock(job.inventory)
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article
            if counting.show_product:
                headers.append('Article')
            headers.append('QTE')
            # Ne pas afficher DLC si counting.dlc est False
            if counting.dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
        else:
            # Mode vrac
            headers.append('QTE')
        
        # Construire les données
        data = [headers]
        
        for job_detail in job_details:
            location = job_detail.location
            row = [location.location_reference]
            
            # Récupérer les stocks
            stocks = self.repository.get_stocks_by_location_and_inventory(location, job.inventory)
            has_stock_for_location = len(stocks) > 0 if stocks else False
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock_for_location and stocks:
                    # Une ligne par produit
                    for stock in stocks:
                        product_row = [location.location_reference]
                        if counting.show_product:
                            product_row.append(stock.product.Short_Description if stock.product else '-')
                        product_row.append(stock.quantity_available)
                        if counting.dlc:
                            product_row.append('Oui' if (stock.product and stock.product.dlc) else '-')
                        if counting.n_lot:
                            product_row.append('Oui' if (stock.product and stock.product.n_lot) else '-')
                        data.append(product_row)
                else:
                    # Pas de stock
                    row_data = [location.location_reference]
                    if counting.show_product:
                        row_data.append('-')
                    row_data.append('-')
                    if counting.dlc:
                        row_data.append('-')
                    if counting.n_lot:
                        row_data.append('-')
                    data.append(row_data)
            else:
                # Mode vrac
                if has_stock_for_location and stocks:
                    total_quantity = sum(s.quantity_available for s in stocks)
                    row.append(total_quantity)
                else:
                    row.append('-')
                data.append(row)
        
        if len(data) == 1:  # Seulement les headers
            return elements
        
        # Créer le tableau
        # Calculer la largeur disponible en tenant compte des marges du document (0.1 cm de chaque côté)
        document_margins = 0.1*cm + 0.1*cm  # leftMargin + rightMargin (réduites de 0.2cm à 0.1cm)
        # Ajouter l'espace réduit des marges (0.1cm de chaque côté = 0.2cm total) à la largeur du tableau
        margin_reduction = (0.2*cm - 0.1*cm) * 2  # Espace réduit des marges
        available_table_width = A4[0] - document_margins + margin_reduction
        col_widths = self._calculate_merged_column_widths(headers, available_table_width)
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style du tableau
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Emplacement centré
            
            # Aligner QTE à droite
            ('ALIGN', (headers.index('QTE'), 1), (headers.index('QTE'), -1), 'RIGHT'),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*cm))
        
        return elements
    
    def _build_main_header(self, inventory):
        """Construit l'en-tete principal du PDF avec les informations de l'inventaire"""
        styles = getSampleStyleSheet()
        
        elements = []
        
        # Espace de 1.5 cm en haut pour déplacer le contenu vers le bas
        elements.append(Spacer(1, 1.5*cm))
        
        # Style pour le titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#000000'),
            spaceAfter=20,
            alignment=1,
        )
        
        # Titre
        title = Paragraph(f"<b>Jobs d'Inventaire</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.4*cm))
        
        # Informations de l'inventaire
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=5,
            alignment=1,
        )
        
        elements.append(Paragraph(f"<b>Libelle:</b> {inventory.label}", info_style))
        elements.append(Paragraph(f"<b>Reference:</b> {inventory.reference}", info_style))
        elements.append(Paragraph(
            f"<b>Date de generation:</b> {timezone.now().strftime('%d/%m/%Y a %H:%M')}", 
            info_style
        ))
        
        return elements
    
    def _build_counting_header(self, counting):
        """Construit l'en-tete pour un comptage avec mode et ordre"""
        styles = getSampleStyleSheet()
        
        elements = []
        
        # Style pour le titre du comptage
        counting_title_style = ParagraphStyle(
            'CountingTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=10,
            leftIndent=0,
        )
        
        # Titre du comptage
        counting_title = Paragraph(
            f"<b>Comptage {counting.order}: {counting.count_mode.upper()}</b>", 
            counting_title_style
        )
        elements.append(counting_title)
        
        return elements
    
    def _build_user_section(self, user, jobs, counting):
        """Construit une section pour un utilisateur avec un tableau fusionné de tous les jobs"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre utilisateur
        if user:
            user_title = f"<b>Affecte a: {user}</b>"
        else:
            user_title = "<b>Non affecte</b>"
        
        user_style = ParagraphStyle(
            'UserTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#000000'),
            spaceAfter=8,
        )
        elements.append(Paragraph(user_title, user_style))
        elements.append(Spacer(1, 0.2*cm))
        
        # Construire un seul tableau fusionné pour tous les jobs
        elements.extend(self._build_merged_jobs_table(jobs, counting))
        
        return elements
    
    def _build_merged_jobs_table(self, jobs, counting):
        """Construit un tableau fusionné pour tous les jobs d'un utilisateur"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Collecter tous les job_details de tous les jobs
        all_job_details_data = []
        
        for job in jobs:
            # Vérifier si le job a un assignment pour ce comptage
            assignments = self.repository.get_assignments_by_job(job)
            has_assignment_for_counting = any(a.counting_id == counting.id for a in assignments)
            
            if not has_assignment_for_counting:
                continue
            
            # Récupérer tous les job details du job
            all_job_details = self.repository.get_job_details_by_job(job)
            
            # Filtrer les job_details
            job_details = []
            for jd in all_job_details:
                if jd.counting_id is None or jd.counting_id == counting.id:
                    job_details.append((job, jd))
            
            # Collecter les données pour chaque job_detail
            for job, job_detail in job_details:
                location = job_detail.location
                
                # Récupérer les stocks pour cet emplacement
                stocks = self.repository.get_stocks_by_location_and_inventory(
                    location,
                    job.inventory
                )
                
                has_stock = len(stocks) > 0 if stocks else False
                
                if 'vrac' in counting.count_mode.lower():
                    # Mode vrac
                    if has_stock:
                        total_quantity = sum(s.quantity_available for s in stocks)
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'quantity': total_quantity
                        })
                    else:
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'quantity': '-'
                        })
                else:
                    # Mode par article
                    if has_stock:
                        for stock in stocks:
                            all_job_details_data.append({
                                'job_reference': job.reference,
                                'job_status': job.status,
                                'location': location.location_reference,
                                'article': stock.product.Short_Description if stock.product else '-',
                                'quantity': stock.quantity_available,
                                'dlc': counting.dlc and stock.product and stock.product.dlc,
                                'n_lot': counting.n_lot and stock.product and stock.product.n_lot,
                                'stock': stock
                            })
                    else:
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'article': '-',
                            'quantity': '-',
                            'dlc': False,
                            'n_lot': False
                        })
        
        if not all_job_details_data:
            no_detail_style = ParagraphStyle(
                'NoDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                spaceAfter=10,
            )
            elements.append(Paragraph("<i>Aucun emplacement trouvé</i>", no_detail_style))
            elements.append(Spacer(1, 0.3*cm))
            return elements
        
        # Construire les en-têtes selon la configuration
        headers = ['Job', 'Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article
            # Colonne Article seulement si show_product est activé
            if counting.show_product:
                headers.append('Article')
            
            headers.append('QTE')
            
            # Colonnes optionnelles selon la configuration du counting
            if counting.dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
        else:
            # Mode vrac
            headers.append('QTE')
        
        # Construire les données du tableau
        data = [headers]
        
        for detail_data in all_job_details_data:
            row = [
                detail_data['job_reference'],
                detail_data['location']
            ]
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                # Ajouter Article seulement si show_product est activé
                if counting.show_product:
                    row.append(detail_data.get('article', '-'))
                
                row.append(detail_data.get('quantity', '-'))
                
                # Colonnes optionnelles selon la configuration
                if counting.dlc:
                    row.append('Oui' if detail_data.get('dlc', False) else '-')
                if counting.n_lot:
                    row.append('Oui' if detail_data.get('n_lot', False) else '-')
            else:
                # Mode vrac
                row.append(detail_data.get('quantity', '-'))
            
            data.append(row)
        
        # Créer le tableau
        # Calculer la largeur disponible en tenant compte des marges du document (0.1 cm de chaque côté)
        document_margins = 0.1*cm + 0.1*cm  # leftMargin + rightMargin (réduites de 0.2cm à 0.1cm)
        # Ajouter l'espace réduit des marges (0.1cm de chaque côté = 0.2cm total) à la largeur du tableau
        margin_reduction = (0.2*cm - 0.1*cm) * 2  # Espace réduit des marges
        available_table_width = A4[0] - document_margins + margin_reduction
        col_widths = self._calculate_merged_column_widths(headers, available_table_width)
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style du tableau
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Emplacement centré
            
            # Aligner la colonne QTE à droite (trouver son index)
            ('ALIGN', (headers.index('QTE'), 1), (headers.index('QTE'), -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_job_table(self, job, counting, user=None):
        """Construit le tableau pour un job"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Ajouter un titre pour le job avec sa référence et statut
        job_title_style = ParagraphStyle(
            'JobTitle',
            parent=styles['Heading4'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=5,
            spaceBefore=8,
        )
        job_title = Paragraph(
            f"<b>Job:</b> {job.reference} | <b>Statut:</b> {job.status}",
            job_title_style
        )
        elements.append(job_title)
        elements.append(Spacer(1, 0.2*cm))
        
        # Vérifier si le job a un assignment pour ce comptage
        assignments = self.repository.get_assignments_by_job(job)
        has_assignment_for_counting = any(a.counting_id == counting.id for a in assignments)
        
        if not has_assignment_for_counting:
            # Le job n'a pas d'assignment pour ce comptage, ne pas l'afficher
            return elements
        
        # Recuperer tous les job details du job
        # Le job est déjà filtré par counting via l'assignement, donc on prend tous les job_details
        all_job_details = self.repository.get_job_details_by_job(job)
        
        # Si certains job_details ont un counting défini, filtrer ceux qui correspondent ou sont null
        # Sinon, prendre tous les job_details
        job_details = []
        for jd in all_job_details:
            # Si le counting du job_detail est null OU correspond au counting recherché
            if jd.counting_id is None or jd.counting_id == counting.id:
                job_details.append(jd)
        
        if not job_details:
            # Afficher un message si aucun job detail trouvé
            no_detail_style = ParagraphStyle(
                'NoDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                spaceAfter=10,
            )
            elements.append(Paragraph("<i>Aucun emplacement trouvé pour ce job</i>", no_detail_style))
            elements.append(Spacer(1, 0.3*cm))
            return elements
        
        # Determiner les colonnes selon le mode de comptage
        if 'vrac' in counting.count_mode.lower():
            # Mode vrac: pas de colonnes article, dlc, n_lot
            headers = ['Emplacement', 'Quantite']
        else:
            # Mode par article: toutes les colonnes
            headers = ['Emplacement', 'Article', 'Quantite', 'DLC', 'N° Lot']
        
        # Recuperer les stocks de l'inventaire
        has_stock = self._inventory_has_stock(job.inventory)
        
        # Construire les donnees du tableau
        data = [headers]
        
        for job_detail in job_details:
            location = job_detail.location
            row_data = [location.location_reference]
            
            # Recuperer les stocks pour cet emplacement
            stocks = self.repository.get_stocks_by_location_and_inventory(
                location,
                job.inventory
            )
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock and stocks:
                    # Afficher chaque produit du stock
                    for stock in stocks:
                        article = stock.product.Short_Description if stock.product else '-'
                        quantity = stock.quantity_available
                        
                        dlc = '-'
                        if counting.dlc and stock.product and stock.product.dlc:
                            dlc = 'Oui'
                        
                        n_lot = '-'
                        if counting.n_lot and stock.product and stock.product.n_lot:
                            n_lot = 'Oui'
                        
                        row_data = [location.location_reference, article, quantity, dlc, n_lot]
                        data.append(row_data)
                else:
                    # Pas de stock, afficher juste l'emplacement
                    row_data = [location.location_reference, '-', '-']
                    if counting.dlc:
                        row_data.append('-')
                    if counting.n_lot:
                        row_data.append('-')
                    data.append(row_data)
            else:
                # Mode vrac: juste la quantite
                if has_stock and stocks:
                    # Somme des quantites
                    total_quantity = sum(s.quantity_available for s in stocks)
                    row_data.append(total_quantity)
                else:
                    row_data.append('-')
                data.append(row_data)
        
        # Creer le tableau
        col_widths = self._calculate_column_widths(headers, A4[0])
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style simple du tableau
        table.setStyle(TableStyle([
            # En-tete
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _calculate_column_widths(self, headers, page_width, margins=4*cm):
        """Calcule la largeur des colonnes"""
        available_width = page_width - margins
        
        if len(headers) == 2:
            # Mode vrac: 2 colonnes
            return [available_width * 0.6, available_width * 0.4]
        else:
            # Mode par article: 6 colonnes (Emplacement, Article, CAB, Désignation, QTE, autres)
            return [available_width * 0.15, available_width * 0.30, available_width * 0.15,  # CAB augmenté de 0.12 à 0.15
                   available_width * 0.12, available_width * 0.14, available_width * 0.14]  # Dernière colonne ajustée
    
    def _calculate_merged_column_widths(self, headers, page_width, margins=0.1*cm):
        """Calcule la largeur des colonnes pour le tableau fusionné"""
        available_width = page_width - margins
        num_headers = len(headers)
        
        if num_headers == 0:
            return []
        
        # Colonnes fixes avec largeurs réduites pour Emplacement, Article, CAB, QTE
        # et plus d'espace pour Désignation
        fixed_widths = {
            'Job': 0.15,
            'Emplacement': 0.15,  # Réduit de 0.20 à 0.12
            'Article': 0.10,  # Réduit
            'CAB': 0.13,  # Augmenté de 0.10 à 0.13
            'QTE': 0.08,  # Réduit
            'Désignation': 0.40,  # Augmenté de 0.25 à 0.40 pour plus d'espace
            'quantite_physique': 0.08,
            'QTE théorique': 0.10,
        }
        
        # Calculer les largeurs
        widths = []
        used_percentage = 0
        
        # Colonnes fixes en premier
        for header in headers:
            if header in fixed_widths:
                widths.append(available_width * fixed_widths[header])
                used_percentage += fixed_widths[header]
            else:
                # Pour les colonnes variables, on calculera après
                widths.append(None)
        
        # Répartir l'espace restant pour les colonnes variables
        remaining_percentage = 1.0 - used_percentage
        variable_headers_count = sum(1 for w in widths if w is None)
        
        if variable_headers_count > 0:
            width_per_variable = remaining_percentage / variable_headers_count
            widths = [w if w is not None else available_width * width_per_variable for w in widths]
        
        return widths
    
    def _group_jobs_by_user(self, jobs):
        """Groupe les jobs par utilisateur"""
        jobs_by_user = {}
        
        for job in jobs:
            assignments = self.repository.get_assignments_by_job(job)
            user = None
            
            # Chercher l'utilisateur dans les assignments
            for assignment in assignments:
                if assignment.session:
                    user = assignment.session.username
                    break
            
            if user not in jobs_by_user:
                jobs_by_user[user] = []
            
            jobs_by_user[user].append(job)
        
        return jobs_by_user
    
    def _inventory_has_stock(self, inventory):
        """Verifie si l'inventaire a des stocks"""
        from apps.masterdata.models import Stock
        return Stock.objects.filter(inventory=inventory).exists()
    
    def generate_job_assignment_pdf(
        self,
        job_id: int,
        assignment_id: int,
        equipe_id: Optional[int] = None
    ) -> BytesIO:
        """
        Genere un PDF pour un job/assignment/equipe specifique
        Utilise les donnees de CountingDetail au lieu de Stock
        
        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            equipe_id: ID de l'equipe (personne ou personne_two) - optionnel
            
        Returns:
            BytesIO: Le contenu du PDF en memoire
        """
        # Recuperer l'assignment
        assignment = self.repository.get_assignment_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment avec l'ID {assignment_id} non trouve")
        
        # Verifier que l'assignment correspond au job
        if assignment.job_id != job_id:
            raise ValueError(f"L'assignment {assignment_id} n'appartient pas au job {job_id}")
        
        # Recuperer le job
        job = assignment.job
        if not job:
            raise ValueError(f"Job avec l'ID {job_id} non trouve")
        
        # Recuperer l'inventaire
        inventory = job.inventory
        if not inventory:
            raise ValueError(f"Inventaire non trouve pour le job {job_id}")
        
        # Recuperer le counting depuis l'assignment
        counting = assignment.counting
        if not counting:
            raise ValueError(f"Comptage non trouve pour l'assignment {assignment_id}")
        
        # Debug: verifier la valeur de counting.dlc dans la base de donnees
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Counting DLC value (from DB): {counting.dlc}, Counting reference: {counting.reference}, Count mode: {counting.count_mode}")
        
        # Si le mode de comptage ne supporte pas DLC, forcer counting.dlc a False
        # Certains modes de comptage ne devraient pas avoir DLC active
        if 'image' in counting.count_mode.lower() or 'vrac' in counting.count_mode.lower():
            if counting.dlc:
                logger.warning(f"Mode de comptage '{counting.count_mode}' ne devrait pas avoir DLC active. Valeur actuelle: {counting.dlc}")
                # Ne pas modifier la base de donnees, mais forcer l'affichage a False dans le code
                # counting.dlc = False  # Decommenter pour forcer la correction en base
                # counting.save()
        
        # Recuperer les infos du warehouse et account
        warehouse_info = self._get_warehouse_info(inventory)
        account_info = self._get_account_info(inventory)
        
        # Recuperer la session affectee dans l'assignment
        session = assignment.session
        
        # Preparer le nom de la session pour l'affichage dans l'en-tete
        session_nom = session.username if session else "Non affecte"
        
        # Recuperer les personnes de l'equipe (pour equipe_nom si necessaire)
        personne = assignment.personne
        personne_two = assignment.personne_two
        
        # Debug: logger les valeurs pour comprendre pourquoi elles sont null
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Assignment ID: {assignment_id}, Personne 1: {personne}, Personne 2: {personne_two}")
        if personne:
            logger.info(f"Personne 1 - ID: {personne.id}, Nom: {personne.nom}, Prenom: {personne.prenom}")
        if personne_two:
            logger.info(f"Personne 2 - ID: {personne_two.id}, Nom: {personne_two.nom}, Prenom: {personne_two.prenom}")
        if not personne and not personne_two:
            logger.warning(f"ATTENTION: Aucune personne trouvée pour l'assignment {assignment_id}")
        
        # Si equipe_id est fourni, filtrer par cette personne
        if equipe_id:
            if personne and personne.id == equipe_id:
                equipe_nom = f"{personne.nom} {personne.prenom}"
            elif personne_two and personne_two.id == equipe_id:
                equipe_nom = f"{personne_two.nom} {personne_two.prenom}"
            else:
                raise ValueError(f"L'equipe {equipe_id} n'est pas associee a l'assignment {assignment_id}")
        else:
            # Construire le nom de l'equipe a partir des deux personnes
            equipe_parts = []
            if personne:
                equipe_parts.append(f"{personne.nom} {personne.prenom}")
            if personne_two:
                equipe_parts.append(f"{personne_two.nom} {personne_two.prenom}")
            equipe_nom = " / ".join(equipe_parts) if equipe_parts else "Non affecte"
        
        # Recuperer les counting details pour ce job et ce counting
        counting_details = self.repository.get_counting_details_by_job_and_counting(job, counting)
        
        if not counting_details:
            raise ValueError(f"Aucun detail de comptage trouve pour le job {job_id} et le comptage {counting.id}")
        
        # Creer le buffer PDF
        buffer = BytesIO()
        
        # Construire le contenu
        story = []
        
        # Construire les pages pour ce job avec la logique spécifique à l'assignment
        # Passer session_nom pour l'affichage dans l'en-tete "Utilisateur:"
        story.extend(self._build_job_assignment_pages(
            job, counting, session_nom, inventory, warehouse_info, account_info, counting_details
        ))
        
        # Creer le document PDF avec marges ajustees
        # Marge du bas augmentee pour laisser de la place aux signatures (4cm)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.1*cm,
            leftMargin=0.1*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm  # Espace pour les signatures
        )
        
        # Calculer la pagination - limiter à 40 lignes maximum sur une seule page
        page_info_map = {}
        lines_per_page = 40
        # Préparer les lignes pour calculer correctement
        all_table_rows = self._prepare_job_assignment_table_rows(counting_details, counting)
        # Limiter à 40 lignes maximum - une seule page
        total_rows = min(len(all_table_rows), lines_per_page)
        total_pages = 1  # Toujours une seule page avec maximum 40 lignes
        
        for page_num in range(total_pages):
            page_info_map[page_num + 1] = {
                'current': page_num + 1,
                'total': total_pages,
                'job_ref': job.reference
            }
        
        # Stocker les infos de pagination dans le document
        doc.page_info_map = page_info_map
        
        # Stocker les informations des personnes pour la signature
        # Stocker aussi le nom séparément pour la vérification
        personne_nom_value = None
        personne_prenom_value = None
        personne_full = None
        if personne:
            personne_nom_value = getattr(personne, 'nom', None)
            personne_prenom_value = getattr(personne, 'prenom', None)
            # Construire le nom complet seulement si au moins un champ existe
            if personne_nom_value or personne_prenom_value:
                parts = []
                if personne_nom_value:
                    parts.append(str(personne_nom_value).strip())
                if personne_prenom_value:
                    parts.append(str(personne_prenom_value).strip())
                personne_full = ' '.join(parts) if parts else None
        
        personne_two_nom_value = None
        personne_two_prenom_value = None
        personne_two_full = None
        if personne_two:
            personne_two_nom_value = getattr(personne_two, 'nom', None)
            personne_two_prenom_value = getattr(personne_two, 'prenom', None)
            # Construire le nom complet seulement si au moins un champ existe
            if personne_two_nom_value or personne_two_prenom_value:
                parts = []
                if personne_two_nom_value:
                    parts.append(str(personne_two_nom_value).strip())
                if personne_two_prenom_value:
                    parts.append(str(personne_two_prenom_value).strip())
                personne_two_full = ' '.join(parts) if parts else None
        
        doc.personne_info = {
            'personne': personne_full,
            'personne_nom': personne_nom_value,
            'personne_two': personne_two_full,
            'personne_two_nom': personne_two_nom_value
        }
        
        # Debug: logger les valeurs stockées
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Stockage personne_info: personne='{personne_full}', personne_nom='{personne_nom_value}', personne_two='{personne_two_full}', personne_two_nom='{personne_two_nom_value}'")
        logger.info(f"Personne objet: {personne}, Personne_two objet: {personne_two}")
        
        # Récupérer les dates de début et de fin de l'assignment
        date_debut = None
        date_fin = None
        
        if assignment.entame_date:
            date_debut = assignment.entame_date.strftime('%d/%m/%Y %H:%M')
        
        # Pour la date de fin, utiliser termine_date si disponible (priorité)
        # Sinon utiliser updated_at si le statut est TERMINE
        # Cela permet d'afficher la date même si termine_date n'a pas été rempli automatiquement
        if assignment.termine_date:
            date_fin = assignment.termine_date.strftime('%d/%m/%Y %H:%M')
        elif assignment.status == 'TERMINE' and assignment.updated_at:
            # Fallback sur updated_at si termine_date n'est pas rempli mais le statut est TERMINE
            date_fin = assignment.updated_at.strftime('%d/%m/%Y %H:%M')
        
        # Stocker les informations de l'inventaire pour le footer
        doc.inventory_info = {
            'reference': inventory.reference,
            'account_name': account_info['name'],
            'warehouse_name': warehouse_info['name'],
            'inventory_type': inventory.inventory_type,
            'date': inventory.date.strftime('%d/%m/%Y') if inventory.date else '-',
            'date_debut': date_debut or '-',
            'date_fin': date_fin or '-',
            'job_reference': job.reference
        }
        
        # Construire le PDF avec header (texte centré) et footer (pagination + signatures) personnalises pour job-assignment-pdf
        doc.build(story, 
                 onFirstPage=self._add_page_header_and_footer_job_assignment_pdf, 
                 onLaterPages=self._add_page_header_and_footer_job_assignment_pdf)
        
        # Reinitialiser le buffer
        buffer.seek(0)
        return buffer
    
    def _build_job_assignment_pages(
        self, 
        job, 
        counting, 
        session_nom, 
        inventory, 
        warehouse_info, 
        account_info, 
        counting_details
    ):
        """
        Construit les pages pour un job/assignment spécifique
        Logique spécifique à l'API jobs/<int:job_id>/assignments/<int:assignment_id>/pdf/
        """
        elements = []
        
        if not counting_details:
            return elements
        
        # Construire toutes les lignes du tableau d'abord
        all_table_rows = self._prepare_job_assignment_table_rows(counting_details, counting)
        
        if not all_table_rows:
            return elements
        
        # Limiter à exactement 40 lignes pour un seul tableau sur une seule page
        lines_per_page = 40
        total_pages = 1  # Un seul tableau = une seule page
        
        # Prendre seulement les 40 premières lignes (ignorer le reste)
        page_rows = all_table_rows[:lines_per_page]
        
        # Construire l'en-tête de la page (une seule fois)
        header_elements = self._build_job_assignment_page_header(
            inventory, job, session_nom, counting, warehouse_info, account_info, 1, total_pages
        )
        
        # Construire un SEUL tableau avec exactement 40 lignes (ou moins si moins de lignes disponibles)
        table_elements = self._build_job_assignment_table_from_rows(page_rows, counting, 1, total_pages)
        
        # Garder l'en-tête et le tableau ensemble sur une seule page
        all_elements = header_elements + table_elements
        elements.append(KeepTogether(all_elements))
        
        return elements
    
    def _prepare_job_assignment_table_rows(self, counting_details, counting):
        """
        Prépare toutes les lignes du tableau pour l'API job assignment
        Utilise CountingDetail comme source de données
        """
        rows = []
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article - une ligne par CountingDetail
            for counting_detail in counting_details:
                location = counting_detail.location
                product = counting_detail.product
                quantity = counting_detail.quantity_inventoried
                
                row = {
                    'location': location.location_reference,
                    'internal_product_code': product.Internal_Product_Code if product and product.Internal_Product_Code else '-',
                    'barcode': product.Barcode if product and product.Barcode else '-',
                    'designation': product.Short_Description if product else '-',
                    'quantite_physique': quantity,
                    'quantite_theorique': '-',  # Pas de quantite theorique dans CountingDetail
                }
                # Ajouter DLC seulement si le comptage le supporte ET si le produit supporte DLC
                # Passer counting_details pour verification stricte
                if self._should_show_dlc(counting, counting_details):
                    row['dlc'] = counting_detail.dlc.strftime('%d/%m/%Y') if counting_detail.dlc else '-'
                # Ajouter n_lot seulement si le comptage le supporte
                if counting.n_lot:
                    row['n_lot'] = counting_detail.n_lot if counting_detail.n_lot else '-'
                rows.append(row)
        else:
            # Mode vrac - grouper par location et sommer les quantites
            location_quantities = {}
            for counting_detail in counting_details:
                location_ref = counting_detail.location.location_reference
                quantity = counting_detail.quantity_inventoried
                
                if location_ref in location_quantities:
                    location_quantities[location_ref] += quantity
                else:
                    location_quantities[location_ref] = quantity
            
            # Creer une ligne par location
            for location_ref, total_quantity in location_quantities.items():
                row = {
                    'location': location_ref,
                    'quantite_physique': total_quantity,
                    'quantite_theorique': '-',  # Pas de quantite theorique dans CountingDetail
                }
                rows.append(row)
        
        return rows
    
    def _build_job_assignment_page_header(self, inventory, job, session_nom, counting, warehouse_info, account_info, page_num, total_pages):
        """
        Construit l'en-tête de page pour l'API job assignment
        Logique spécifique à l'API jobs/<int:job_id>/assignments/<int:assignment_id>/pdf/
        """
        elements = []
        styles = getSampleStyleSheet()
        
        # Ajouter un espace en haut de la page
        elements.append(Spacer(1, 0.5*cm))
        
        # Style pour les labels (en gras) - aligné à gauche
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=0,  # Left
        )
        
        # Style pour les labels alignés à droite
        label_style_right = ParagraphStyle(
            'LabelStyleRight',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=2,  # Right
        )
        
        # Informations sur une seule ligne: Ordre de comptage à gauche | Équipe affectée à droite
        info_row_data = [
            Paragraph(f"<b>comptage :</b> {counting.order}", label_style),
            Paragraph(f"<b>Équipe :</b> {session_nom if session_nom else 'Non affecté'}", label_style_right),
        ]
        
        info_table = Table([info_row_data], colWidths=[8*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Première colonne à gauche
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Deuxième colonne à droite
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(info_table)
        # Ajouter un espace entre les informations et le tableau
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_job_assignment_table_from_rows(self, rows, counting, page_num, total_pages):
        """
        Construit le tableau pour l'API job assignment
        Logique spécifique à l'API jobs/<int:job_id>/assignments/<int:assignment_id>/pdf/
        """
        elements = []
        styles = getSampleStyleSheet()
        
        # Style pour la désignation avec retour à la ligne automatique
        designation_style = ParagraphStyle(
            'DesignationStyle',
            parent=styles['Normal'],
            fontSize=6,  # Réduit encore plus pour économiser l'espace
            textColor=colors.black,
            alignment=0,  # Left align
            leading=7,  # Réduit pour économiser l'espace vertical
            spaceBefore=0,
            spaceAfter=0,
            wordWrap='CJK',  # Permet le retour à la ligne automatique
        )
        
        # Déterminer si on affiche la quantité théorique
        show_theorique = counting.quantity_show or counting.stock_situation
        
        # Déterminer si on affiche DLC en utilisant la méthode helper
        # Vérifier dans les rows si au moins un produit a DLC activé
        has_product_with_dlc = False
        if rows and len(rows) > 0:
            for row in rows:
                if 'dlc' in row:
                    has_product_with_dlc = True
                    break
        
        # Si aucun produit n'a DLC dans les rows, ne pas afficher la colonne
        show_dlc = self._should_show_dlc(counting) if has_product_with_dlc else False
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article - toujours afficher Article et Désignation pour le PDF
            headers.append('Article')  # Internal_Product_Code
            headers.append('CAB')  # Barcode
            headers.append('Désignation')
            headers.append('QTE')  # Toujours présent
            
            if show_theorique:
                headers.append('QTE théorique')
            
            # Colonnes optionnelles - Ne pas afficher DLC si show_dlc est False
            if show_dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
        else:
            # Mode vrac
            headers.append('QTE')  # Toujours présent
            
            if show_theorique:
                headers.append('QTE théorique')
        
        # Trouver l'index de la colonne Désignation
        designation_index = headers.index('Désignation') if 'Désignation' in headers else None
        
        # Construire les données
        data = [headers]
        
        for row in rows:
            table_row = [row['location']]
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article - toujours afficher Article et Désignation pour le PDF
                # Article (Internal_Product_Code)
                table_row.append(row.get('internal_product_code', '-'))
                # Code à barre (Barcode)
                table_row.append(row.get('barcode', '-'))
                # Désignation - utiliser Paragraph pour permettre le retour à la ligne
                designation_text = row.get('designation', '-')
                # Échapper les caractères spéciaux pour XML/HTML
                designation_text = str(designation_text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                table_row.append(Paragraph(designation_text, designation_style))
                
                # Quantité (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
                
                # Colonnes optionnelles - ajouter seulement si show_dlc est True
                if show_dlc:
                    # DLC est déjà formatée comme date ou '-' dans _prepare_job_assignment_table_rows
                    dlc_value = row.get('dlc', '-')
                    # Convertir False en '-' pour éviter d'afficher "False"
                    if dlc_value is False or dlc_value == False or str(dlc_value).lower() == 'false':
                        dlc_value = '-'
                    table_row.append(str(dlc_value) if dlc_value else '-')
                if counting.n_lot:
                    table_row.append(row.get('n_lot', '-'))
            else:
                # Mode vrac
                # Quantité (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
            
            data.append(table_row)
        
        if len(data) == 1:  # Seulement les headers
            return elements
        
        # Créer le tableau - pas de répétition de l'en-tête (repeatRows=0)
        # Permettre la division du tableau si nécessaire (splitByRow=1)
        # Aligner le tableau avec le pied de page (mêmes marges que le footer des deux côtés)
        footer_margin = 0.5*cm  # Marge du footer (identique à celle utilisée dans le footer)
        document_left_margin = 0.1*cm  # leftMargin du document
        document_right_margin = 0.1*cm  # rightMargin du document
        # Footer commence à: doc.leftMargin + footer_margin = 0.1 + 0.5 = 0.6cm
        # Footer se termine à: A4[0] - doc.rightMargin - footer_margin = 21.0 - 0.1 - 0.5 = 20.4cm
        # Tableau doit avoir exactement les mêmes marges que le footer
        # Largeur totale disponible dans le document = A4[0] - document_left_margin - document_right_margin
        # = 21.0 - 0.1 - 0.1 = 20.8cm
        # Pour avoir les mêmes marges que le footer, on doit ajouter 0.5cm à gauche et 0.5cm à droite
        # Largeur disponible pour le tableau de données = 20.8 - 0.5 - 0.5 = 19.8cm
        footer_margin = 0.5*cm
        document_left_margin = 0.1*cm
        document_right_margin = 0.1*cm
        total_document_width = A4[0] - document_left_margin - document_right_margin  # 20.8cm
        available_table_width = total_document_width - footer_margin - footer_margin  # 19.8cm
        col_widths = self._calculate_merged_column_widths(headers, available_table_width, margins=0*cm)
        
        # Style du tableau
        table_style = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Augmenter la taille de l'en-tête
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),  # Réduit pour économiser l'espace
            ('TOPPADDING', (0, 0), (-1, 0), 3),  # Réduit pour économiser l'espace
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Centrer verticalement l'en-tête
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),  # Mettre en gras
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Augmenter la taille
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),  # Toutes les valeurs centrées horizontalement
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # Centrer verticalement le corps
        ]
        
        # Aligner la colonne Désignation au centre si elle existe
        if designation_index is not None:
            table_style.append(('ALIGN', (designation_index, 1), (designation_index, -1), 'CENTER'))  # Centrer aussi la désignation
        
        # Ajouter les lignes de séparation entre toutes les colonnes
        # Padding modéré pour augmenter la hauteur et la largeur sans dépasser la page
        table_style.extend([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Ligne plus épaisse sous l'en-tête
            ('TOPPADDING', (0, 1), (-1, -1), 1.5),  # Réduit pour économiser l'espace
            ('BOTTOMPADDING', (0, 1), (-1, -1), 1.5),  # Réduit pour économiser l'espace
            ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Réduit pour augmenter la largeur du tableau
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Réduit pour augmenter la largeur du tableau
        ])
        
        # Ajuster le padding de la colonne Désignation pour mieux gérer les retours à la ligne
        if designation_index is not None:
            table_style.append(('TOPPADDING', (designation_index, 1), (designation_index, -1), 1.5))
            table_style.append(('BOTTOMPADDING', (designation_index, 1), (designation_index, -1), 1.5))
        
        # Ajouter des colonnes vides au début et à la fin pour créer les marges identiques au footer
        # Le footer a les mêmes marges des deux côtés: doc.leftMargin + footer_margin = 0.6cm
        # et doc.rightMargin + footer_margin = 0.6cm
        footer_margin = 0.5*cm
        document_left_margin = 0.1*cm
        document_right_margin = 0.1*cm
        # Le spacer gauche doit compenser la différence entre la marge du footer et la marge du document
        # Footer position gauche: 0.6cm, Document margin: 0.1cm, donc spacer = 0.5cm
        left_spacer = footer_margin  # 0.5cm pour arriver à 0.6cm total (0.1 + 0.5)
        # Le spacer droit doit être identique au spacer gauche pour avoir les mêmes marges
        right_spacer = footer_margin  # 0.5cm pour arriver à 0.6cm total (0.1 + 0.5)
        
        # Ajouter une colonne vide au début et à la fin de chaque ligne pour créer les marges
        extended_data = []
        for row in data:
            extended_row = [''] + list(row) + ['']
            extended_data.append(extended_row)
        
        # Créer les largeurs de colonnes avec les spacers
        # Vérifier que la somme des largeurs correspond à la largeur disponible dans le document
        extended_col_widths = [left_spacer] + col_widths + [right_spacer]
        total_width = sum(extended_col_widths)
        expected_width = A4[0] - document_left_margin - document_right_margin  # 20.8cm
        
        # Ajuster si nécessaire pour s'assurer que le tableau occupe toute la largeur disponible
        # IMPORTANT: Garder les marges gauche et droite IDENTIQUES en ajustant les colonnes de données
        if abs(total_width - expected_width) > 0.01*cm:
            width_diff = expected_width - total_width
            # Ajuster les colonnes de données proportionnellement pour garder les marges identiques
            if sum(col_widths) > 0:
                ratio = (sum(col_widths) + width_diff) / sum(col_widths)
                col_widths = [w * ratio for w in col_widths]
                # Recalculer avec les nouvelles largeurs, en gardant les marges identiques
                extended_col_widths = [left_spacer] + col_widths + [right_spacer]
        
        # Créer le tableau étendu avec les marges
        extended_table = Table(extended_data, colWidths=extended_col_widths, repeatRows=0, splitByRow=1)
        
        # Créer un nouveau style pour le tableau étendu
        # Les colonnes de données sont maintenant aux indices 1 à -2 (colonne 0 et -1 sont vides)
        extended_table_style = []
        
        # Appliquer le style original aux colonnes de données seulement (1 à -2)
        # En-tête
        extended_table_style.extend([
            ('BACKGROUND', (1, 0), (-2, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (1, 0), (-2, 0), colors.black),
            ('ALIGN', (1, 0), (-2, 0), 'CENTER'),
            ('FONTNAME', (1, 0), (-2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (-2, 0), 9),
            ('BOTTOMPADDING', (1, 0), (-2, 0), 3),
            ('TOPPADDING', (1, 0), (-2, 0), 3),
            ('VALIGN', (1, 0), (-2, 0), 'MIDDLE'),
        ])
        
        # Corps
        extended_table_style.extend([
            ('BACKGROUND', (1, 1), (-2, -1), colors.white),
            ('TEXTCOLOR', (1, 1), (-2, -1), colors.black),
            ('FONTNAME', (1, 1), (-2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (-2, -1), 8),
            ('ALIGN', (1, 1), (-2, -1), 'CENTER'),
            ('VALIGN', (1, 1), (-2, -1), 'MIDDLE'),
        ])
        
        # Aligner la colonne Désignation au centre si elle existe (décaler l'index de +1)
        if designation_index is not None:
            extended_table_style.append(('ALIGN', (designation_index + 1, 1), (designation_index + 1, -1), 'CENTER'))
        
        # Ajouter les lignes de séparation et le padding
        extended_table_style.extend([
            ('GRID', (1, 0), (-2, -1), 0.5, colors.black),
            ('LINEBELOW', (1, 0), (-2, 0), 1, colors.black),
            ('TOPPADDING', (1, 1), (-2, -1), 1.5),
            ('BOTTOMPADDING', (1, 1), (-2, -1), 1.5),
            ('LEFTPADDING', (1, 0), (-2, -1), 2),
            ('RIGHTPADDING', (1, 0), (-2, -1), 2),
        ])
        
        # Ajuster le padding de la colonne Désignation
        if designation_index is not None:
            extended_table_style.append(('TOPPADDING', (designation_index + 1, 1), (designation_index + 1, -1), 1.5))
            extended_table_style.append(('BOTTOMPADDING', (designation_index + 1, 1), (designation_index + 1, -1), 1.5))
        
        # Style pour les colonnes vides (première et dernière) - les rendre complètement invisibles
        extended_table_style.extend([
            ('BACKGROUND', (0, 0), (0, -1), colors.white),  # Colonne gauche vide
            ('BACKGROUND', (-1, 0), (-1, -1), colors.white),  # Colonne droite vide
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),  # Texte blanc (invisible)
            ('TEXTCOLOR', (-1, 0), (-1, -1), colors.white),  # Texte blanc (invisible)
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 0),
            ('LEFTPADDING', (-1, 0), (-1, -1), 0),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (0, -1), 0),
            ('BOTTOMPADDING', (0, 0), (0, -1), 0),
            ('TOPPADDING', (-1, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (-1, 0), (-1, -1), 0),
            # Masquer toutes les bordures des colonnes vides
            ('LINELEFT', (0, 0), (0, -1), 0, colors.white),
            ('LINERIGHT', (0, 0), (0, -1), 0, colors.white),
            ('LINETOP', (0, 0), (0, 0), 0, colors.white),
            ('LINEBOTTOM', (0, -1), (0, -1), 0, colors.white),
            ('LINELEFT', (-1, 0), (-1, -1), 0, colors.white),
            ('LINERIGHT', (-1, 0), (-1, -1), 0, colors.white),
            ('LINETOP', (-1, 0), (-1, 0), 0, colors.white),
            ('LINEBOTTOM', (-1, -1), (-1, -1), 0, colors.white),
        ])
        
        extended_table.setStyle(TableStyle(extended_table_style))
        
        elements.append(extended_table)
        
        # Pas de pagination ici, elle sera dans le footer fixe
        return elements

