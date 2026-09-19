# Guide développeur — Backend

Ce guide explique comment étendre l'API Django : créer une app, un
modèle, un serializer, un viewset filtrable, et brancher tout ça aux
permissions. Il ne couvre que le **backend** (`poc-vente-back`) — pour le
frontend, voir `GUIDE_DEVELOPPEUR.md` dans le dépôt `poc-vente-front`.

Pour l'installation et le lancement, voir `README.md`. Pour l'utilisation
de l'app une fois connecté, voir `GUIDE_UTILISATION.md` (frontend).

Les exemples reprennent la ressource `Product` (la plus simple des
ressources en place : Customers, Products, Ventes) comme fil rouge — pour
une ressource avec des lignes imbriquées, s'inspirer plutôt de `Vente`/
`VenteLigne`.

**Convention du projet : un fichier par classe**, à la manière Java,
plutôt que des modules `models.py`/`serializers.py`/`views.py`
monolithiques. Chaque package expose ses classes via `__init__.py`.

```
apps/ventes/
├── models/product.py
├── serializers/product_serializer.py
├── views/product_viewset.py
├── admin/product_admin.py
├── filters/product_filters.py
├── signals/vente_ligne_signals.py
├── migrations/
├── factories.py
├── tests.py
└── urls.py
```

Ce découpage n'est pas arbitraire : chaque fichier répond à une question
différente sur la ressource (« c'est quoi en base ? », « qu'est-ce que
l'API expose ? », « qui peut faire quoi ? », « comment on filtre la
liste ? », « que se passe-t-il automatiquement quand ça change ? »). Un
fichier ne devient un **package** (dossier + `__init__.py`) que s'il
regroupe plusieurs classes portant une vraie logique — `filters/`/
`signals/` n'existent que parce que plusieurs modèles de `apps.ventes`
ont chacun le leur ; `admin/product_admin.py` reste un enregistrement à
une ligne, pas de logique, donc pas besoin d'y réfléchir davantage.

---

## 0. Créer une nouvelle app (si la ressource n'a pas encore de home)

Les ressources actuelles vivent dans `apps.accounts` (Customer, User,
Role) ou `apps.ventes` (Product, Vente, VenteLigne). Une nouvelle
ressource va presque toujours dans une app existante — ne créer une
nouvelle app que si le domaine est vraiment différent.

1. **Créer le dossier.** Il existe une commande Django pour ça
   (`python manage.py startapp <nom> apps/<nom>` — le second argument
   place l'app dans `apps/` plutôt qu'à la racine du projet), mais elle
   génère la structure **plate** par défaut de Django (`admin.py`,
   `models.py`, `views.py`, `tests.py`, `migrations/`) — pas les packages
   par entité utilisés ici, et rien pour `serializers`/`filters`/
   `factories.py` (concepts DRF/du projet, pas du Django de base). Deux
   options :
   - la lancer puis **réorganiser** ce qu'elle génère (transformer
     `models.py` en dossier `models/` + fichier par entité, etc.) ;
   - ou créer directement la structure cible à la main, plus rapide dès
     qu'on sait qu'on va vouloir des packages :

   ```
   apps/ma_nouvelle_app/
   ├── __init__.py
   ├── apps.py
   ├── models/__init__.py
   ├── serializers/__init__.py
   ├── views/__init__.py
   ├── admin/__init__.py
   ├── migrations/__init__.py
   ├── factories.py
   ├── tests.py
   └── urls.py
   ```

   **Pas de commande pour scaffolder un modèle/serializer/viewset
   individuel** — ni Django ni DRF n'en fournissent (contrairement à des
   frameworks type Rails avec ses générateurs) : ce sont de simples
   classes Python à écrire à la main, voir §§ 1, 3 et 5 ci-dessous.

2. **`apps.py`** :

   ```python
   from django.apps import AppConfig

   class MaNouvelleAppConfig(AppConfig):
       name = 'apps.ma_nouvelle_app'
   ```

   (Ajouter une méthode `ready()` important les `signals` uniquement si
   l'app en a besoin — voir `apps/ventes/apps.py` pour l'exemple du
   recalcul automatique de `Vente.total`.)

