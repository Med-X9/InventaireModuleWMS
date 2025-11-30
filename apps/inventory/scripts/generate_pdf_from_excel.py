"""
Script Python standalone pour générer un PDF des jobs d'inventaire depuis un fichier Excel
Utilise la même configuration que l'API inventory-jobs-pdf

Usage:
    python manage.py shell
    >>> exec(open('apps/inventory/scripts/generate_pdf_from_excel.py').read())
    >>> generate_pdf_from_excel('chemin/vers/fichier.xlsx', 'chemin/sortie.pdf')
    
    ou directement:
    python apps/inventory/scripts/generate_pdf_from_excel.py chemin/vers/fichier.xlsx [chemin/sortie.pdf]
"""
import os
import sys

# Configuration Django - à adapter selon votre structure de projet
if __name__ == "__main__":
    # Trouver le répertoire du projet (remonte de scripts/ vers la racine)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Configurer Django - REMPLACEZ 'your_project' par le nom réel de votre projet Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    import django
    django.setup()

import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
import logging
import time
import errno

logger = logging.getLogger(__name__)


def calculate_column_widths(headers, available_width):
    """Calcule la largeur des colonnes"""
    fixed_widths = {
        'Emplacement': 0.15,
        'Article': 0.10,
        'CAB': 0.13,
        'QTE': 0.08,
        'Désignation': 0.40,
        'quantite_physique': 0.08,
        'QTE théorique': 0.10,
    }
    
    widths = []
    used_percentage = 0
    
    for header in headers:
        if header in fixed_widths:
            widths.append(available_width * fixed_widths[header])
            used_percentage += fixed_widths[header]
        else:
            widths.append(None)
    
    remaining_percentage = 1.0 - used_percentage
    variable_headers_count = sum(1 for w in widths if w is None)
    
    if variable_headers_count > 0:
        width_per_variable = remaining_percentage / variable_headers_count
        widths = [w if w is not None else available_width * width_per_variable for w in widths]
    
    return widths


def build_pages_from_excel_data(job_ref, rows, inventory_info):
    """Construit les pages pour un job depuis les données Excel"""
    elements = []
    
    if not rows:
        return elements
    
    # Limiter à 40 lignes
    all_table_rows = rows[:40]
    
    if not all_table_rows:
        return elements
    
    # Construire les en-têtes
    headers = ['Emplacement', 'Article', 'CAB', 'Désignation', 'QTE']
    
    # Vérifier les colonnes optionnelles
    has_qte_theorique = any(row.get('qte_theorique') for row in all_table_rows if row.get('qte_theorique'))
    if has_qte_theorique:
        headers.append('QTE théorique')
    
    has_dlc = any(row.get('dlc') for row in all_table_rows if row.get('dlc'))
    if has_dlc:
        headers.append('DLC')
    
    has_n_lot = any(row.get('n_lot') for row in all_table_rows if row.get('n_lot'))
    if has_n_lot:
        headers.append('N° Lot')
    
    # Style pour la désignation
    styles = getSampleStyleSheet()
    designation_style = ParagraphStyle(
        'DesignationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=0,
        leading=8,
        spaceBefore=0,
        spaceAfter=0,
        wordWrap='CJK',
        fontName='Arial',
    )
    
    # Construire les données du tableau
    data = [headers]
    designation_col_idx = headers.index('Désignation') if 'Désignation' in headers else -1
    
    for row in all_table_rows:
        row_data = [
            row.get('location', '-'),
            row.get('article', '-'),
            row.get('cab', '-'),
            row.get('designation', '-'),
            row.get('qte', '-'),
        ]
        
        if has_qte_theorique:
            row_data.append(row.get('qte_theorique', '-'))
        
        if has_dlc:
            row_data.append(row.get('dlc', '-'))
        
        if has_n_lot:
            row_data.append(row.get('n_lot', '-'))
        
        # Appliquer le style Paragraph à la colonne Désignation
        if designation_col_idx >= 0:
            cell_value = row_data[designation_col_idx]
            if cell_value and cell_value != '-':
                row_data[designation_col_idx] = Paragraph(str(cell_value), designation_style)
        
        data.append(row_data)
    
    # Créer le tableau
    document_margins = 0.1*cm + 0.1*cm
    margin_reduction = (0.2*cm - 0.1*cm) * 2
    available_table_width = A4[0] - document_margins + margin_reduction
    col_widths = calculate_column_widths(headers, available_table_width)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Style du tableau
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]
    
    table.setStyle(TableStyle(table_style))
    
    elements.append(KeepTogether([Spacer(0.2*cm, 0.2*cm), table]))
    
    return elements


