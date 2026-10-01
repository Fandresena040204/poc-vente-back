import importlib
import sys
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import connection, models

from apps.ventes.models import VenteListView

pytestmark = pytest.mark.django_db

VIEW_NAME = 'demo_ligne_list_view'
MIGRATIONS_DIR = Path(apps.get_app_config('ventes').path) / 'migrations'

SQL_V1 = "SELECT 'L1'::varchar AS id, 'V1'::varchar AS vente_id, 2::numeric(10, 2) AS quantity;"
SQL_V2 = "SELECT 'L1'::varchar AS id, 'V1'::varchar AS vente_id, 5::numeric(10, 2) AS quantity;"


@pytest.fixture
def demo_model():
    # même cas que VenteLigneListView.vente : FK vers une vue, avec db_column
    class DemoLigneListView(models.Model):
        id = models.CharField(max_length=20, primary_key=True)
        vente = models.ForeignKey(
            VenteListView,
            on_delete=models.DO_NOTHING,
            db_column='vente_id',
            db_constraint=False,
            related_name='+',
        )
        quantity = models.DecimalField(max_digits=10, decimal_places=2)

        class Meta:
            app_label = 'ventes'
            managed = False
            db_table = VIEW_NAME

    yield DemoLigneListView

    del apps.all_models['ventes']['demolignelistview']
    apps.clear_cache()


@pytest.fixture
def generated_files():
    yield

    for path in MIGRATIONS_DIR.glob(f'*_{VIEW_NAME}_view.py'):
        path.unlink()
        sys.modules.pop(f'apps.ventes.migrations.{path.stem}', None)
    for path in (MIGRATIONS_DIR / '__pycache__').glob(f'*_{VIEW_NAME}_view.*.pyc'):
        path.unlink()
    importlib.invalidate_caches()


def make_view_migration(tmp_path, sql, old_sql=None, depends_on=None):
    sql_file = tmp_path / 'new.sql'
    sql_file.write_text(sql, encoding='utf-8')
    options = {'sql': str(sql_file)}

    if old_sql is not None:
        old_sql_file = tmp_path / 'old.sql'
        old_sql_file.write_text(old_sql, encoding='utf-8')
        options['old_sql'] = str(old_sql_file)

    if depends_on is not None:
        options['depends_on'] = depends_on

    call_command(
        'make_view_migration',
        'ventes',
        'DemoLigneListView',
        VIEW_NAME,
        stdout=StringIO(),
        **options,
    )
    importlib.invalidate_caches()
    return sorted(MIGRATIONS_DIR.glob(f'*_{VIEW_NAME}_view.py'))[-1]


def load_migration(path):
    return importlib.import_module(f'apps.ventes.migrations.{path.stem}').Migration


def view_quantity():
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT quantity FROM {VIEW_NAME}')
        return cursor.fetchone()[0]


def test_creation_generates_create_model_and_run_sql(demo_model, generated_files, tmp_path):
    path = make_view_migration(tmp_path, SQL_V1)
    create_model, run_sql = load_migration(path).operations

    assert create_model.name == 'DemoLigneListView'
    fields = dict(create_model.fields)
    assert list(fields) == ['id', 'vente', 'quantity']
    assert fields['vente'].db_column == 'vente_id'
    assert create_model.options['managed'] is False

    assert run_sql.sql == f'CREATE OR REPLACE VIEW {VIEW_NAME} AS\n{SQL_V1[:-1]};'
    assert run_sql.reverse_sql == f'DROP VIEW IF EXISTS {VIEW_NAME};'

    call_command('makemigrations', 'ventes', check=True, dry_run=True, stdout=StringIO())

    call_command('migrate', 'ventes', path.stem, verbosity=0)
    assert view_quantity() == Decimal('2.00')


def test_modification_reverse_restores_old_definition(demo_model, generated_files, tmp_path):
    first = make_view_migration(tmp_path, SQL_V1)
    call_command('migrate', 'ventes', first.stem, verbosity=0)

    second = make_view_migration(tmp_path, SQL_V2, old_sql=SQL_V1)
    operations = load_migration(second).operations

    assert len(operations) == 1
    assert operations[0].sql == f'CREATE OR REPLACE VIEW {VIEW_NAME} AS\n{SQL_V2[:-1]};'
    assert operations[0].reverse_sql == f'CREATE OR REPLACE VIEW {VIEW_NAME} AS\n{SQL_V1[:-1]};'

    call_command('migrate', 'ventes', second.stem, verbosity=0)
    assert view_quantity() == Decimal('5.00')

    call_command('migrate', 'ventes', first.stem, verbosity=0)
    assert view_quantity() == Decimal('2.00')


def test_depends_on_adds_extra_dependency(demo_model, generated_files, tmp_path):
    path = make_view_migration(
        tmp_path, SQL_V1, depends_on=['accounts:0009_rename_tables_drop_prefix']
    )
    dependencies = load_migration(path).dependencies

    assert ('accounts', '0009_rename_tables_drop_prefix') in dependencies
    assert len(dependencies) == 2


def create_demo_view(columns):
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE VIEW {VIEW_NAME} AS SELECT {columns}')


def check_view_models_ok():
    out = StringIO()
    call_command('check_view_models', stdout=out)
    return out.getvalue()


def check_view_models_fails():
    out = StringIO()
    with pytest.raises(SystemExit) as exit_info:
        call_command('check_view_models', stdout=out)
    assert exit_info.value.code == 1
    return out.getvalue()


def test_check_view_models_ok_when_views_match():
    output = check_view_models_ok()

    assert 'ProductListView (product_list_view) : OK' in output
    assert 'VenteListView (vente_list_view) : OK' in output
    assert 'VenteLigneListView (vente_ligne_list_view) : OK' in output


def test_check_view_models_uses_db_column_for_fk(demo_model):
    create_demo_view("'L1'::varchar AS id, 'V1'::varchar AS vente_id, 2::numeric AS quantity")

    output = check_view_models_ok()

    assert 'VenteLigneListView (vente_ligne_list_view) : OK' in output
    assert f'DemoLigneListView ({VIEW_NAME}) : OK' in output
    assert "'vente'" not in output


def test_check_view_models_detects_column_added_in_db(demo_model):
    create_demo_view(
        "'L1'::varchar AS id, 'V1'::varchar AS vente_id, 2::numeric AS quantity, "
        "'x'::varchar AS note"
    )

    output = check_view_models_fails()

    assert "colonne 'note' présente en base mais absente du modèle" in output
    assert '1 modèle(s) en écart avec la base.' in output


def test_check_view_models_detects_column_removed_from_db(demo_model):
    create_demo_view("'L1'::varchar AS id, 'V1'::varchar AS vente_id")

    output = check_view_models_fails()

    assert "colonne 'quantity' déclarée sur le modèle mais absente en base" in output


def test_check_view_models_reports_missing_view(demo_model):
    output = check_view_models_fails()

    assert f'DemoLigneListView ({VIEW_NAME}) : absente en base' in output
    assert 'colonne' not in output
