"""
Commande Django pour préparer un fichier Excel "image de stock" à importer dans la table Stock.

Combine deux fichiers Excel :
  - Fichier emplacements : colonne "emplacement" (ex. inventory_location_job_test_fixed_corrige.xlsx)
  - Fichier articles : colonne "code article" ou "internal product code" (ex. Product-2026-03-15.xlsx)

Produit un fichier avec les colonnes attendues par l'API d'import stock : article, emplacement, quantite.

Exemple d'utilisation :
    # Mode 1-à-1 (défaut) : ligne i emplacements avec ligne i articles
    python manage.py prepare_stock_image_excel --locations inventory_location_job_test_fixed_corrige.xlsx --products Product-2026-03-15.xlsx --output image_stock_import.xlsx

    # Mode cartésien (toutes combinaisons) avec limite de lignes
    python manage.py prepare_stock_image_excel --locations fichier_locations.xlsx --products fichier_articles.xlsx --output image_stock.xlsx --cartesian --max-rows 50000 --default-qte 0
"""
import pandas as pd
from django.core.management.base import BaseCommand, CommandError


# Colonnes requises pour l'import stock (API StockImportView / stock_service)
OUTPUT_COLUMNS = ['article', 'emplacement', 'quantite']

# Noms de colonnes possibles pour les articles (premier trouvé utilisé)
ARTICLE_COLUMN_ALIASES = ['code article', 'internal product code', 'article', 'product code', 'reference']

# Nom de colonne pour l'emplacement
LOCATION_COLUMN_ALIASES = ['emplacement', 'location', 'location_reference', 'emplacement_reference']


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les noms de colonnes en minuscules et strip."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df


def get_article_column(df: pd.DataFrame) -> str:
    """Retourne le nom de la colonne article dans df."""
    cols = set(df.columns)
    for alias in ARTICLE_COLUMN_ALIASES:
        if alias in cols:
            return alias
    raise ValueError(
        f"Aucune colonne 'code article' trouvée. Colonnes attendues (ou similaires) : {ARTICLE_COLUMN_ALIASES}. "
        f"Colonnes trouvées : {list(df.columns)}."
    )


def get_location_column(df: pd.DataFrame) -> str:
    """Retourne le nom de la colonne emplacement dans df."""
    cols = set(df.columns)
    for alias in LOCATION_COLUMN_ALIASES:
        if alias in cols:
            return alias
    raise ValueError(
        f"Aucune colonne 'emplacement' trouvée. Colonnes attendues (ou similaires) : {LOCATION_COLUMN_ALIASES}. "
        f"Colonnes trouvées : {list(df.columns)}."
    )


def safe_series(s: pd.Series) -> pd.Series:
    """Supprime les NaN et vides, convertit en string."""
    out = s.astype(str).str.strip()
    out = out.replace('', pd.NA).replace('nan', pd.NA).replace('None', pd.NA)
    return out.dropna()


class Command(BaseCommand):
    help = (
        "Prépare un fichier Excel image de stock (colonnes article, emplacement, quantite) "
        "à partir d'un fichier emplacements et d'un fichier articles."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--locations',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel des emplacements (doit contenir une colonne "emplacement").',
        )
        parser.add_argument(
            '--products',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel des articles (doit contenir "code article" ou "internal product code").',
        )
        parser.add_argument(
            '--output',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel de sortie (.xlsx).',
        )
        parser.add_argument(
            '--default-qte',
            type=int,
            default=0,
            help='Quantité par défaut pour chaque ligne (défaut: 0).',
        )
        parser.add_argument(
            '--cartesian',
            action='store_true',
            help='Produire toutes les combinaisons article × emplacement (attention: peut être très volumineux).',
        )
        parser.add_argument(
            '--max-rows',
            type=int,
            default=None,
            help='Limiter le nombre de lignes en mode cartesian (ex: 50000). Ignoré en mode 1-à-1.',
        )

    def handle(self, *args, **options):
        locations_path = options['locations']
        products_path = options['products']
        output_path = options['output']
        default_qte = options['default_qte']
        use_cartesian = options['cartesian']
        max_rows = options['max_rows']

        if default_qte < 0:
            raise CommandError('--default-qte doit être >= 0.')

        self.stdout.write(
            self.style.SUCCESS(
                f"Préparation de l'image de stock : locations={locations_path}, products={products_path}"
            )
        )

        try:
            df_locations = pd.read_excel(locations_path, engine='openpyxl')
        except Exception as e:
            raise CommandError(f"Impossible de lire le fichier emplacements : {e}")

        try:
            df_products = pd.read_excel(products_path, engine='openpyxl')
        except Exception as e:
            raise CommandError(f"Impossible de lire le fichier articles : {e}")

        df_locations = normalize_columns(df_locations)
        df_products = normalize_columns(df_products)

        try:
            loc_col = get_location_column(df_locations)
        except ValueError as e:
            raise CommandError(str(e))

        try:
            art_col = get_article_column(df_products)
        except ValueError as e:
            raise CommandError(str(e))

        if use_cartesian:
            locations = safe_series(df_locations[loc_col]).unique().tolist()
            articles = safe_series(df_products[art_col]).unique().tolist()
            if not locations:
                raise CommandError("Aucun emplacement valide trouvé dans le fichier emplacements.")
            if not articles:
                raise CommandError("Aucun article valide trouvé dans le fichier articles.")
            total = len(articles) * len(locations)
            if max_rows is not None and total > max_rows:
                # Limiter : garder un sous-ensemble pour rester sous max_rows
                import math
                n_art = min(len(articles), max(1, int(math.sqrt(max_rows))))
                n_loc = min(len(locations), max(1, max_rows // n_art))
                articles = articles[:n_art]
                locations = locations[:n_loc]
                total = n_art * n_loc
                self.stdout.write(self.style.WARNING(f"Mode cartesian limité à {total} lignes (--max-rows={max_rows})."))
            rows = []
            for art in articles:
                for loc in locations:
                    rows.append({'article': art, 'emplacement': loc, 'quantite': default_qte})
            out_df = pd.DataFrame(rows)
        else:
            # Association 1 à 1 : ligne i du fichier emplacements avec ligne i du fichier articles
            n_loc = len(df_locations)
            n_art = len(df_products)
            n = min(n_loc, n_art)
            if n_loc != n_art:
                self.stdout.write(
                    self.style.WARNING(
                        f"Les deux fichiers n'ont pas le même nombre de lignes (emplacements: {n_loc}, articles: {n_art}). "
                        f"Utilisation des {n} premières lignes communes."
                    )
                )
            out_df = pd.DataFrame({
                'article': df_products[art_col].iloc[:n].astype(str).str.strip(),
                'emplacement': df_locations[loc_col].iloc[:n].astype(str).str.strip(),
                'quantite': default_qte,
            })
            out_df = out_df.replace('nan', '').replace('None', '')
            out_df = out_df[out_df['article'].str.len() > 0]
            out_df = out_df[out_df['emplacement'].str.len() > 0]

        out_df = out_df[OUTPUT_COLUMNS]

        try:
            out_df.to_excel(output_path, index=False, engine='openpyxl')
        except Exception as e:
            raise CommandError(f"Erreur lors de l'écriture du fichier : {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Fichier écrit : {output_path} ({len(out_df)} lignes)")
        )
        if use_cartesian:
            self.stdout.write(f"  Articles uniques : {len(articles)}")
            self.stdout.write(f"  Emplacements uniques : {len(locations)}")
        self.stdout.write(
            self.style.WARNING(
                "Colonnes du fichier : article, emplacement, quantite (compatibles import stock API)."
            )
        )
