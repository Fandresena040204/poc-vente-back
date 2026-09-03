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

## À faire

- [ ] Permissions plus fines par objet (ex: un vendeur ne voit que ses propres ventes) si le POC
      est étendu — actuellement les permissions sont par modèle, pas par instance
- [ ] Pagination et filtres avancés côté frontend une fois React/TanStack démarré
- [ ] Génération de PDF (WeasyPrint) pour les ventes validées
- [ ] Frontend React + TanStack (hors périmètre de ce POC, session séparée)
