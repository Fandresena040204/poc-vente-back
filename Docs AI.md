# Docs AI

Voici la liste complète et détaillée, backend et frontend, pour l'architecture avec **modèles Django explicites** (sans moteur d'entités génériques) et **React + TanStack** côté front.

***

# PARTIE BACKEND — Django + DRF

## 1. Fondations Django

**Structure multi-app** Django encourage un découpage en apps indépendantes plutôt qu'un monolithe. Structure typique :

* `apps/core` : utilitaires transverses, mixins de modèles réutilisables (ex: un `TimestampedModel` avec `created_at`/`updated_at` que tous les autres modèles héritent)
* `apps/accounts` : utilisateurs, rôles, authentification
* `apps/invoicing`, `apps/crm`, `apps/inventory`... : une app par domaine métier, chacune avec ses propres `models.py`, `serializers.py`, `views.py`
* `apps/workflow` : machines à états, approbations transverses
* `config/` : settings, URLs racine, configuration WSGI/ASGI

Ce découpage isole les responsabilités : modifier la logique de facturation ne touche pas le code CRM. Chaque app est aussi testable indépendamment.

**Configuration multi-environnement**`django-environ` charge la configuration depuis des variables d'environnement plutôt que du code en dur. Un seul `settings.py` lit `DATABASE_URL`, `SECRET_KEY`, `DEBUG` etc. depuis un fichier `.env` (différent par environnement : dev, staging, prod). Évite la duplication de fichiers de settings qui divergent avec le temps, et évite de committer des secrets dans le code.

**PostgreSQL** Base de données recommandée pour ce type de projet (comme discuté précédemment) : contraintes d'intégrité solides, JSON natif (`JSONField`) pour les cas où un peu de flexibilité reste utile sans tout généraliser, performances de recherche full-text natives.

**CORS**`django-cors-headers` autorise explicitement le domaine React à consommer l'API Django, puisque les deux tournent sur des origines différentes (ports différents en dev, sous-domaines différents en prod). Sans ça, le navigateur bloque les requêtes par la politique same-origin.

***

## 2. Modèles Django (le cœur du système, version explicite)

**Un modèle par objet métier** Chaque type de donnée (Facture, Client, Produit, Commande...) est une classe Python héritant de `models.Model`, avec ses champs déclarés explicitement :

```python
class Invoice(TimestampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)

```

**Mixins réutilisables** Pour éviter de répéter les mêmes champs partout (dates de création/modification, utilisateur créateur, soft-delete), on définit des classes abstraites réutilisables :

```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class AuditedModel(TimestampedModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    class Meta:
        abstract = True

```

Tout modèle métier hérite de ces classes pour bénéficier automatiquement de ces champs, sans duplication.

**Relations natives**`ForeignKey`, `ManyToManyField`, `OneToOneField` — les relations sont de vraies contraintes SQL (clé étrangère réelle en base), avec intégrité référentielle garantie par PostgreSQL lui-même (impossible de créer une facture pointant vers un client inexistant). C'est un avantage direct par rapport à un système générique où les liens sont souvent de simples IDs stockés sans contrainte.

**Modèles enfants (tables liées)** Pour les structures type "facture + lignes de facture", on utilise une relation `ForeignKey` classique depuis le modèle enfant vers le parent :

```python
class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

```

**Migrations**`python manage.py makemigrations` détecte automatiquement les changements de modèles et génère les fichiers de migration ; `migrate` les applique. Chaque migration est versionnée dans le code (committée en Git), ce qui permet de savoir exactement quel changement de schéma a eu lieu, quand, et de revenir en arrière si besoin (`migrate app_name 0004` pour redescendre à une version antérieure).

***

## 3. Sérialiseurs DRF explicites

**Un&#x20;****`ModelSerializer`****&#x20;par modèle**

```python
class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'status', 'total', 'due_date', 'created_at']
        read_only_fields = ['status', 'created_at']

```

DRF génère automatiquement les champs de sérialisation à partir des champs du modèle (type, requis, longueur max...), mais le développeur garde le contrôle total et explicite sur ce qui est exposé.

