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

### Format des identifiants

Toutes les ressources utilisent un identifiant texte lisible (`PREFIXE` + numéro séquentiel sur
5 chiffres) comme clé primaire, généré côté serveur via une séquence PostgreSQL dédiée — jamais
fourni par le client :

| Ressource   | Préfixe | Exemple    |
|-------------|---------|------------|
| Customer    | `CUS`   | `CUS00001` |
| Product     | `PRD`   | `PRD00001` |
| Vente       | `VNT`   | `VNT00001` |
| VenteLigne  | `LGN`   | `LGN00001` |
| User        | `USR`   | `USR00001` |
| Role        | `ROL`   | `ROL00001` |

`User` est un modèle Django personnalisé (`AUTH_USER_MODEL = 'accounts.User'`), et `Role`
remplace le `Group` Django par défaut — les deux suivent donc le même format que les ressources
métier.

### Authentification

- `POST /api/auth/register/` — inscription (crée un utilisateur, renvoie directement les tokens JWT)
- `POST /api/token/` — connexion (login), renvoie `access`/`refresh`
- `POST /api/token/refresh/` — renouvelle un `access` token à partir du `refresh`
- `GET/PATCH /api/auth/me/` — consulter/modifier son propre profil (utilisateur connecté)

### Utilisateurs et rôles (réservé au rôle `admin`)

- `GET /api/users/` — liste des utilisateurs (avec leurs rôles)
- `GET /api/users/{id}/` — détail d'un utilisateur
- `POST /api/users/{id}/assign_role/` — assigne un rôle (`{"role": "manager"}`)
- `POST /api/users/{id}/remove_role/` — retire un rôle
- `GET/POST /api/roles/`, `GET/PUT/PATCH/DELETE /api/roles/{id}/` — CRUD des rôles

#### Comment savoir/faire qu'un utilisateur "a" le rôle admin

Le rôle `Role` (table `accounts_role`) est la **seule source de vérité** pour ces deux ressources.
`User` n'a même plus de champ `is_superuser` en base (retiré — Django ne fournit pas de notion de
superutilisateur en dehors de son propre système de permissions, qu'on n'utilise pas ici). Seul
`is_staff` subsiste, uniquement pour se connecter à `/admin/` (l'interface web native) — aucun lien
avec les permissions de l'API JSON. La permission `IsAdminRole` vérifie uniquement
`user.roles.filter(name='admin').exists()`.

Un rôle `admin` est **créé automatiquement par migration** (`accounts.0003_seed_admin_role`), donc
`Role` n'est jamais vide après un `migrate` — mais il n'est assigné à personne par défaut. Pour
l'assigner à un utilisateur (commande exécutée directement en base, donc pas soumise à la
permission `IsAdminRole` — c'est le mécanisme de bootstrap) :

```bash
python manage.py assign_admin_role <username>
```

Pour vérifier que ça a fonctionné, sans toucher à la base : `GET /api/auth/me/` renvoie `roles`
pour l'utilisateur connecté — n'importe qui peut vérifier ses propres droits via ce endpoint. Un
admin peut aussi vérifier via `GET /api/users/{id}/`.

### Ressources métier (permissions granulées par rôle)

- `GET/POST /api/customers/`, `GET/PUT/PATCH/DELETE /api/customers/{id}/` — CRUD clients
- `GET/POST /api/products/`, `GET/PUT/PATCH/DELETE /api/products/{id}/` — CRUD produits
- `GET/POST /api/ventes/` — liste/création de ventes (avec lignes imbriquées)
- `GET/PUT/PATCH/DELETE /api/ventes/{id}/` — détail d'une vente
- `POST /api/ventes/{id}/valider/` — action custom de validation d'une vente en brouillon
- `GET /api/meta/{resource}/` — métadonnées introspectées d'une ressource (`ventes`, `products`, `customers`)

### Système de permissions

Les ressources métier (`customers`, `products`, `ventes`) ne sont plus juste "réservées aux
connectés" — chaque méthode HTTP nécessite une **permission Django** précise (`add_x`, `view_x`,
`change_x`, `delete_x`, auto-générées par modèle), elle-même attribuée à un ou plusieurs **rôles**,
eux-mêmes assignés aux utilisateurs :