def add_page_header_and_footer(canvas_obj, doc):
    """Ajoute le header et footer (même configuration que inventory-jobs-pdf)"""
    canvas_obj.saveState()
    
    # Titre centré
    inventory_info = getattr(doc, 'inventory_info', {})
    page_num = canvas_obj.getPageNumber()
    page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
    job_reference = page_info.get('job_ref', inventory_info.get('job_reference', '-'))
    
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.setFillColor(colors.black)
    
    title_text = f"FICHE DE COMPTAGE : {job_reference}"
    title_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 12)
    x_title = (doc.pagesize[0] - title_width) / 2
    y_header = doc.pagesize[1] - doc.topMargin - 0.5*cm
    canvas_obj.drawString(x_title, y_header, title_text)
    
    # Footer centré
    if inventory_info:
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        
        footer_y = 1*cm
        
        reference = inventory_info.get('reference', '-')
        account = inventory_info.get('account_name', '-')
        warehouse = inventory_info.get('warehouse_name', '-')
        
        footer_parts = [f"Réf. Inventaire: {reference}", f"Compte: {account}", f"Magasin: {warehouse}"]
        footer_text = "-".join(footer_parts)
        
        footer_width = canvas_obj.stringWidth(footer_text, "Helvetica", 8)
        footer_x = (doc.pagesize[0] - footer_width) / 2
        canvas_obj.drawString(footer_x, footer_y, footer_text)
        
        # Labels de dates
        date_line_y = 2.8*cm
        signature_margin = 0.5*cm
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.black)
        
        date_debut_x = doc.leftMargin + signature_margin
        canvas_obj.drawString(date_debut_x, date_line_y, "Date début:")
        
        label_text_fin = "Date fin :"
        label_fin_width = canvas_obj.stringWidth(label_text_fin, "Helvetica", 10)
        space_for_manual_entry = 4*cm
        date_fin_label_x = doc.pagesize[0] - doc.rightMargin - label_fin_width - signature_margin - space_for_manual_entry
        canvas_obj.drawString(date_fin_label_x, date_line_y, label_text_fin)
    
    # Pagination à droite
    page_num = canvas_obj.getPageNumber()
    page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
    
    if page_info:
        current = page_info.get('current', 1)
        total = page_info.get('total', 1)
        
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        
        text = f"Page {current}/{total}"
        text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
        footer_margin = 0.5*cm
        x = doc.pagesize[0] - doc.rightMargin - text_width - footer_margin
        y = 0.5*cm
        canvas_obj.drawString(x, y, text)
    
    # Signatures
    personne_info = getattr(doc, 'personne_info', {})
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.setFillColor(colors.black)
    text_y = 2*cm
    
    signature_margin = 0.5*cm
    x1 = doc.leftMargin + signature_margin
    canvas_obj.drawString(x1, text_y, "Signature L'Oréal :")
    
    canvas_obj.setFont("Helvetica", 10)
    label_text_agl = "Signature AGL :"
    space_for_manual_entry = 4*cm
    label_width = canvas_obj.stringWidth(label_text_agl, "Helvetica", 10)
    x2 = doc.pagesize[0] - doc.rightMargin - label_width - signature_margin - space_for_manual_entry
    canvas_obj.drawString(x2, text_y, label_text_agl)
    
    canvas_obj.restoreState()


