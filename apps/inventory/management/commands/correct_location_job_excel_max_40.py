"""
Commande Django pour corriger un fichier Excel d'import InventoryLocationJob :
- Divise les locations par job : chaque job contient au maximum 40 locations.
- Conserve la même logique de nomination que l'API : JOB-0001, JOB-0002, ...
- Respecte les validations de l'API (colonnes, format job, sessions, active=false => job/sessions vides).

Format Excel attendu (colonnes requises) :
  warehouse, emplacement, active, job, session_1, session_2

Exemple d'utilisation :
    python manage.py correct_location_job_excel_max_40 --input fichier.xlsx --output fichier_corrige.xlsx
    python manage.py correct_location_job_excel_max_40 --input fichier.xlsx --output fichier_corrige.xlsx --max-per-job 40
"""
import re
import pandas as pd
from django.core.management.base import BaseCommand, CommandError


# Constantes alignées avec l'API (inventory_location_job_import_service et vue)
REQUIRED_COLUMNS = ['warehouse', 'emplacement', 'active', 'job', 'session_1', 'session_2']
DEFAULT_MAX_LOCATIONS_PER_JOB = 40
JOB_PATTERN = re.compile(r'^JOB-(\d{4})$')


def normalize_boolean(value):
    """Normalise une valeur en booléen (aligné avec _normalize_boolean du service)."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ('', 'none', 'null', 'n/a', 'na', 'false', '0', 'no', 'non', 'n', 'f', 'non actif', 'inactif'):
            return False
        if v in ('true', '1', 'yes', 'oui', 'o', 'y', 't', 'actif', 'active'):
            return True
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def normalize_excel_value(value):
    """Normalise une valeur Excel (NaN, None -> '')."""
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass
    if value is None:
        return ''
    s = str(value).strip()
    if not s or s.lower() in ('nan', 'none', 'null', 'nat', '<na>', 'n/a', 'na'):
        return ''
    return s


class Command(BaseCommand):
    help = (
        'Corrige un fichier Excel d\'import location-job : max N locations par job, '
        'nommage JOB-0001, JOB-0002, ..., validations API respectées.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel à corriger (.xlsx)',
        )
        parser.add_argument(
            '--output',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel de sortie (.xlsx)',
        )
        parser.add_argument(
            '--max-per-job',
            type=int,
            default=DEFAULT_MAX_LOCATIONS_PER_JOB,
            help=f'Nombre maximum de locations par job (défaut: {DEFAULT_MAX_LOCATIONS_PER_JOB})',
        )

    def handle(self, *args, **options):
        input_path = options['input']
        output_path = options['output']
        max_per_job = options['max_per_job']

        if max_per_job < 1:
            raise CommandError('--max-per-job doit être >= 1.')

        self.stdout.write(
            self.style.SUCCESS(
                f'Correction du fichier Excel : max {max_per_job} locations par job'
            )
        )

        try:
            df = pd.read_excel(input_path, engine='openpyxl')
        except Exception as e:
            raise CommandError(f'Impossible de lire le fichier Excel : {e}')

        # Normaliser les noms de colonnes (comme l'API)
        df.columns = df.columns.str.strip().str.lower()

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise CommandError(
                f'Colonnes manquantes : {", ".join(missing)}. '
                f'Attendues : {", ".join(REQUIRED_COLUMNS)}. '
                f'Trouvées : {list(df.columns)}.'
            )

        # Séparer lignes actives et inactives
        active_mask = df.apply(
            lambda row: normalize_boolean(row.get('active')),
            axis=1
        )
        df_active = df[active_mask].copy()
        df_inactive = df[~active_mask].copy()

        # Pour les lignes inactives : vider job, session_1, session_2 (règle API)
        for col in ('job', 'session_1', 'session_2'):
            df_inactive[col] = ''

        if df_active.empty:
            # Aucune ligne active : sortir tel quel (avec inactives corrigées)
            out = pd.concat([df_active, df_inactive], ignore_index=True)
            out = out[REQUIRED_COLUMNS]
            try:
                out.to_excel(output_path, index=False, engine='openpyxl')
            except Exception as e:
                raise CommandError(f'Erreur lors de l\'écriture du fichier : {e}')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Fichier écrit : {output_path} (0 ligne(s) active(s), {len(df_inactive)} inactive(s))'
                )
            )
            return

        # Grouper les lignes actives par (warehouse, job_original, session_1, session_2)
        # pour préserver les sessions par "groupe logique", puis découper en paquets de max_per_job
        df_active['_session_1_norm'] = df_active['session_1'].apply(normalize_excel_value)
        df_active['_session_2_norm'] = df_active['session_2'].apply(normalize_excel_value)
        df_active['_job_orig'] = df_active['job'].apply(
            lambda x: normalize_excel_value(x) if isinstance(x, str) else ''
        )

        # Construire la liste de lignes actives avec nouveau numéro de job
        job_counter = 1
        new_active_rows = []

        # Grouper par (warehouse, job_orig, session_1, session_2) pour garder la même équipe par groupe
        group_cols = ['warehouse', '_job_orig', '_session_1_norm', '_session_2_norm']
        for key, grp in df_active.groupby(group_cols, dropna=False):
            warehouse, job_orig, s1, s2 = key
            # Découper en paquets de max_per_job
            start = 0
            while start < len(grp):
                chunk = grp.iloc[start:start + max_per_job]
                new_job = f'JOB-{job_counter:04d}'
                for _, row in chunk.iterrows():
                    new_active_rows.append({
                        'warehouse': row['warehouse'],
                        'emplacement': row['emplacement'],
                        'active': row['active'],
                        'job': new_job,
                        'session_1': s1,
                        'session_2': s2,
                    })
                job_counter += 1
                start += max_per_job

        df_active_new = pd.DataFrame(new_active_rows)

        # Réassembler : d'abord toutes les lignes actives (avec jobs 1, 2, ...), puis les inactives
        df_inactive_out = df_inactive[REQUIRED_COLUMNS].copy()
        out = pd.concat([df_active_new, df_inactive_out], ignore_index=True)
        out = out[REQUIRED_COLUMNS]

        try:
            out.to_excel(output_path, index=False, engine='openpyxl')
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'écriture du fichier : {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Fichier écrit : {output_path}'
            )
        )
        self.stdout.write(
            f'  Lignes actives : {len(df_active_new)} (réparties en {job_counter - 1} job(s), max {max_per_job} locations/job).'
        )
        self.stdout.write(
            f'  Lignes inactives : {len(df_inactive_out)} (job/session_1/session_2 vidés).'
        )
        self.stdout.write(
            self.style.WARNING(
                'Vérifiez que warehouse correspond au nom du warehouse (warehouse_name), '
                'et que session_1/session_2 sont au format equipe-1001..1999 / equipe-2001..2999.'
            )
        )