```
Permission (Django, auto-générée : add_vente, view_vente, change_vente, delete_vente, ...)
    ↓ ManyToMany
Role (admin, user, editor, ou un rôle personnalisé créé via /api/roles/)
    ↓ ManyToMany
User (peut avoir plusieurs rôles à la fois — leurs permissions se cumulent)
```

La classe `HasRolePermission` traduit l'action du ViewSet en permission requise :

| Action DRF                | Permission requise | Méthode HTTP    |
|----------------------------|---------------------|-----------------|
| `list` / `retrieve`        | `view_<modèle>`     | GET             |
| `create`                   | `add_<modèle>`      | POST            |
| `update` / `partial_update`| `change_<modèle>`   | PUT / PATCH     |
| `destroy`                  | `delete_<modèle>`   | DELETE          |
| action custom (ex: `valider`) | `change_<modèle>` (par défaut) | POST |

Un utilisateur a accès à l'action si **au moins un de ses rôles** possède la permission
correspondante (`user.roles.filter(permissions__codename=...).exists()`).

**3 rôles créés par défaut** (migration `accounts.0006_seed_role_permissions`), sur `customers`,
`products` et `ventes` :

| Rôle     | Peut faire                          |
|----------|--------------------------------------|
| `admin`  | Tout (add/view/change/delete)        |
| `editor` | Créer, lire, modifier (pas supprimer) |
| `user`   | Créer et lire seulement               |

Un utilisateur peut avoir **plusieurs rôles simultanément** (`roles` est un `ManyToManyField`) —
leurs permissions se cumulent. Exemple : un utilisateur avec le rôle `user` (create+read) *et* un
rôle personnalisé n'accordant que `delete_customer` pourra créer, lire **et** supprimer des
clients, mais toujours pas les modifier.

`roles`/`users` (gestion des rôles eux-mêmes) restent séparément gérés par `IsAdminRole` (rôle
`admin` uniquement), pas par ce système générique — voir plus haut.

### Récapitulatif des permissions par ressource

| Ressource     | GET (liste/détail)     | POST                    | PUT/PATCH               | DELETE                   |
|---------------|-------------------------|--------------------------|---------------------------|----------------------------|
| `auth/register` | —                     | Public (`AllowAny`)      | —                          | —                           |
| `auth/me`     | Connecté                | —                         | Connecté (son propre profil) | —                       |
| `token`       | —                       | Public (`AllowAny`)      | —                          | —                           |
| `customers`   | Rôle avec `view_customer` | Rôle avec `add_customer` | Rôle avec `change_customer` | Rôle avec `delete_customer` |
| `products`    | Rôle avec `view_product`  | Rôle avec `add_product`  | Rôle avec `change_product`  | Rôle avec `delete_product`  |
| `ventes`      | Rôle avec `view_vente`    | Rôle avec `add_vente`    | Rôle avec `change_vente`    | Rôle avec `delete_vente`    |
| `roles`       | Rôle `admin`            | Rôle `admin`             | Rôle `admin`               | Rôle `admin`                |
| `users`       | Rôle `admin`            | — (pas de création directe, passer par `auth/register`) | — (utiliser `assign_role`/`remove_role`) | — |

« Rôle `admin` » = l'utilisateur a le rôle `admin` assigné via
`python manage.py assign_admin_role <username>`.

## Guide de test Postman

Base URL locale : `http://localhost:8000`. Pense à libérer le port avant de tester
(`python manage.py runserver` doit être le seul processus dessus).

Créer une variable d'environnement Postman `base_url = http://localhost:8000` et une variable
`access_token` (à remplir après le login/register) évite de retaper l'URL et le header à chaque
requête. Dans les exemples ci-dessous, remplace `{{base_url}}` par du texte en dur si tu ne veux
pas créer d'environnement.