**Validation custom** Toute règle de validation qui dépasse les contraintes basiques du modèle s'écrit directement dans le sérialiseur, de façon lisible et testable unitairement :

```python
def validate_due_date(self, value):
    if value and value < timezone.now().date():
        raise serializers.ValidationError("La date d'échéance ne peut pas être dans le passé.")
    return value

def validate(self, data):
    # validation croisée entre plusieurs champs
    ...

```

**Sérialiseurs imbriqués** Pour représenter une facture avec ses lignes dans une seule réponse JSON, DRF permet d'imbriquer un sérialiseur dans un autre :

```python
class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)

```

**Sérialiseurs différents selon le contexte** Rien n'empêche d'avoir un `InvoiceListSerializer` (léger, pour les listes) et un `InvoiceDetailSerializer` (complet, avec les lignes imbriquées) pour la même ressource — pratique courante en DRF pour optimiser la taille des réponses selon le besoin réel de la vue.

***

## 4. ViewSets et routing explicites

**Un&#x20;****`ModelViewSet`****&#x20;par ressource**

```python
class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, InvoicePermission]
    filterset_fields = ['status', 'customer']
    search_fields = ['reference', 'customer__name']
    ordering_fields = ['created_at', 'due_date', 'total']

    def get_queryset(self):
        return Invoice.objects.select_related('customer').prefetch_related('lines')

```

