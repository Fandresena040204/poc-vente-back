# POC Vente Backend

POC backend Django/DRF validant le pattern décrit dans `Docs AI.md` : modèles Django explicites,
sérialiseurs/viewsets DRF, endpoint de métadonnées par introspection. Première ressource
implémentée : **Vente** (parent) / **VenteLigne** (enfant).

Le frontend React + TanStack sera abordé dans une session séparée — ce dépôt ne concerne que le
backend.

## Prérequis

- Python 3.12+
- PostgreSQL 14+
- Git et un compte GitHub avec accès au dépôt

## Cloner le projet

```bash
git clone https://github.com/Fandresena040204/poc-vente-back.git
cd poc-vente-back
```

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

## Structure du projet

Convention adoptée pour ce dépôt : **un fichier par classe**, à la manière Java, plutôt que des
modules `models.py`/`serializers.py`/`views.py` monolithiques. Chaque package expose ses classes
via `__init__.py`, donc les imports habituels (`from apps.ventes.models import Vente`) restent
valables.

```
apps/ventes/
├── models/
│   ├── product.py
│   ├── vente.py          # Vente + VenteStatus
│   └── vente_ligne.py
├── serializers/
│   ├── product_serializer.py
│   ├── vente_serializer.py
│   └── vente_ligne_serializer.py
├── views/
│   ├── product_viewset.py
│   └── vente_viewset.py
└── admin/
    ├── product_admin.py
    ├── vente_admin.py
    └── vente_ligne_inline.py
```

En ajoutant une nouvelle ressource métier, suivre le même découpage : un fichier par modèle, par
sérialiseur, par viewset, par classe d'admin.

## Endpoints principaux

### Authentification

- `POST /api/auth/register/` — inscription (crée un utilisateur, renvoie directement les tokens JWT)
- `POST /api/token/` — connexion (login), renvoie `access`/`refresh`
- `POST /api/token/refresh/` — renouvelle un `access` token à partir du `refresh`
- `GET/PATCH /api/auth/me/` — consulter/modifier son propre profil (utilisateur connecté)

### Utilisateurs et rôles (réservé aux administrateurs, `is_staff=True`)

- `GET /api/users/` — liste des utilisateurs (avec leurs rôles)
- `GET /api/users/{id}/` — détail d'un utilisateur
- `POST /api/users/{id}/assign_role/` — assigne un rôle (`{"role": "manager"}`)
- `POST /api/users/{id}/remove_role/` — retire un rôle
- `GET/POST /api/roles/`, `GET/PUT/PATCH/DELETE /api/roles/{id}/` — CRUD des rôles (`Group` Django)

### Ressources métier (authentification requise)

- `GET/POST /api/customers/`, `GET/PUT/PATCH/DELETE /api/customers/{id}/` — CRUD clients
- `GET/POST /api/products/`, `GET/PUT/PATCH/DELETE /api/products/{id}/` — CRUD produits
- `GET/POST /api/ventes/` — liste/création de ventes (avec lignes imbriquées)
- `GET/PUT/PATCH/DELETE /api/ventes/{id}/` — détail d'une vente
- `POST /api/ventes/{id}/valider/` — action custom de validation d'une vente en brouillon
- `GET /api/meta/{resource}/` — métadonnées introspectées d'une ressource (`ventes`, `products`, `customers`)

## Suivi de projet

Voir `TODO.md` à la racine pour l'état d'avancement.

## Contribuer

### Stratégie de branches

- `main` — code stable, déployable. **Protégée** : pas de push direct, merge uniquement via
  Pull Request avec la CI verte.
- `develop` — branche d'intégration. Toutes les fonctionnalités y sont fusionnées avant de partir
  vers `main`.
- `feature/xxx` — une branche par fonctionnalité, créée depuis `develop`
  (ex : `feature/model-vente`, `feature/viewset-vente`).

### Créer une branche de fonctionnalité

Toujours partir d'un `develop` à jour :

```bash
git checkout develop
git pull
git checkout -b feature/nom-de-la-fonctionnalite
```

### Développer et tester en local

```bash
# Lancer le serveur
python manage.py runserver

# Lancer les tests
python -m pytest -q

# Lancer le lint
ruff check .

# Vérifier qu'aucune migration n'est manquante
python manage.py makemigrations --check --dry-run
```

Les quatre commandes ci-dessus sont celles exécutées par la CI — les passer en local avant de
pousser évite un aller-retour inutile.

### Commiter

Utiliser des messages de commit conventionnels (`feat:`, `fix:`, `chore:`, `test:`, `docs:`,
`refactor:`, `ci:`) :

```bash
git add <fichiers concernés>
git commit -m "feat: description courte de la fonctionnalité"
```

Éviter `git add -A`/`git add .` sans vérifier `git status` avant, pour ne pas commiter de fichiers
indésirables (`.env`, `db.sqlite3`, etc. — déjà couverts par `.gitignore`).

### Pousser et ouvrir une Pull Request

```bash
git push -u origin feature/nom-de-la-fonctionnalite
gh pr create --base develop --head feature/nom-de-la-fonctionnalite \
  --title "feat: description courte" \
  --body "Résumé de ce que fait la PR et comment le tester."
```

(Ou directement depuis l'interface GitHub, bouton "Compare & pull request".)

La CI (lint + migrations + tests) se déclenche automatiquement sur la PR. Attendre qu'elle soit
verte avant de merger.

### Merger

Une fois la CI verte (et une relecture si vous travaillez à plusieurs) :

```bash
gh pr merge --merge --delete-branch
```

Toujours merger `feature/xxx` → `develop`. Le passage `develop` → `main` se fait de la même façon,
via une Pull Request dédiée, une fois les fonctionnalités validées sur `develop`.

### Mettre à jour sa branche locale après un merge

```bash
git checkout develop
git pull
```
