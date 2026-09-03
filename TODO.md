# TODO — POC Backend Ventes

Suivi de tâches sous forme de fichier plutôt que GitHub Issues : plus simple à faire évoluer
directement dans les PRs pour un POC solo, sans configuration supplémentaire côté GitHub.

## Fait

- [x] Setup projet Django (structure multi-app, django-environ, PostgreSQL, CORS)
- [x] Modèles `TimestampedModel`/`AuditedModel`, `Customer`, `Product`, `Vente`, `VenteLigne`
- [x] Signal de recalcul automatique de `Vente.total`
- [x] Sérialiseurs DRF avec gestion des lignes imbriquées (create/update)
- [x] `VenteViewSet`/`ProductViewSet`, filtres, action custom `valider`
- [x] Authentification JWT (`djangorestframework-simplejwt`)
- [x] Endpoint de métadonnées par introspection (`/api/meta/<resource>/`)
- [x] Tests pytest-django + factory_boy (création, recalcul, action, N+1, auth)
- [x] CI GitHub Actions (ruff, makemigrations --check, tests)

## À faire

- [ ] Permissions plus fines (par objet / par champ) si le POC est étendu
- [ ] Pagination et filtres avancés côté frontend une fois React/TanStack démarré
- [ ] Génération de PDF (WeasyPrint) pour les ventes validées
- [ ] Mettre en place `django-fsm` si des transitions de statut plus complexes apparaissent
- [ ] Frontend React + TanStack (hors périmètre de ce POC, session séparée)
