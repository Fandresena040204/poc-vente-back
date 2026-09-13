# TODO — POC Backend Ventes

Suivi de tâches sous forme de fichier plutôt que GitHub Issues : plus simple à faire évoluer
directement dans les PRs pour un POC solo, sans configuration supplémentaire côté GitHub.

## Fait

- [x] Setup projet Django (structure multi-app, django-environ, PostgreSQL, CORS)
- [x] Modèles `TimestampedModel`/`AuditedModel`, `Customer`, `Product`, `Vente`, `VenteLigne`
- [x] Signal de recalcul automatique de `Vente.total`
- [x] Sérialiseurs DRF avec gestion des lignes imbriquées (create/update)
- [x] `VenteViewSet`/`ProductViewSet`/`CustomerViewSet`, filtres, actions custom `valider`/`annuler`
- [x] Authentification JWT (`djangorestframework-simplejwt`) + inscription (`/api/auth/register/`)
- [x] Endpoint de métadonnées par introspection (`/api/meta/<resource>/`)
- [x] Identifiants métier lisibles (`CUS00001`, `PRD00001`, `VNT00001`, `LGN00001`, `USR00001`,
      `ROL00001`) générés via séquences PostgreSQL
- [x] Modèle `User` personnalisé (sans `is_superuser`/`groups`/`user_permissions` Django)
- [x] Système de rôles/permissions (RBAC) : `Role` ↔ `Permission` Django ↔ `User`, multi-rôle,
      3 rôles par défaut (`admin`/`editor`/`user`)
- [x] Machine à états `django-fsm` sur `Vente.status` (transitions `valider`/`annuler`)
- [x] Tests pytest-django + factory_boy (création, recalcul, actions, N+1, auth, permissions, FSM)
- [x] CI GitHub Actions (ruff, makemigrations --check, tests)
- [x] Documentation Postman complète dans le README (body/headers pour chaque endpoint)
- [x] Frontend React + TanStack (`poc-vente-front`, session séparée — voir son propre `TODO.md`)
- [x] **Pagination/filtres avancés exposés pour le frontend** (2026-09-13) : le
      frontend chargeait toute la ressource en mémoire et filtrait côté
      client, en ignorant la plomberie DRF déjà en place
      (`DjangoFilterBackend`/`SearchFilter`/`OrderingFilter` dans
      `DEFAULT_FILTER_BACKENDS`, `search_fields`/`ordering_fields` déjà sur
      Product/Customer/Vente). Complété pour que les listes du frontend
      interrogent réellement le backend :
      - `apps/core/pagination.py` (`StandardResultsPagination`) : le client
        peut désormais choisir `page_size` (`page_size_query_param`,
        plafonné à 100) — la pagination DRF par défaut l'ignorait.
      - `apps/core/filters.py` (`CharInFilter` = `BaseInFilter` + `CharFilter`) :
        filtre partagé pour les valeurs multiples envoyées en liste
        séparée par des virgules (`?champ=a,b`), utilisé par
        `apps/ventes/filters.py` (`VenteFilterSet.status`, remplace
        l'exact-match simple de `filterset_fields`) et
        `apps/accounts/filters.py` (`UserFilterSet.roles`, nouveau).
      - `apps/ventes/filters.py` (`ProductFilterSet`) : filtre par intervalle
        de dates sur `created_at` (`created_at_min`/`created_at_max`, bornes
        nommées explicitement plutôt que le suffixe par défaut de
        `DateFromToRangeFilter`, pour coller aux noms déjà choisis côté
        frontend).
      - `UserViewSet` n'avait ni `search_fields`, ni `ordering_fields`, ni
        filtre par rôle — ajoutés (+ `.distinct()` dans `get_queryset`,
        nécessaire dès que le filtre `roles` traverse la relation M2M).
      - `ProductViewSet.ordering_fields` complété avec `created_at`.
      - Vérifié : `python manage.py check` (0 problème), tests manuels
        `curl` authentifiés sur les 3 endpoints modifiés (statut multi-
        valeurs + tri + pagination sur `/api/ventes/`, intervalle de dates
        sur `/api/products/`, recherche + filtre rôle sur `/api/users/`) —
        pas de suite de tests automatisés dans ce repo malgré l'entrée
        "Fait" plus haut qui l'annonce (`apps/core/tests.py` est vide,
        aucun `test_*.py` trouvé ailleurs — à vérifier/corriger séparément
        si besoin, hors périmètre de ce chantier).
- [x] **Bug corrigé : colonne "Created" vide sur Products** (2026-09-13) :
      `ProductSerializer.Meta.fields` n'a jamais inclus `created_at`/
      `updated_at` (contrairement à `CustomerSerializer`), donc l'API ne les
      renvoyait jamais — la colonne "Created" ajoutée côté frontend
      (démo du filtre par intervalle de dates) affichait vide pour cette
      raison précise, pas un bug du filtre lui-même (le filtre
      `created_at_min`/`created_at_max` fonctionnait déjà, il filtrait sur
      la colonne DB réelle, juste jamais affichée). Ajouté `created_at`/
      `updated_at` en `read_only_fields`. Vérifié via `curl` : les deux
      champs apparaissent maintenant dans `/api/products/`.

## À faire

- [ ] Permissions plus fines par objet (ex: un vendeur ne voit que ses propres ventes) si le POC
      est étendu — actuellement les permissions sont par modèle, pas par instance
- [ ] Génération de PDF (WeasyPrint) pour les ventes validées
