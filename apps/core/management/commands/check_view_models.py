import sys

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        "Vérifie que les colonnes de chaque modèle unmanaged correspondent à sa vue en base. "
        "Exemple : python manage.py check_view_models"
    )

    def _db_columns(self, table):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = %s",
                [table],
            )
            return {row[0] for row in cursor.fetchall()}

    def handle(self, *args, **options):
        unmanaged_models = [model for model in apps.get_models() if not model._meta.managed]
        unmanaged_models.sort(key=lambda model: model.__name__)

        errors = 0
        for model in unmanaged_models:
            table = model._meta.db_table
            title = f"{model.__name__} ({table})"

            model_columns = {
                field.column
                for field in model._meta.get_fields()
                if field.concrete and not field.many_to_many
            }
            db_columns = self._db_columns(table)

            if not db_columns:
                errors += 1
                message = f"{title} : absente en base (migration pas encore appliquée ?)"
                self.stdout.write(self.style.ERROR(message))
                continue

            missing_in_model = sorted(db_columns - model_columns)
            missing_in_db = sorted(model_columns - db_columns)

            if not missing_in_model and not missing_in_db:
                self.stdout.write(self.style.SUCCESS(f"{title} : OK"))
                continue

            errors += 1
            self.stdout.write(self.style.ERROR(f"{title} :"))
            for column in missing_in_model:
                self.stdout.write(
                    f"  - colonne '{column}' présente en base mais absente du modèle"
                )
            for column in missing_in_db:
                self.stdout.write(
                    f"  - colonne '{column}' déclarée sur le modèle mais absente en base"
                )

        if errors:
            self.stdout.write(self.style.ERROR(f"{errors} modèle(s) en écart avec la base."))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS("Tous les modèles sont cohérents avec la base."))
