import re
from argparse import RawDescriptionHelpFormatter
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError, DjangoHelpFormatter
from django.db import connection, migrations
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ModelState
from django.db.migrations.writer import MigrationWriter


class HelpFormatter(DjangoHelpFormatter, RawDescriptionHelpFormatter):
    pass


class Command(BaseCommand):
    help = (
        "Génère une migration pour une vue SQL.\n\n"
        "Exemples :\n"
        "  python manage.py make_view_migration ventes ProductListView product_list_view "
        "--sql nouveau.sql\n"
        "  python manage.py make_view_migration ventes ProductListView product_list_view "
        "--sql nouveau.sql --old-sql ancien.sql\n"
        "  python manage.py make_view_migration ventes VenteListView vente_list_view "
        "--sql nouveau.sql --depends-on accounts:0009_rename_tables_drop_prefix"
    )

    def create_parser(self, prog_name, subcommand, **kwargs):
        kwargs['formatter_class'] = HelpFormatter
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('app_label')
        parser.add_argument('model_name')
        parser.add_argument('view_name')
        parser.add_argument('--sql', required=True)
        parser.add_argument('--old-sql')
        parser.add_argument('--depends-on', nargs='*')

    def _read_sql(self, path):
        try:
            sql = Path(path).read_text(encoding='utf-8').strip()
        except FileNotFoundError:
            raise CommandError(f"fichier '{path}' introuvable")

        if sql.endswith(';'):
            sql = sql[:-1]

        return sql

    def handle(self, *args, **options):
        app_label = options['app_label']
        model_name = options['model_name']
        view_name = options['view_name']
        sql_path = options['sql']
        old_sql_path = options['old_sql']

        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f"app '{app_label}' introuvable")

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(
                f"modèle '{model_name}' introuvable dans '{app_label}', écris d'abord le modèle"
            )

        new_sql = self._read_sql(sql_path)

        if old_sql_path is not None:
            old_sql = self._read_sql(old_sql_path)
        else:
            old_sql = None

        loader = MigrationLoader(connection)
        leaves = loader.graph.leaf_nodes(app_label)

        if len(leaves) == 0:
            raise CommandError(f"l'app '{app_label}' n'a aucune migration")
        elif len(leaves) > 1:
            raise CommandError(
                f"conflit de migrations dans '{app_label}' : {leaves}, lance makemigrations --merge"
            )
        else:
            parent = leaves[0]

        migrations_dir = Path(app_config.path) / 'migrations'

        numbers = []
        for file in migrations_dir.glob('*.py'):
            match = re.match(r'^(\d{4})_', file.name)
            if match:
                numbers.append(int(match.group(1)))

        next_number = max(numbers) + 1
        migration_name = f"{next_number:04d}_{view_name}_view"
        migration_path = migrations_dir / f"{migration_name}.py"

        forward_sql = f"CREATE OR REPLACE VIEW {view_name} AS\n{new_sql};"
        if old_sql is None:
            reverse_sql = f"DROP VIEW IF EXISTS {view_name};"
        else:
            reverse_sql = f"CREATE OR REPLACE VIEW {view_name} AS\n{old_sql};"

        operations = []
        if old_sql is None:
            model_state = ModelState.from_model(model)
            operations.append(
                migrations.CreateModel(
                    name=model_state.name,
                    fields=list(model_state.fields.items()),
                    options=model_state.options,
                    bases=model_state.bases,
                    managers=model_state.managers,
                )
            )
        operations.append(migrations.RunSQL(sql=forward_sql, reverse_sql=reverse_sql))

        dependencies = [parent]
        for extra in options['depends_on'] or []:
            dep_app, dep_name = extra.split(':', 1)
            dependencies.append((dep_app, dep_name))

        migration_class = type(
            'Migration',
            (migrations.Migration,),
            {'dependencies': dependencies, 'operations': operations},
        )
        migration = migration_class(migration_name, app_label)
        content = MigrationWriter(migration).as_string()
        migration_path.write_text(content, encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f"migration créée : {migration_path}"))
        self.stdout.write(
            self.style.WARNING(
                "lance ensuite :\n"
                "  python manage.py check_view_models\n"
                "  python manage.py makemigrations --check --dry-run"
            )
        )
