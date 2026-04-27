from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0024_assigment_bloqued_date_assigment_debloqued_date_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE inventory_assigment "
                        "ADD COLUMN IF NOT EXISTS bloqued_date timestamp with time zone NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE inventory_assigment "
                        "DROP COLUMN IF EXISTS bloqued_date;"
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE inventory_assigment "
                        "ADD COLUMN IF NOT EXISTS debloqued_date timestamp with time zone NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE inventory_assigment "
                        "DROP COLUMN IF EXISTS debloqued_date;"
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE inventory_historicalassigment "
                        "ADD COLUMN IF NOT EXISTS bloqued_date timestamp with time zone NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE inventory_historicalassigment "
                        "DROP COLUMN IF EXISTS bloqued_date;"
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE inventory_historicalassigment "
                        "ADD COLUMN IF NOT EXISTS debloqued_date timestamp with time zone NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE inventory_historicalassigment "
                        "DROP COLUMN IF EXISTS debloqued_date;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="assigment",
                    name="bloqued_date",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="assigment",
                    name="debloqued_date",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="historicalassigment",
                    name="bloqued_date",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="historicalassigment",
                    name="debloqued_date",
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
    ]