def generate_pdf_from_excel(excel_file_path: str, output_pdf_path: str = None) -> str:
    """
    Génère un PDF des jobs d'inventaire depuis un fichier Excel
    
    Args:
        excel_file_path: Chemin vers le fichier Excel
        output_pdf_path: Chemin de sortie pour le PDF (optionnel)
        
    Returns:
        str: Chemin du fichier PDF généré
    """
    try:
        # Vérifier que le fichier Excel existe
        if not os.path.exists(excel_file_path):
            raise FileNotFoundError(f"Le fichier Excel n'existe pas: {excel_file_path}")
        
        if not excel_file_path.endswith(('.xlsx', '.xls')):
            raise ValueError(f"Le fichier doit être au format Excel (.xlsx ou .xls)")
        
        # Déterminer le chemin de sortie
        if output_pdf_path is None:
            base_name = os.path.splitext(excel_file_path)[0]
            output_pdf_path = f"{base_name}.pdf"
        
        logger.info(f"Début de la génération du PDF depuis: {excel_file_path}")
        
        # Vérifier que le fichier n'est pas verrouillé avant de le lire
        max_retries = 3
        retry_delay = 1  # secondes
        
        for attempt in range(max_retries):
            try:
                # Tenter d'ouvrir le fichier en mode lecture pour vérifier s'il est verrouillé
                with open(excel_file_path, 'rb') as test_file:
                    pass  # Si on peut ouvrir le fichier, il n'est pas verrouillé
                break  # Sortir de la boucle si le fichier est accessible
            except (IOError, OSError) as e:
                if e.errno == errno.EBUSY or e.errno == errno.EACCES:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Fichier verrouillé (tentative {attempt + 1}/{max_retries}). "
                            f"Attente de {retry_delay} seconde(s)..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Augmenter le délai à chaque tentative
                    else:
                        raise IOError(
                            f"Le fichier Excel est verrouillé ou utilisé par un autre programme: {excel_file_path}\n"
                            f"Veuillez fermer le fichier dans Excel ou tout autre programme qui l'utilise."
                        )
                else:
                    raise
        
        # Lire le fichier Excel
        try:
            df = pd.read_excel(excel_file_path, engine='openpyxl')
        except ImportError:
            raise ImportError("openpyxl est requis. Installez-le avec: pip install openpyxl")
        except PermissionError as e:
            raise PermissionError(
                f"Permission refusée lors de la lecture du fichier Excel: {excel_file_path}\n"
                f"Le fichier est peut-être ouvert dans Excel ou un autre programme. "
                f"Veuillez le fermer et réessayer."
            )
        except Exception as e:
            error_msg = str(e)
            if "EBUSY" in error_msg or "resource busy" in error_msg.lower() or "locked" in error_msg.lower():
                raise IOError(
                    f"Le fichier Excel est verrouillé: {excel_file_path}\n"
                    f"Veuillez fermer le fichier dans Excel ou tout autre programme qui l'utilise."
                )
            raise ValueError(f"Erreur lors de la lecture du fichier Excel: {error_msg}")
        
        if df.empty:
            raise ValueError("Le fichier Excel est vide")
        
        # Valider les colonnes requises
        required_columns = ['Job', 'Emplacement', 'Article', 'CAB', 'Désignation', 'QTE']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colonnes manquantes: {', '.join(missing_columns)}")
        
        # Récupérer les informations de l'inventaire
        inventory_info = {
            'reference': df.get('Réf. Inventaire', pd.Series(['-']))[0] if 'Réf. Inventaire' in df.columns else '-',
            'account_name': df.get('Compte', pd.Series(['-']))[0] if 'Compte' in df.columns else '-',
            'warehouse_name': df.get('Magasin', pd.Series(['-']))[0] if 'Magasin' in df.columns else '-',
            'date': df.get('Date', pd.Series(['-']))[0] if 'Date' in df.columns else '-',
        }
        
        # Convertir la date
        if hasattr(inventory_info['date'], 'strftime'):
            inventory_info['date'] = inventory_info['date'].strftime('%d/%m/%Y')
        elif pd.notna(inventory_info['date']):
            inventory_info['date'] = str(inventory_info['date'])
        else:
            inventory_info['date'] = '-'
        
        # Grouper les données par Job
        jobs_data = {}
        for _, row in df.iterrows():
            job_ref = str(row['Job']).strip() if pd.notna(row['Job']) else '-'
            if job_ref not in jobs_data:
                jobs_data[job_ref] = []
            
            data_row = {
                'location': str(row['Emplacement']).strip() if pd.notna(row['Emplacement']) else '-',
                'article': str(row['Article']).strip() if pd.notna(row['Article']) else '-',
                'cab': str(row['CAB']).strip() if pd.notna(row['CAB']) else '-',
                'designation': str(row['Désignation']).strip() if pd.notna(row['Désignation']) else '-',
                'qte': str(row['QTE']).strip() if pd.notna(row['QTE']) else '-',
                'qte_theorique': str(row.get('QTE théorique', '-')).strip() if pd.notna(row.get('QTE théorique', None)) else None,
                'dlc': str(row.get('DLC', '-')).strip() if pd.notna(row.get('DLC', None)) else None,
                'n_lot': str(row.get('N° Lot', '-')).strip() if pd.notna(row.get('N° Lot', None)) else None,
            }
            jobs_data[job_ref].append(data_row)
        
        if not jobs_data:
            raise ValueError("Aucune donnée valide trouvée dans le fichier Excel")
        
        # Calculer la pagination
        page_info_map = {}
        page_counter = 0
        for job_ref in jobs_data.keys():
            page_counter += 1
            page_info_map[page_counter] = {
                'current': 1,
                'total': 1,
                'job_ref': job_ref
            }
        
        # Créer le buffer PDF
        buffer = BytesIO()
        story = []
        
        # Construire les pages pour chaque job
        for job_ref, rows in jobs_data.items():
            job_pages = build_pages_from_excel_data(job_ref, rows, inventory_info)
            if job_pages:
                story.extend(job_pages)
        
        if not story:
            raise ValueError("Aucun contenu à générer")
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.1*cm,
            leftMargin=0.1*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )
        
        doc.page_info_map = page_info_map
        doc.inventory_info = {
            'reference': inventory_info['reference'],
            'account_name': inventory_info['account_name'],
            'warehouse_name': inventory_info['warehouse_name'],
            'inventory_type': '-',
            'date': inventory_info['date'],
            'date_debut': None,
            'date_fin': None,
            'job_reference': '-'
        }
        doc.personne_info = {
            'personne': None,
            'personne_nom': None,
            'personne_two': None,
            'personne_two_nom': None
        }
        
        # Construire le PDF
        doc.build(story, 
                 onFirstPage=add_page_header_and_footer, 
                 onLaterPages=add_page_header_and_footer)
        
        # Écrire le PDF avec gestion des erreurs de verrouillage
        buffer.seek(0)
        max_write_retries = 3
        write_retry_delay = 1
        
        for attempt in range(max_write_retries):
            try:
                with open(output_pdf_path, 'wb') as output_file:
                    output_file.write(buffer.getvalue())
                break  # Succès, sortir de la boucle
            except (IOError, OSError) as e:
                if (e.errno == errno.EBUSY or e.errno == errno.EACCES) and attempt < max_write_retries - 1:
                    logger.warning(
                        f"Impossible d'écrire le PDF (tentative {attempt + 1}/{max_write_retries}). "
                        f"Le fichier de sortie est peut-être verrouillé. Attente de {write_retry_delay} seconde(s)..."
                    )
                    time.sleep(write_retry_delay)
                    write_retry_delay *= 2
                else:
                    if e.errno == errno.EBUSY or e.errno == errno.EACCES:
                        raise IOError(
                            f"Impossible d'écrire le fichier PDF: {output_pdf_path}\n"
                            f"Le fichier est peut-être ouvert dans un autre programme. "
                            f"Veuillez le fermer et réessayer."
                        )
                    else:
                        raise
        
        logger.info(f"PDF généré avec succès: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        logger.error(f"Erreur: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_from_excel.py <chemin_fichier_excel> [chemin_sortie_pdf]")
        print("\nFormat attendu du fichier Excel:")
        print("Colonnes requises: 'Job', 'Emplacement', 'Article', 'CAB', 'Désignation', 'QTE'")
        print("Colonnes optionnelles: 'QTE théorique', 'DLC', 'N° Lot'")
        print("Colonnes pour les infos inventaire: 'Réf. Inventaire', 'Compte', 'Magasin', 'Date'")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    output_pdf_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result_path = generate_pdf_from_excel(excel_file_path, output_pdf_path)
        print(f"✓ PDF généré avec succès: {result_path}")
    except Exception as e:
        print(f"✗ Erreur: {str(e)}")
        sys.exit(1)
