# Prompt — POC Backend Django/DRF

## Contexte

Tu es un ingénieur backend senior chargé de démarrer un POC (proof of concept). Le document d'architecture ci-joint (`Docs_AI.md`) décrit l'approche cible : **modèles Django explicites** (pas de moteur d'entités génériques), DRF pour l'API, endpoint de métadonnées basé sur introspection, et un futur frontend React + TanStack (hors périmètre pour l'instant).

**Ce POC ne concerne que le backend.** Ne touche à aucun code frontend. Le frontend sera abordé dans une session ultérieure, avec des consignes séparées, une fois le backend testé et validé.

## Objectif du POC

Implémenter, de bout en bout, une première ressource métier complète — **Vente** (parent) et **VenteLigne** (enfant) — pour valider le pattern décrit dans le document avant de le répliquer sur les ressources suivantes.

## Périmètre technique attendu

1. **Setup du projet**
   - Projet Django avec structure multi-app (`config/`, `apps/core`, `apps/accounts`, `apps/ventes`)
   - `django-environ` pour la configuration via `.env` (fournir un `.env.example`)
   - PostgreSQL comme base de données
   - `django-cors-headers` configuré (même si pas de frontend pour l'instant, prépare le terrain)
   - `requirements.txt` ou `pyproject.toml` propre, versions figées

2. **Modèles**
   - `TimestampedModel` et `AuditedModel` (mixins abstraits réutilisables) dans `apps/core`
   - `Customer` (client) minimal dans `apps/accounts` ou une app dédiée
   - `Product` minimal
   - `Vente` (hérite de `AuditedModel`, FK vers `Customer`, `status`, `total`)
   - `VenteLigne` (FK vers `Vente` en `CASCADE`, FK vers `Product` en `PROTECT`, `quantity`, `unit_price`)
   - Signal `post_save`/`post_delete` sur `VenteLigne` pour recalculer automatiquement `Vente.total`
   - Migrations propres et committées

3. **Sérialiseurs DRF**
   - `VenteLigneSerializer`
   - `VenteSerializer` avec sérialiseur imbriqué en lecture, et `create()`/`update()` surchargés pour gérer la création/modification des lignes en une seule requête
   - `total` en `read_only_fields` (jamais calculé côté client)

4. **ViewSets et routing**
   - `VenteViewSet` (`ModelViewSet`) avec `select_related`/`prefetch_related` pour éviter le N+1
   - Filtres de base (`status`, `customer`)
   - Une action custom `@action` pertinente (ex: `approve` ou équivalent, à toi de proposer selon le doc)
   - Router DRF standard

5. **Authentification et permissions**
   - JWT via `djangorestframework-simplejwt`
   - Permissions de base (`IsAuthenticated`), même simplifiées pour le POC

6. **Endpoint de métadonnées**
   - Implémenter au minimum la réponse `OPTIONS` native DRF sur `/api/ventes/`
   - Si le temps le permet, un endpoint custom d'introspection comme décrit dans le document (section 5)

7. **Tests**
   - `pytest-django` + `factory_boy`
   - Au moins : création d'une vente avec lignes, recalcul du total, tentative de transition invalide si tu ajoutes un statut avec `django-fsm`
   - Un test qui vérifie qu'aucune requête N+1 n'apparaît sur le endpoint de liste

8. **CI**
   - GitHub Actions : lint (`ruff`), tests, vérification `makemigrations --check`

## Gestion Git et gestion de projet — obligatoire

- **Initialise un dépôt Git et crée un dépôt distant public sur GitHub** (utilise le nom `poc-ventes-backend` sauf si tu proposes mieux, dans ce cas demande confirmation avant de créer le repo)
- Configure une branche `main` protégée (pas de commit direct dessus une fois le setup initial poussé)
- Utilise une stratégie de branches claire, par exemple :
  - `main` — code stable
  - `develop` — intégration
  - `feature/xxx` — une branche par fonctionnalité (ex: `feature/setup-django`, `feature/model-vente`, `feature/serializer-vente`, `feature/viewset-vente`, `feature/auth-jwt`, `feature/tests`)
- Chaque fonctionnalité doit passer par une Pull Request vers `develop`, avec une description claire de ce qui a été fait
- Utilise des messages de commit conventionnels (`feat:`, `fix:`, `chore:`, `test:`, `docs:`)
- **Crée une TODO list / suivi de tâches** : soit via des GitHub Issues (une par étape du périmètre ci-dessus), soit via un fichier `TODO.md` à la racine, mis à jour au fur et à mesure — précise laquelle des deux méthodes tu choisis et pourquoi
- Ajoute un `README.md` clair : comment installer, configurer le `.env`, lancer les migrations, lancer les tests, lancer le serveur

## Consignes de méthode

- Avance étape par étape dans l'ordre du périmètre ci-dessus (setup → modèles → sérialiseurs → viewsets → auth → métadonnées → tests → CI)
- Après chaque étape significative, fais un point : ce qui a été fait, ce qui reste, et attends une validation avant de continuer si un choix d'architecture n'est pas évident
- Ne commence aucun travail frontend, même si ça te semble rapide à faire — j'apporterai des consignes séparées pour cette partie
- Si une partie du document d'architecture est ambiguë ou incomplète pour l'implémentation, pose la question plutôt que de supposer

## Livrable final attendu pour ce POC

- Un dépôt GitHub public, fonctionnel, avec historique de branches et PRs propre
- Un backend Django/DRF qui tourne en local avec `Vente`/`VenteLigne` en CRUD complet, testé
- Une liste de tâches (issues ou `TODO.md`) reflétant l'état d'avancement réel
- Un README permettant à n'importe qui de cloner et lancer le projet en quelques minutes