3. **L'enregistrer** dans `config/settings.py`, section `INSTALLED_APPS`,
   sous `# Apps locales` :

   ```python
   INSTALLED_APPS = [
       ...
       'apps.core',
       'apps.accounts',
       'apps.ventes',
       'apps.ma_nouvelle_app',  # à ajouter
   ]
   ```

4. **Brancher ses URLs** dans `config/urls.py` (voir § 7 plus bas pour le
   contenu de `urls.py` de l'app elle-même) :

   ```python
   urlpatterns = [
       ...
       path('api/', include('apps.ma_nouvelle_app.urls')),
   ]
   ```

---

## 1. Créer une entité (modèle)

1. **Le modèle** — hérite de `TimestampedModel` (ajoute `created_at`/
   `updated_at` automatiquement) ou `AuditedModel` (ajoute en plus
   `created_by`/`updated_by`, voir `Vente`), avec un `id` texte généré
   côté serveur via une séquence Postgres (jamais fourni par le client) :

   ```python
   # apps/ventes/models/product.py
   from django.db import models
   from apps.core.models import TimestampedModel
   from apps.core.utils import generate_reference

   class Product(TimestampedModel):
       id = models.CharField(max_length=20, primary_key=True, editable=False)
       name = models.CharField(max_length=255)
       sku = models.CharField(max_length=64, unique=True)
       default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

       class Meta:
           ordering = ['name']

       def save(self, *args, **kwargs):
           if not self.id:
               self.id = generate_reference('product_id_seq', 'PRD')
           super().save(*args, **kwargs)

       def __str__(self):
           return self.name
   ```

   L'exporter dans `apps/ventes/models/__init__.py`
   (`from apps.ventes.models.product import Product`, + `__all__`).

2. **La séquence Postgres** — une migration `RunSQL` dédiée (le nom de la
   séquence doit correspondre exactement à celui passé à
   `generate_reference`) :

   ```python
   migrations.RunSQL(
       sql="CREATE SEQUENCE IF NOT EXISTS product_id_seq;",
       reverse_sql="DROP SEQUENCE IF EXISTS product_id_seq;",
   )
   ```

   Choisir un préfixe court et unique (`PRD`, `CUS`, `VNT`...) — il
   apparaît tel quel dans les identifiants (`PRD00001`).

3. **Migrations** — `python manage.py makemigrations <app>` pour le
   modèle, puis ajouter la migration `RunSQL` de la séquence à la main
   (voir `apps/ventes/migrations/0002_reference_sequences.py`). Terminer
   par `python manage.py migrate`.

4. **Admin** (optionnel mais recommandé, pratique pour inspecter/modifier
   des données sans passer par l'API) :

   ```python
   # apps/ventes/admin/product_admin.py
   from django.contrib import admin
   from apps.ventes.models import Product
   admin.site.register(Product)
   ```

   L'exporter dans `apps/ventes/admin/__init__.py`.

5. **Factory** (pour les tests) — voir `apps/ventes/factories.py`,
   pattern `factory_boy` classique.

---

## 2. Signaux (optionnel — quand une action déclenche un effet ailleurs)

Un signal ne devient utile que si **la sauvegarde/suppression d'un
modèle doit automatiquement en affecter un autre**, sans que
l'appelant (viewset, admin, shell) ait à le savoir. Exemple actuel :
créer/modifier/supprimer une `VenteLigne` doit recalculer
`Vente.total` — plutôt que d'ajouter cet appel dans chaque endroit qui
manipule des lignes (viewset, admin, script de migration de données...),
un signal le fait une seule fois, pour tous les appelants.

Chaque modèle émetteur a son propre fichier, comme pour
`filters/`/`admin/` :

```python
# apps/ventes/signals/vente_ligne_signals.py
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from apps.ventes.models import VenteLigne

@receiver(post_save, sender=VenteLigne)
def recalculate_total_on_save(sender, instance, **kwargs):
    instance.vente.recalculate_total()

@receiver(post_delete, sender=VenteLigne)
def recalculate_total_on_delete(sender, instance, **kwargs):
    instance.vente.recalculate_total()
```

`apps/ventes/signals/__init__.py` importe chaque `<entite>_signals.py`
(l'import suffit à enregistrer les `@receiver`, pas besoin de les
ré-exporter) :

```python
from apps.ventes.signals import vente_ligne_signals  # noqa: F401
```

Et `apps.py` importe le **package** `signals` une seule fois, dans
`ready()` — Django appelle `ready()` après que tous les modèles de toutes
les apps soient chargés, ce qui évite les imports circulaires que l'on
aurait en import du signal directement dans le modèle :

```python
class VentesConfig(AppConfig):
    name = 'apps.ventes'
    def ready(self):
        from apps.ventes import signals  # noqa: F401
```

Ne pas créer `signals/` tant qu'un seul modèle de l'app n'a besoin d'un
signal — un fichier plat `signals.py` (comme actuellement dans
`apps.accounts`, qui n'en a aucun) suffit ; ne le transformer en package
que lorsqu'un deuxième modèle en a besoin.

---

## 3. Le serializer

```python
# apps/ventes/serializers/product_serializer.py
from rest_framework import serializers
from apps.ventes.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'default_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
```

**Toujours inclure `created_at`/`updated_at`** dans `fields` (en lecture
seule) dès que le modèle hérite de `TimestampedModel`/`AuditedModel` —
même si rien ne les affiche encore côté frontend. Oubli réel rencontré
sur ce projet : `ProductSerializer` ne les exposait pas, et une colonne
"Created" ajoutée plus tard côté frontend s'est retrouvée vide alors que
la donnée existait bien en base (voir `TODO.md`, entrée "Bug corrigé").

L'exporter dans `apps/ventes/serializers/__init__.py`.

---

## 4. Filtres — quand et où

Le viewset (§ 5) déclare déjà `search_fields`/`ordering_fields` : ce sont
de **simples listes de noms de champs**, sans logique, donc elles restent
toujours inline dans le viewset — pas besoin d'un fichier séparé pour ça.

Un fichier dédié dans `filters/<entite>_filters.py` ne devient nécessaire
que lorsqu'un filtre a besoin d'une vraie classe avec du code : filtre par
intervalle (dates, nombres), ou filtre multi-valeurs (`?champ=a,b`).

- **Filtre multi-valeurs** — réutiliser `CharInFilter` (déjà défini dans
  `apps/core/filters.py`, partagé par toute l'API) : accepte une liste
  séparée par des virgules et l'applique en lookup `__in`.

  ```python
  # apps/ventes/filters/vente_filters.py
  from django_filters import rest_framework as filters
  from apps.core.filters import CharInFilter
  from apps.ventes.models import Vente

  class VenteFilterSet(filters.FilterSet):
      status = CharInFilter(field_name='status')

      class Meta:
          model = Vente
          fields = ['status', 'customer']
  ```

- **Filtre par intervalle** — deux `DateFilter`/`NumberFilter` avec
  `lookup_expr='gte'`/`'lte'`, nommés explicitement `<champ>_min`/
  `<champ>_max` (plutôt que le suffixe par défaut de
  `DateFromToRangeFilter`) pour que le nom du paramètre soit prévisible
  côté frontend :

  ```python
  # apps/ventes/filters/product_filters.py
  from django_filters import rest_framework as filters
  from apps.ventes.models import Product

  class ProductFilterSet(filters.FilterSet):
      created_at_min = filters.DateFilter(field_name='created_at', lookup_expr='gte')
      created_at_max = filters.DateFilter(field_name='created_at', lookup_expr='lte')

      class Meta:
          model = Product
          fields = ['created_at_min', 'created_at_max']
  ```

  Exporter les deux dans `apps/ventes/filters/__init__.py`
  (`from apps.ventes.filters.product_filters import ProductFilterSet`, etc.).

- **Filtre sur une relation M2M** (ex. filtrer `User` par nom de rôle) —
  même `CharInFilter`, avec un `field_name` traversant la relation
  (`roles__name`), **et** ajouter `.distinct()` sur le queryset du
  viewset (une jointure M2M peut dupliquer les lignes) :

  ```python
  # apps/accounts/filters.py
  class UserFilterSet(filters.FilterSet):
      roles = CharInFilter(field_name='roles__name')
      class Meta:
          model = User
          fields = ['roles']
  ```

  (Ici un seul fichier plat suffit — `apps/accounts/filters.py` — car il
  n'y a qu'une seule entité filtrable de cette façon dans `accounts`. Le
  package `filters/` de `apps/ventes/` existe seulement parce que Product
  *et* Vente en ont chacun un.)

**Ne jamais mettre cette logique dans le modèle** : un `FilterSet` se
construit à partir de `request.GET`, un concept HTTP — le modèle doit
rester utilisable hors contexte API (admin, commande shell, signal) sans
dépendre de DRF/django-filter.

---

## 5. Le viewset

Un `ModelViewSet` DRF standard suffit, avec `HasRolePermission` comme
unique classe de permission :

```python
# apps/ventes/views/product_viewset.py
from rest_framework import viewsets
from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import ProductFilterSet
from apps.ventes.models import Product
from apps.ventes.serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [HasRolePermission]
    filterset_class = ProductFilterSet          # seulement si un FilterSet dédié existe (§ 4)
    search_fields = ['name', 'sku']             # active ?search=
    ordering_fields = ['name', 'default_price', 'created_at']  # active ?ordering=
```

Si la ressource n'a besoin que de recherche/tri (pas de filtre par
intervalle ni multi-valeurs), omettre simplement `filterset_class` — voir
`CustomerViewSet`, qui n'en a pas.

**Comment `HasRolePermission` sait quelle permission exiger** — elle
déduit le `codename` Django à partir de l'action DRF et du modèle du
serializer, aucune configuration supplémentaire à écrire :

| Action DRF | Permission requise (`<action>_<model_name>`) | Méthode HTTP |
|---|---|---|
| `list` / `retrieve` | `view_product` | GET |
| `create` | `add_product` | POST |
| `update` / `partial_update` | `change_product` | PUT / PATCH |
| `destroy` | `delete_product` | DELETE |
| action custom (`@action`) | `change_product` par défaut | selon la méthode déclarée |

Ces 4 permissions (`add_product`, `view_product`, `change_product`,
`delete_product`) sont **créées automatiquement par Django** dès que le
modèle existe (post-migration) — pas besoin de les déclarer à la main. Un
utilisateur y a accès si **au moins un de ses rôles** possède la
permission (`user.roles.filter(permissions__codename=...)`).

### 5.1. Endpoint custom (pas du CRUD standard)

Le CRUD de base (`list`/`create`/`retrieve`/`update`/`destroy`) vient
gratuitement de `ModelViewSet` — rien à écrire pour ça. Pour une action
métier en plus (ex. changer le statut d'une Vente), ajouter une méthode
décorée `@action` sur le viewset :

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class VenteViewSet(viewsets.ModelViewSet):
    ...
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        vente = self.get_object()
        try:
            vente.validate_vente()          # transition django-fsm, voir modèle
        except TransitionNotAllowed:
            return Response({'detail': "..."}, status=400)
        vente.save(update_fields=['status', 'updated_at'])
        return Response(VenteSerializer(vente, context={'request': request}).data)
```

- `detail=True` route vers `POST /api/<ressource>/{id}/valider/` (agit
  sur une instance) ; `detail=False` vers `POST /api/<ressource>/valider/`
  (agit sur la collection). Le nom de la méthode devient le dernier
  segment de l'URL.
- Pas besoin de toucher `urls.py` — le `DefaultRouter` détecte les
  `@action` automatiquement.
- Si la transition d'état est gérée par **django-fsm**
  (`@transition(field=status, source=..., target=...)` sur le modèle,
  voir `Vente.validate_vente`/`Vente.cancel_vente`), toujours encadrer
  l'appel d'un `try/except TransitionNotAllowed` — la transition lève
  cette exception si l'état actuel ne le permet pas (ex. annuler une
  vente qui est encore en brouillon).
- Par défaut, `HasRolePermission` exige `change_<model>` pour une action
  custom (voir tableau ci-dessus) — remplaçable en surchargeant
  `get_permissions()` sur le viewset si l'action a besoin d'une
  permission différente.

Exemple réel complet : `apps/ventes/views/vente_viewset.py` (`valider`/
`annuler`).

---

## 6. Pagination

Rien à déclarer dans le viewset : la pagination est **globale**, appliquée
automatiquement à toute l'API par `config/settings.py` :

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsPagination',
    ...
}
```

`StandardResultsPagination` (`apps/core/pagination.py`) laisse le client
choisir `page_size` via `?page_size=` (plafonné à 100 par
`max_page_size`) — la classe par défaut de DRF ignore ce paramètre sinon.
Ne redéfinir `pagination_class` dans un viewset que si cette ressource a
besoin d'un comportement **différent** du défaut (aucune ressource
actuelle n'en a besoin).

---

## 7. Enregistrer les routes

```python
# apps/ventes/urls.py
from rest_framework.routers import DefaultRouter
from apps.ventes.views import ProductViewSet, VenteViewSet

router = DefaultRouter()
router.register('ventes', VenteViewSet, basename='vente')
router.register('products', ProductViewSet, basename='product')
urlpatterns = router.urls
```

Puis vérifier que `config/urls.py` inclut bien
`path('api/', include('apps.ventes.urls'))` (déjà le cas si le modèle vit
dans une app déjà branchée — sinon voir § 0).

---

## 8. Donner la permission aux rôles par défaut

Sans cette étape, la ressource existe mais **personne n'y a accès** tant
qu'un admin ne configure pas manuellement la matrice de permissions
(`/api/roles/`, voir `GUIDE_UTILISATION.md` côté frontend). Pour la
seeder par défaut à la création du modèle, ajouter le couple
`(app_label, model_name)` dans la migration de données correspondante
(voir `apps/accounts/migrations/0006_seed_role_permissions.py`, variable
`targets`) :

```python
targets = [
    ('accounts', 'customer'),
    ('ventes', 'product'),
    ('ventes', 'vente'),
    ('ma_nouvelle_app', 'ma_nouvelle_ressource'),  # à ajouter
]
```

`roles`/`users` (gestion des rôles eux-mêmes) restent en dehors de ce
mécanisme générique : protégés par `IsAdminRole` (vérifie directement
`role.name == 'admin'`), pas par les permissions par modèle — voir
`RoleViewSet`/`UserViewSet`.

---

## 9. Exposer les métadonnées (optionnel)

Utilisé pour l'introspection `GET /api/meta/<resource>/` — ajouter le
serializer dans `RESOURCE_SERIALIZER_MAP` d'`apps/core/views.py`.

---

## 10. Tests

Voir `apps/accounts/tests.py`/`apps/ventes/tests.py` pour le pattern :
pytest-django + `factory_boy` + `User.objects.create_user(...)` +
assignation de rôle en dur pour tester les permissions par cas (24 tests
au total actuellement). Commandes CI à lancer en local avant de pousser :

```bash
ruff check .
python manage.py makemigrations --check --dry-run
python -m pytest -q
```

---

Une fois tout ça en place côté backend, la ressource est immédiatement
utilisable côté frontend en suivant `GUIDE_DEVELOPPEUR.md` du dépôt
`poc-vente-front` (`api.ts`/`hooks.ts` pointant vers les nouveaux
endpoints `/api/<ressource>/`, filtres/tri/pagination consommant les
paramètres exposés ici).