Pour chaque requête protégée, ajouter dans l'onglet **Headers** de Postman :

```
Authorization: Bearer <access_token>
```

(ou dans l'onglet **Auth** → Type `Bearer Token` → coller le token).

---

### 1. Inscription (sign up) — publique

- **Méthode** : `POST`
- **URL** : `{{base_url}}/api/auth/register/`
- **Headers** : `Content-Type: application/json`
- **Body (raw JSON)** :
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "MotDePasseSolide123!"
}
```
- **Réponse 201** :
```json
{
  "user": { "id": "USR00002", "username": "alice", "email": "alice@example.com" },
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```
Le mot de passe est validé par les règles Django (`validate_password`) : au moins 8 caractères,
pas uniquement numérique, pas trop commun.

### 2. Connexion (login)

- **Méthode** : `POST`
- **URL** : `{{base_url}}/api/token/`
- **Headers** : `Content-Type: application/json`
- **Body** :
```json
{
  "username": "alice",
  "password": "MotDePasseSolide123!"
}
```
- **Réponse 200** : `{ "access": "<jwt>", "refresh": "<jwt>" }`. Copier `access` dans la variable
  Postman `access_token`.

### 3. Rafraîchir le token

- **Méthode** : `POST`
- **URL** : `{{base_url}}/api/token/refresh/`
- **Body** :
```json
{ "refresh": "<refresh_token_obtenu_au_login>" }
```
- **Réponse 200** : `{ "access": "<nouveau_jwt>" }`

### 4. Mon profil

- **GET** `{{base_url}}/api/auth/me/` — headers : `Authorization: Bearer {{access_token}}`
- **PATCH** `{{base_url}}/api/auth/me/` — même header, body :
```json
{ "first_name": "Alice", "last_name": "Martin" }
```

### 5. Clients (`customers`) — nécessite le rôle approprié (`view_customer`/`add_customer`/...)

Un utilisateur `role_only_admin` type n'a pas forcément la permission ici — utilise un compte
avec le rôle `admin`, `editor` ou `user` (créés par défaut), ou crée un rôle sur-mesure (étape 8).

- **Créer** — `POST {{base_url}}/api/customers/` (nécessite `add_customer`)
```json
{
  "name": "Acme Corp",
  "email": "contact@acme.test",
  "phone": "0123456789"
}
```
- **Lister** — `GET {{base_url}}/api/customers/` (nécessite `view_customer`)
- **Détail** — `GET {{base_url}}/api/customers/CUS00001/` (nécessite `view_customer`)
- **Modifier** — `PATCH {{base_url}}/api/customers/CUS00001/` body : `{ "phone": "0698765432" }`
  (nécessite `change_customer` — le rôle `user` par défaut ne l'a pas, renvoie 403)
- **Supprimer** — `DELETE {{base_url}}/api/customers/CUS00001/` (nécessite `delete_customer` —
  seul le rôle `admin` par défaut l'a)

Toutes ces requêtes nécessitent le header `Authorization: Bearer {{access_token}}`.

### 6. Produits (`products`) — mêmes règles de permission que `customers`

- **Créer** — `POST {{base_url}}/api/products/`
```json
{
  "name": "Clavier mécanique",
  "sku": "SKU-001",
  "default_price": "49.90"
}
```
- **Lister** — `GET {{base_url}}/api/products/`
- **Détail** — `GET {{base_url}}/api/products/PRD00001/`
- **Modifier** — `PATCH {{base_url}}/api/products/PRD00001/` body : `{ "default_price": "39.90" }`
- **Supprimer** — `DELETE {{base_url}}/api/products/PRD00001/`

### 7. Ventes (`ventes`) — mêmes règles de permission (`view_vente`/`add_vente`/`change_vente`/`delete_vente`)

`POST /api/ventes/{id}/valider/` nécessite `change_vente` (le rôle `user` ne l'a pas, `editor` et
`admin` l'ont).

- **Créer une vente avec lignes** — `POST {{base_url}}/api/ventes/`
```json
{
  "customer": "CUS00001",
  "lines": [
    { "product": "PRD00001", "quantity": "2", "unit_price": "49.90" },
    { "product": "PRD00002", "quantity": "1", "unit_price": "15.00" }
  ]
}
```
  `customer` et `product` sont les `id` (codes) créés aux étapes 5 et 6. `total` est calculé
  automatiquement côté serveur (ne pas l'envoyer, il est en lecture seule).
- **Lister** — `GET {{base_url}}/api/ventes/` (filtres possibles : `?status=draft`,
  `?customer=CUS00001`, `?ordering=-created_at`, `?search=acme`)
- **Détail** — `GET {{base_url}}/api/ventes/VNT00001/`
- **Modifier les lignes** — `PATCH {{base_url}}/api/ventes/VNT00001/`
```json
{
  "lines": [
    { "id": "LGN00001", "quantity": "3", "unit_price": "49.90", "product": "PRD00001" }
  ]
}
```
  Une ligne avec `id` existant est mise à jour, une ligne sans `id` est créée, une ligne
  existante absente du tableau envoyé est supprimée.
- **Supprimer** — `DELETE {{base_url}}/api/ventes/VNT00001/`
- **Valider une vente (brouillon → validée)** — `POST {{base_url}}/api/ventes/VNT00001/valider/`
  (pas de body). Renvoie 400 si la vente n'est pas en statut `draft`.

### 8. Rôles (`roles`) — réservé au rôle `admin`

Un rôle `admin` existe déjà par défaut (créé par migration), mais n'est assigné à personne. Pour
en donner l'accès à un compte (ex: ton superuser local `testuser`) :

```bash
python manage.py assign_admin_role testuser
```

Connecte-toi ensuite via l'étape 2 pour récupérer son token.

- **Créer un rôle avec des permissions** — `POST {{base_url}}/api/roles/`
```json
{
  "name": "manager",
  "permissions": ["view_customer", "add_customer", "change_customer"]
}
```
  `permissions` prend une liste de `codename` Django (`view_<modèle>`, `add_<modèle>`,
  `change_<modèle>`, `delete_<modèle>` — pour `customer`, `product` ou `vente`).
- **Lister** — `GET {{base_url}}/api/roles/` (chaque rôle renvoie sa liste de `permissions`)
- **Modifier les permissions d'un rôle** — `PATCH {{base_url}}/api/roles/ROL00003/` body :
```json
{ "permissions": ["view_customer", "add_customer", "delete_customer"] }
```
  (remplace entièrement la liste — pour ajouter une seule permission à un rôle existant, renvoyer
  la liste complète souhaitée)
- **Supprimer** — `DELETE {{base_url}}/api/roles/ROL00003/`

Avec un token d'utilisateur sans le rôle `admin`, ces requêtes renvoient `403 Forbidden`.

### 9. Utilisateurs et assignation de rôle (`users`) — réservé au rôle `admin`

- **Lister** — `GET {{base_url}}/api/users/` → renvoie chaque utilisateur avec son tableau `roles`
- **Détail** — `GET {{base_url}}/api/users/USR00002/`
- **Assigner un rôle** — `POST {{base_url}}/api/users/USR00002/assign_role/`
```json
{ "role": "manager" }
```
  Renvoie `404` si le rôle n'existe pas encore (le créer d'abord via l'étape 8).
- **Retirer un rôle** — `POST {{base_url}}/api/users/USR00002/remove_role/`
```json
{ "role": "manager" }
```

Il n'y a pas de création/suppression d'utilisateur via `/api/users/` : la création passe par
`/api/auth/register/` (étape 1). C'est un choix volontaire pour ce POC — à faire évoluer si un
vrai back-office de gestion des comptes est nécessaire.

### 10. Métadonnées (introspection)

- `GET {{base_url}}/api/meta/ventes/`
- `GET {{base_url}}/api/meta/products/`
- `GET {{base_url}}/api/meta/customers/`

Aucun body, retourne la structure des champs du sérialiseur correspondant (utile pour un futur
frontend générique).

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