`select_related`/`prefetch_related` optimisent les requêtes SQL en évitant le problème classique des "N+1 requêtes" (une requête par ligne au lieu d'une seule requête globale avec jointure).

**Actions custom** Pour des opérations qui dépassent le CRUD standard (ex: approuver une facture), DRF permet d'ajouter des actions dédiées :

```python
@action(detail=True, methods=['post'])
def approve(self, request, pk=None):
    invoice = self.get_object()
    invoice.approve()  # méthode métier sur le modèle ou via django-fsm
    return Response(InvoiceSerializer(invoice).data)

```

Ça devient un endpoint `POST /api/invoices/{id}/approve/`.

**Router**

```python
router = DefaultRouter()
router.register('invoices', InvoiceViewSet, basename='invoice')
router.register('customers', CustomerViewSet, basename='customer')

```

Génère automatiquement toutes les routes CRUD standard (`GET/POST /invoices/`, `GET/PUT/PATCH/DELETE /invoices/{id}/`) pour chaque ressource enregistrée.

***

## 5. Endpoint de métadonnées basé sur introspection (pas de table de config dynamique)

**Le principe** Même en approche explicite, garder un endpoint qui décrit la structure d'une ressource reste très utile pour piloter un frontend générique. La différence fondamentale avec l'approche précédente : ce schéma est **dérivé du code existant** (le sérialiseur DRF), pas stocké dans une table de configuration séparée.

**Option native :&#x20;****`OPTIONS`** DRF répond nativement à une requête `OPTIONS` sur n'importe quel endpoint avec la description des champs :

```python
OPTIONS /api/invoices/

```

renvoie un JSON avec les champs, leurs types, s'ils sont requis, leurs choix (`choices`) le cas échéant — dérivé automatiquement du `ModelSerializer`.

**Option custom, plus riche** Si `OPTIONS` ne suffit pas (besoin de labels traduits, d'ordre d'affichage, de groupement de champs en sections), on écrit un petit endpoint qui introspecte la classe du sérialiseur :

```python
class MetaView(APIView):
    def get(self, request, resource):
        serializer_class = RESOURCE_SERIALIZER_MAP[resource]  # mapping explicite et fini
        fields_meta = []
        for name, field in serializer_class().fields.items():
            fields_meta.append({
                'name': name,
                'type': field.__class__.__name__,
                'required': field.required,
                'read_only': field.read_only,
                'label': field.label,
            })
        return Response({'fields': fields_meta})

```

**L'avantage clé**`RESOURCE_SERIALIZER_MAP` est un dictionnaire fini et explicite (`{'invoices': InvoiceSerializer, 'customers': CustomerSerializer}`), pas une table en base qui peut se désynchroniser. Le schéma renvoyé au frontend ne peut jamais mentir sur le vrai comportement de l'API, puisqu'il est calculé à partir du même code qui traite réellement les requêtes.

***

## 6. Authentification et permissions

**JWT**`djangorestframework-simplejwt` : *access token* de courte durée pour chaque requête API, *refresh token* de longue durée pour en obtenir un nouveau sans redemander les identifiants. Standard pour une SPA découplée du backend.

**Permissions par modèle** Automatiquement disponibles pour de vrais modèles Django : `add_invoice`, `change_invoice`, `delete_invoice`, `view_invoice`, générées à la migration. On les vérifie via `permission_classes` sur chaque ViewSet, ou via des permissions custom (`InvoicePermission`) qui encodent des règles métier plus fines (ex: seul le créateur ou un manager peut modifier une facture soumise).

**Permissions par objet**`django-guardian` s'applique directement et nativement sur vos modèles réels — pas d'adaptation nécessaire comme ce serait le cas avec un système d'entités génériques. On peut attribuer `view_invoice` à un utilisateur précis sur une instance précise (`assign_perm('view_invoice', user, invoice_instance)`).

**Permissions par champ** Toujours à coder manuellement (aucune lib générique ne le fait proprement), mais plus simple ici car les champs sont connus et fixes à l'avance :

```python
def to_representation(self, instance):
    data = super().to_representation(instance)
    if not self.context['request'].user.has_perm('invoicing.view_total', instance):
        data.pop('total', None)
    return data

```

**Rôles et groupes**`django.contrib.auth.models.Group` pour des rôles simples. `django-rules` si vous avez besoin de règles de permission déclaratives et conditionnelles (ex: "un manager peut approuver une facture seulement si son montant est inférieur à X").

**Rate limiting** Throttling natif DRF (`UserRateThrottle`, `AnonRateThrottle`, ou une classe custom) pour limiter le nombre de requêtes par utilisateur/IP dans une fenêtre de temps donnée.

***

## 7. Workflow et logique métier

**Machines à états (****`django-fsm`****)**

```python
class Invoice(models.Model):
    status = FSMField(default='draft')

    @transition(field=status, source='draft', target='submitted')
    def submit(self):
        ...

    @transition(field=status, source='submitted', target='approved')
    def approve(self):
        ...

```

Empêche structurellement les transitions invalides (impossible d'appeler `approve()` depuis l'état `draft`) — la cohérence est garantie par le code, pas par une convention que chaque développeur doit respecter manuellement.

**Workflows multi-étapes (****`django-viewflow`****)** Pour des processus impliquant plusieurs utilisateurs successifs (validation manager → validation finance), avec suivi d'avancement et affectation automatique de tâches aux bons utilisateurs à chaque étape.

**Signaux Django**

```python
@receiver(post_save, sender=InvoiceLine)
def recalculate_invoice_total(sender, instance, **kwargs):
    instance.invoice.recalculate_total()

```

Déclenche automatiquement de la logique métier à certains événements du cycle de vie d'un modèle, sans coupler explicitement le code qui déclenche l'événement à celui qui réagit.

**Pas de scripts custom exécutables** Contrairement à l'approche générique, ici toute la logique métier est du vrai code Python versionné — pas besoin (ni possibilité) d'un mécanisme de scripts dynamiques exécutés à l'exécution. C'est plus sûr (pas de risque d'exécution de code arbitraire) et plus simple à déboguer.

***

## 8. Tâches asynchrones

**Celery** Exécute du travail hors du cycle requête/réponse HTTP (envoi d'email de confirmation, génération de PDF volumineux, traitement d'un import de masse). Nécessite un broker de messages (Redis généralement) et des processus *workers* séparés qui consomment la file de tâches.

**`django-celery-beat`** Planifie des tâches récurrentes (relances automatiques de factures impayées chaque nuit, par exemple), configurable depuis l'admin Django plutôt que codé en dur dans un fichier de config statique.

**`django-celery-results`** Persiste le résultat et l'état de chaque tâche exécutée en base de données, consultable a posteriori.

**Endpoint de suivi** Un endpoint DRF exposant l'état d'une tâche en cours (`pending`/`running`/`success`/`failed`), pour que le frontend puisse afficher une progression, via polling régulier ou WebSocket.

***

## 9. Temps réel

**Django Channels** Étend Django pour supporter les WebSockets (au-delà du simple HTTP requête/réponse), nécessaire pour du push serveur → client sans que le client ait à interroger constamment le serveur.

**Groupes de canaux** Permet de cibler précisément qui reçoit quel message (ex: seuls les utilisateurs consultant actuellement une facture précise reçoivent la notification que quelqu'un d'autre vient de la modifier), plutôt que de diffuser à tout le monde.

***

## 10. Import/export et fichiers

**`django-import-export`** Définit comment un fichier CSV/Excel se mappe vers un modèle Django précis, avec prévisualisation et gestion d'erreur ligne par ligne avant validation définitive de l'import.

**`django-storages`** Abstrait le stockage de fichiers (pièces jointes, PDF générés) pour utiliser un service cloud (S3 ou équivalent) plutôt que le disque local — indispensable dès qu'on veut plusieurs serveurs web en parallèle, qui ne partagent pas de disque.

***

## 11. Rapports et impression

**Agrégations natives Django**

```python
Invoice.objects.filter(status='paid').aggregate(total=Sum('total'))
Invoice.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('total'))

```

Permet de construire des endpoints de reporting (totaux, moyennes, regroupements par période) directement en SQL généré par l'ORM, sans sortir de Django.

**WeasyPrint** Convertit un template HTML/CSS en PDF — utile pour générer une facture imprimable ou un bon de commande à partir d'un template Django classique.

***

## 12. Multi-tenancy (si applicable)

**`django-tenants`** Isole les données de chaque organisation cliente via des schémas PostgreSQL distincts, avec une seule installation applicative partagée. Chaque modèle métier reste défini une seule fois dans le code, mais les données sont physiquement séparées par tenant.

***

## 13. Tests et qualité

**`pytest-django`** Framework de test plus ergonomique que le `TestCase` natif de Django pour la majorité des équipes (fixtures, paramétrage de tests plus simples).

**Factory Boy**

```python
class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invoice
    customer = factory.SubFactory(CustomerFactory)
    status = InvoiceStatus.DRAFT

```

Génère des données de test cohérentes automatiquement, directement liées à un modèle réel — plus simple qu'avec un système d'entités génériques où il faudrait aussi simuler des définitions dynamiques dans les tests.

**CI (intégration continue)** Pipeline (GitHub Actions par exemple) qui à chaque push : lance le linter (`ruff`), exécute les tests, vérifie l'absence de migration manquante (`makemigrations --check`).

***

# PARTIE FRONTEND — React + TanStack

## 1. TanStack Query (gestion des données serveur)

**Configuration du&#x20;****`QueryClient`** Centralise `staleTime` (durée avant qu'une donnée soit considérée périmée), `gcTime` (durée de conservation en cache après non-utilisation), et la stratégie de retry en cas d'échec réseau.

**Hooks par ressource (semi-génériques)** Plutôt qu'un système 100% générique par "entité dynamique", on paramètre par **endpoint connu et fini** :

```tsx
function useInvoiceList(filters) {
  return useQuery({
    queryKey: ['invoices', filters],
    queryFn: () => api.get('/invoices/', { params: filters }),
  });
}

```

On peut factoriser un hook générique sous-jacent (`useResourceList(endpoint, filters)`) réutilisé par tous les hooks spécifiques, tout en gardant la possibilité d'ajouter une logique propre à une ressource particulière (filtre par défaut métier, transformation de données spécifique) sans casser le pattern générique.

**Mutations avec invalidation de cache**

```tsx
function useCreateInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.post('/invoices/', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });
}

```

Après création, la liste des factures en cache est automatiquement invalidée et se rafraîchit, sans code de synchronisation manuel.

**Updates optimistes** Pour les actions fréquentes (changer un statut, cocher une case), on met à jour l'affichage immédiatement avant confirmation serveur, avec rollback automatique en cas d'échec — améliore la perception de réactivité.

**Infinite queries**`useInfiniteQuery` pour le chargement progressif de listes longues (scroll infini), évite de recharger l'intégralité de la liste à chaque nouvelle page.

***

## 2. TanStack Table (vues liste/rapport)

**Composant de liste piloté par les métadonnées d'introspection**

```tsx
function InvoiceListView() {
  const { data: meta } = useResourceMeta('invoices');
  const { data: invoices } = useInvoiceList(filters);
  const columns = useMemo(() => buildColumnsFromMeta(meta), [meta]);
  // rendu avec useReactTable de TanStack Table
}

```

Les colonnes sont dérivées du même endpoint de métadonnées basé sur introspection DRF décrit en partie backend — donc toujours synchronisées avec la vraie forme de l'API.

**Tri, filtres, pagination côté serveur** L'état de tri/filtre de TanStack Table pilote les query params envoyés à DRF (`?ordering=-due_date&status=paid`) ; c'est Django/PostgreSQL qui fait le travail lourd de tri/filtre, pas le navigateur — indispensable dès que le volume de données dépasse quelques centaines de lignes.

**Colonnes configurables par utilisateur** Sauvegarde de la préférence de colonnes affichées/ordre, en base (table `UserPreference`) ou en local storage selon le besoin de persistance cross-device.

**Sélection multiple et actions en masse** TanStack Table gère la sélection de lignes nativement ; il faut construire la barre d'action contextuelle qui apparaît quand une sélection existe (supprimer, exporter, changer de statut en masse via l'action custom `@action` DRF évoquée plus haut).

***

## 3. TanStack Router (navigation)

**Routes par ressource connue**

```tsx
const invoiceListRoute = createRoute({
  path: '/invoices',
  component: InvoiceListView,
});
const invoiceDetailRoute = createRoute({
  path: '/invoices/$invoiceId',
  component: InvoiceDetailView,
});

```

Contrairement à l'approche générique (`/:entite`), ici les routes correspondent à des ressources précises et connues à l'avance — plus explicite, plus facile à raisonner, avec un typage complet des paramètres.

**Typage fort** TanStack Router valide les paramètres de route à la compilation (ex: `invoiceId` est garanti être une string, avec autocomplétion sur les routes existantes) — réduit les erreurs de navigation par rapport à React Router classique.

**Guards de route** Vérification des permissions avant d'afficher une route (`beforeLoad`), en s'appuyant sur les informations de permission déjà chargées côté utilisateur courant, avec redirection si non autorisé.

***

## 4. TanStack Form (formulaires dynamiques ou semi-dynamiques)

**Génération depuis l'introspection** Le composant `<DynamicForm resource="invoices" />` reste pertinent : il lit le schéma exposé par l'endpoint de métadonnées basé sur introspection DRF, et génère un champ adapté pour chaque champ du sérialiseur (texte, select depuis `choices`, date, lien via `PrimaryKeyRelatedField`...).

**Mapping type de champ → composant** Un dictionnaire de correspondance à construire une fois :

```tsx
const FIELD_COMPONENT_MAP = {
  CharField: TextInput,
  IntegerField: NumberInput,
  ChoiceField: SelectInput,
  DateField: DateInput,
  PrimaryKeyRelatedField: LinkSearchInput,
};

```

**Validation synchronisée** Les règles basiques (requis, longueur, format) dérivées de l'introspection sont interprétées côté React par TanStack Form pour un feedback immédiat, tout en gardant la validation Django comme rempart définitif — ne jamais faire confiance uniquement au frontend pour la sécurité des données.

**Champs conditionnels** Si un champ ne doit apparaître que sous certaines conditions (ex: "raison du rejet" visible seulement si `status === 'rejected'`), cette logique reste à coder explicitement dans le composant du formulaire concerné (moins générique qu'avec un système de métadonnées dynamique complet, mais plus simple à tracer puisqu'un formulaire correspond à une ressource connue).

**Composant "lien" réutilisable** Un composant d'autocomplete/recherche générique, réutilisé par tous les champs de type relation (`customer` sur une facture, `product` sur une ligne de facture), qui interroge l'endpoint de la ressource liée.

**Composant table enfant** Pour les lignes de facture ou toute relation "un vers plusieurs" éditable inline : tableau avec ajout/suppression de lignes, intégré dans le formulaire parent, synchronisé avec le sérialiseur imbriqué côté DRF.

***

## 5. Composants transverses

**Vues multiples** Composants génériques réutilisables (Kanban, Calendrier) activables par ressource selon ses besoins métier — un Kanban de factures groupées par statut, un calendrier de commandes groupées par date de livraison. Le composant reste générique, seule la configuration (quel champ groupe, quel champ date) change par ressource.

**Moteur de permission côté UI** Utilise les informations de permission renvoyées par l'API (soit dans la réponse de la ressource elle-même, soit via un endpoint dédié) pour masquer/désactiver des champs et actions non autorisés — améliore l'UX, mais le serveur reste la seule vraie barrière de sécurité.

**Gestion de l'authentification** Stockage du token en mémoire ou cookie httpOnly (éviter localStorage pour limiter le risque XSS), rafraîchissement automatique avant expiration, déconnexion propre en cas d'échec de refresh.

**Notifications temps réel** Abonnement WebSocket (Django Channels), avec mise à jour ciblée du cache TanStack Query correspondant quand une notification indique qu'une donnée affichée a changé côté serveur (`queryClient.invalidateQueries` déclenché par un message WebSocket).

***

## 6. Outillage complémentaire

**État global léger** TanStack Query couvre l'essentiel du state serveur. Pour l'état purement client (thème, panneau latéral ouvert/fermé, préférences d'affichage), Zustand est une option légère et simple, ou le Context API natif si les besoins restent limités.

**Design system** Radix UI (primitives accessibles) + Tailwind CSS, ou directement shadcn/ui, pour construire rapidement des composants cohérents (boutons, modales, selects) sans tout reconstruire à la main.

***

## Tableau récapitulatif de ce qui a changé vs l'approche générique

| Brique                  | Avant (entités génériques)                 | Maintenant (modèles explicites)                           |
| ----------------------- | ------------------------------------------ | --------------------------------------------------------- |
| Définition de structure | Table `EntityDefinition`/`FieldDefinition` | Fichiers `models.py` par app                              |
| Stockage des données    | Table dynamique ou EAV                     | Vraies tables SQL par modèle                              |
| ViewSet/Sérialiseur     | Générés dynamiquement à l'exécution        | Écrits explicitement par ressource                        |
| Endpoint de métadonnées | Lit une table de config                    | Introspecte le sérialiseur DRF existant                   |
| Ajout d'une ressource   | Sans code (formulaire)                     | Modèle + migration + sérialiseur + viewset                |
| Frontend générique      | Oui, piloté par entité dynamique           | Oui, piloté par introspection (même niveau de généricité) |

## Ordre de priorité recommandé

1. **Modèles Django + migrations** pour les premières ressources métier
2. **Sérialiseurs et ViewSets DRF** correspondants, avec permissions de base
3. **Endpoint d'introspection de métadonnées** (même simple au départ, juste `OPTIONS` natif)
4. **TanStack Query + Router** : CRUD basique bout en bout sur une première ressource
5. **`<DynamicForm>`****&#x20;générique** basé sur l'introspection, testé sur cette première ressource
6. **TanStack Table générique**, même principe
7. **Répliquer le pattern** sur les ressources suivantes (devrait aller vite une fois le socle validé)
8. **Workflow, Celery, temps réel, reporting** une fois le CRUD de base stable

Voulez-vous qu'on détaille maintenant un exemple concret complet — par exemple l'implémentation bout en bout d'une ressource "Invoice" (modèle → sérialiseur → viewset → hooks TanStack Query → DynamicForm), pour avoir un template réutilisable pour les ressources suivantes ?

