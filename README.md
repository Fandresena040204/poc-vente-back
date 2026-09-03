# POC Vente Backend

POC backend Django/DRF validant le pattern décrit dans `Docs AI.md` : modèles Django explicites,
sérialiseurs/viewsets DRF, endpoint de métadonnées par introspection. Première ressource
implémentée : **Vente** (parent) / **VenteLigne** (enfant).

Le frontend React + TanStack sera abordé dans une session séparée — ce dépôt ne concerne que le
backend.

## Prérequis

- Python 3.12+
- PostgreSQL 14+

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash) — .venv/bin/activate sous Linux/Mac
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env` et adapter les valeurs, notamment `DATABASE_URL` :

```bash
cp .env.example .env
```

Créer la base et l'utilisateur PostgreSQL correspondants (adapter selon votre `.env`) :

```sql
CREATE ROLE poc_ventes_user LOGIN PASSWORD 'poc_ventes_pwd' CREATEDB;
CREATE DATABASE poc_ventes_db OWNER poc_ventes_user;
```

`CREATEDB` est nécessaire pour que Django puisse créer la base de test dédiée à la suite pytest.

## Migrations

```bash
python manage.py migrate
```

## Lancer le serveur

```bash
python manage.py runserver
```

L'API est disponible sous `/api/` (ex: `/api/ventes/`, `/api/products/`), avec authentification
JWT via `/api/token/` et `/api/token/refresh/`.

## Tests

```bash
python -m pytest -q
```

## Lint

```bash
ruff check .
```

## Endpoints principaux

- `GET/POST /api/ventes/` — liste/création de ventes (avec lignes imbriquées)
- `GET/PUT/PATCH/DELETE /api/ventes/{id}/` — détail d'une vente
- `POST /api/ventes/{id}/valider/` — action custom de validation d'une vente en brouillon
- `GET/POST /api/products/` — CRUD produits
- `GET /api/meta/{resource}/` — métadonnées introspectées d'une ressource (`ventes`, `products`)
- `POST /api/token/`, `POST /api/token/refresh/` — authentification JWT

## Suivi de projet

Voir `TODO.md` à la racine pour l'état d'avancement.
