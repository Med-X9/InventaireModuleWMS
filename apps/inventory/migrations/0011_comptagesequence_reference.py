import hashlib

from django.db import migrations, models
from django.utils import timezone


def _generate_reference(sequence):
    """
    Reproduit la logique de ReferenceMixin.generate_reference pour les instances existantes.
    """
    timestamp_source = getattr(sequence, "created_at", None) or timezone.now()
    timestamp = int(timestamp_source.timestamp())
    timestamp_short = str(timestamp)[-4:]
    data_to_hash = f"{sequence.id}{timestamp}"
    hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:4].upper()
    reference = f"CS-{sequence.id}-{timestamp_short}-{hash_value}"
    if len(reference) > 20:
        reference = reference[:20]
    return reference


def populate_comptage_sequence_references(apps, schema_editor):
    ComptageSequence = apps.get_model("inventory", "ComptageSequence")
    HistoricalComptageSequence = apps.get_model("inventory", "HistoricalComptageSequence")

    reference_cache = {}
    sequences = ComptageSequence.objects.filter(reference__isnull=True)
    for sequence in sequences.iterator():
        generated = _generate_reference(sequence)
        sequence.reference = generated
        sequence.save(update_fields=["reference"])
        reference_cache[sequence.id] = generated

    historical_sequences = HistoricalComptageSequence.objects.filter(reference__isnull=True)
    for history in historical_sequences.iterator():
        reference = reference_cache.get(history.id)
        if not reference:
            reference = _generate_reference(history)
        history.reference = reference
        history.save(update_fields=["reference"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0010_add_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="comptagesequence",
            name="reference",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="historicalcomptagesequence",
            name="reference",
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True),
        ),
        migrations.RunPython(populate_comptage_sequence_references, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="comptagesequence",
            name="reference",
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name="historicalcomptagesequence",
            name="reference",
            field=models.CharField(db_index=True, max_length=20),
        ),
    ]

