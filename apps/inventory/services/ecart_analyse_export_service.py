"""
Service d'export analyse écarts stock théorique (Excel) et PDF recomptage.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Set, Tuple

from apps.inventory.exceptions.inventory_exceptions import InventoryNotFoundError
from apps.inventory.exceptions.warehouse_exceptions import WarehouseNotFoundError
from apps.inventory.models import CountingDetail, Inventory
from apps.inventory.repositories.ecart_stock_theorique_repository import (
    EcartStockTheoriqueRepository,
)
from apps.masterdata.models import Warehouse

logger = logging.getLogger(__name__)


class EcartAnalyseExportService:
    """
    Exports liés à l'analyse magasin (EcartStockTheorique).

    - Excel : toutes les lignes d'analyse (théorique / pratique / écart)
    - PDF : lignes écart ≠ 0 via CountingDetail (job + emplacements inventoriés)
      Colonnes : N° | Job | Emplacement | Désignation | Barcode | |Écart| |
      Positif/Négatif | 3e | 4e | 5e comptage
      Tri décroissant sur |écart| + header magasin
    """

    def __init__(
        self,
        repository: Optional[EcartStockTheoriqueRepository] = None,
    ) -> None:
        self.repository = repository or EcartStockTheoriqueRepository()

    def _get_inventory_and_warehouse(
        self, inventory_id: int, warehouse_id: int
    ) -> Tuple[Inventory, Warehouse]:
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
        except Inventory.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"Inventaire avec l'ID {inventory_id} non trouvé"
            ) from exc
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist as exc:
            raise WarehouseNotFoundError(
                f"Entrepôt avec l'ID {warehouse_id} non trouvé"
            ) from exc
        return inventory, warehouse

    def generate_analyse_excel(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> BytesIO:
        """
        Génère un Excel de toutes les lignes EcartStockTheorique du magasin.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ValueError(
                "pandas est requis pour l'export Excel. "
                "Installez-le avec: pip install pandas"
            ) from exc

        inventory, warehouse = self._get_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        qs = self.repository.get_for_inventory_warehouse(
            inventory_id, warehouse_id
        )
        rows: List[Dict[str, Any]] = []
        for ecart in qs:
            barcode = ""
            if ecart.product_id and ecart.product:
                barcode = ecart.product.Barcode or ""
            if not barcode:
                barcode = ecart.article_cle or ""
            rows.append(
                {
                    "Désignation": ecart.designation or "",
                    "Barcode": barcode,
                    "Qté théorique": ecart.qte_theorique,
                    "Qté inventoriée": ecart.qte_pratique,
                    "Écart": ecart.ecart,
                    "Résultat final": (
                        ecart.resultat_final
                        if ecart.resultat_final is not None
                        else ""
                    ),
                    "Validé": "Oui" if ecart.valide else "Non",
                }
            )

        if not rows:
            raise ValueError(
                f"Aucune donnée d'analyse pour inventaire {inventory.reference} "
                f"/ magasin {warehouse.warehouse_name}"
            )

        df = pd.DataFrame(rows)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Analyse")
        buffer.seek(0)
        logger.info(
            "Export Excel analyse: %s lignes (inv=%s wh=%s)",
            len(rows),
            inventory_id,
            warehouse_id,
        )
        return buffer

    def get_pdf_recount_rows(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Tuple[Warehouse, Inventory, List[Dict[str, Any]]]:
        """
        Lignes PDF : écart ≠ 0, job + emplacements via CountingDetail (pas Stock).

        Colonnes : job, emplacement, designation, barcode,
        ecart_abs, signe (Positif/Négatif),
        comptage_3 / comptage_4 / comptage_5 (vides pour saisie).

        Tri : |écart| décroissant.
        """
        inventory, warehouse = self._get_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        ecarts = list(
            self.repository.get_nonzero_ecarts(inventory_id, warehouse_id)
        )
        if not ecarts:
            raise ValueError(
                "Aucune ligne avec écart à exporter pour ce magasin"
            )

        product_ids: Set[int] = {
            e.product_id for e in ecarts if e.product_id is not None
        }

        # Job + emplacements inventoriés par produit (CountingDetail du magasin)
        placements_by_product: Dict[int, List[Tuple[str, str]]] = {
            pid: [] for pid in product_ids
        }
        if product_ids:
            cd_rows = (
                CountingDetail.objects.filter(
                    job__inventory_id=inventory_id,
                    job__warehouse_id=warehouse_id,
                    product_id__in=product_ids,
                )
                .select_related("location", "job")
                .order_by("job__reference", "location__location_reference", "id")
                .values_list(
                    "product_id",
                    "job__reference",
                    "location_id",
                    "location__location_reference",
                )
                .distinct()
            )
            seen_placement: Dict[int, Set[Tuple[str, int]]] = {
                pid: set() for pid in product_ids
            }
            for product_id, job_ref, location_id, location_ref in cd_rows:
                if product_id is None:
                    continue
                placement_key = ((job_ref or "").strip(), location_id or 0)
                if placement_key in seen_placement.setdefault(product_id, set()):
                    continue
                seen_placement[product_id].add(placement_key)
                placements_by_product.setdefault(product_id, []).append(
                    ((job_ref or "").strip(), (location_ref or "").strip())
                )

        rows: List[Dict[str, Any]] = []
        seen_keys: Set[Tuple[str, str, str, str, int]] = set()

        for ecart in ecarts:
            barcode = ""
            if ecart.product_id and ecart.product:
                barcode = (ecart.product.Barcode or "").strip()
            if not barcode:
                barcode = (ecart.article_cle or "").strip()
            designation = (ecart.designation or "").strip()
            ecart_value = int(ecart.ecart or 0)
            ecart_abs = abs(ecart_value)
            if ecart_value > 0:
                signe = "Positif"
            elif ecart_value < 0:
                signe = "Négatif"
            else:
                continue

            placements = (
                placements_by_product.get(ecart.product_id, [])
                if ecart.product_id
                else []
            )
            if not placements:
                placements = [("", "")]

            for job_reference, emplacement in placements:
                key = (
                    job_reference,
                    emplacement,
                    barcode,
                    designation,
                    ecart_value,
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                rows.append(
                    {
                        "job": job_reference,
                        "emplacement": emplacement,
                        "designation": designation,
                        "barcode": barcode,
                        "ecart": ecart_value,
                        "ecart_abs": ecart_abs,
                        "signe": signe,
                        "comptage_3": "",
                        "comptage_4": "",
                        "comptage_5": "",
                    }
                )

        # Tri décroissant par valeur absolue de l'écart
        rows.sort(
            key=lambda r: (
                -int(r["ecart_abs"]),
                r["job"] or "zzz",
                r["emplacement"] or "zzz",
                r["barcode"] or "",
                r["designation"] or "",
            )
        )
        return warehouse, inventory, rows

    def generate_ecart_pdf(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> BytesIO:
        """
        PDF tableau recomptage des lignes avec écart.
        Header : nom du magasin.
        Colonnes : N° | Job | Emplacement | Désignation | Barcode |
        |Écart| | Positif/Négatif | 3e | 4e | 5e comptage.
        Tri : |écart| décroissant.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        warehouse, inventory, rows = self.get_pdf_recount_rows(
            inventory_id, warehouse_id
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1.0 * cm,
            rightMargin=1.0 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "EcartPdfTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=6,
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            "EcartPdfSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=12,
            alignment=1,
        )

        story = []
        story.append(
            Paragraph(
                f"Magasin : {warehouse.warehouse_name}",
                title_style,
            )
        )
        story.append(
            Paragraph(
                f"Inventaire : {inventory.label} ({inventory.reference}) — "
                f"Lignes avec écart théorique / physique",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 0.4 * cm))

        table_data = [
            [
                "N°",
                "Job",
                "Emplacement",
                "Désignation",
                "Barcode",
                "|Écart|",
                "Positif/Négatif",
                "3e comptage",
                "4e comptage",
                "5e comptage",
            ]
        ]
        cell_style = ParagraphStyle(
            "EcartCell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
        )
        for index, row in enumerate(rows, start=1):
            table_data.append(
                [
                    Paragraph(str(index), cell_style),
                    Paragraph(row.get("job") or "—", cell_style),
                    Paragraph(row["emplacement"] or "—", cell_style),
                    Paragraph(row["designation"] or "—", cell_style),
                    Paragraph(row["barcode"] or "—", cell_style),
                    Paragraph(str(row.get("ecart_abs", "")), cell_style),
                    Paragraph(row.get("signe") or "", cell_style),
                    Paragraph(row.get("comptage_3") or "", cell_style),
                    Paragraph(row.get("comptage_4") or "", cell_style),
                    Paragraph(row.get("comptage_5") or "", cell_style),
                ]
            )

        col_widths = [
            1.2 * cm,
            2.2 * cm,
            2.8 * cm,
            5.4 * cm,
            2.8 * cm,
            1.8 * cm,
            2.4 * cm,
            2.6 * cm,
            2.6 * cm,
            2.6 * cm,
        ]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F2F2F2")],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("ALIGN", (0, 1), (1, -1), "CENTER"),
                    ("ALIGN", (5, 1), (9, -1), "CENTER"),
                ]
            )
        )
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        logger.info(
            "Export PDF écarts: %s lignes (inv=%s wh=%s)",
            len(rows),
            inventory_id,
            warehouse_id,
        )
        return buffer
