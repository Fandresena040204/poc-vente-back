# Guide développeur

Ce guide explique comment étendre l'application : ajouter un menu, une
page (liste + saisie), une route côté frontend, ou une nouvelle ressource
côté backend (modèle, serializer, viewset). Il est **dupliqué à
l'identique** dans les deux dépôts (`poc-vente-front` et
`poc-vente-back`) puisqu'il couvre les deux — modifie-le dans les deux si
tu le mets à jour.

Pour l'installation et le lancement, voir `README.md` de chaque dépôt.
Pour l'utilisation de l'app une fois connecté, voir `GUIDE_UTILISATION.md`
(frontend uniquement).

Les exemples reprennent la ressource `Product` (la plus simple des 3 déjà
en place : Customers, Products, Ventes) comme fil rouge — pour une
ressource avec des lignes imbriquées, s'inspirer plutôt de `Vente`/
`VenteLigne`.

---

## Côté frontend

Toutes les features suivent le même découpage dans
`src/features/<resource>/` :

```
src/features/products/
├── api.ts                              # appels axios vers le backend
├── hooks.ts                            # hooks TanStack Query
├── index.tsx                           # page "Liste"
├── saisie.tsx                          # page "Saisie" (create + edit)
├── data/
│   └── schema.ts                       # types + schémas zod
└── components/
    ├── products-provider.tsx           # état du dialog de suppression
    ├── products-dialogs.tsx            # monte le dialog de suppression
    ├── products-primary-buttons.tsx    # bouton "Add Product"
    ├── products-form.tsx               # formulaire (create + edit)
    ├── products-delete-dialog.tsx      # confirmation de suppression
    ├── products-columns.tsx            # colonnes du tableau
    ├── products-table.tsx              # tableau (tri/filtre/pagination)
    └── data-table-row-actions.tsx      # menu ⋮ par ligne
```

### 1. Ajouter un item de menu / sous-menu

La sidebar est définie dans
`src/components/layout/data/sidebar-data.ts`. Chaque groupe (`navGroups`)
contient des items qui sont soit un lien direct (`NavLink`), soit un
sous-menu (`NavCollapsible`, dès qu'il a un tableau `items`) :

```ts
// Lien direct
{ title: 'Settings', url: '/settings', icon: Settings },

// Sous-menu avec deux sous-items (pattern utilisé par Ventes/Products/Customers)
{
  title: 'Products',
  icon: Package,
  items: [
    { title: 'Liste', url: '/products', permission: 'view_product' },
    { title: 'Saisie', url: '/products/saisie', permission: 'add_product' },
  ],
},
```

`permission` (vérifié via `hasPermission`) et `role` (vérifié via
`hasRole`, tous deux depuis `@/stores/auth-store`) sont optionnels, et
peuvent être posés aussi bien sur un item de premier niveau que sur un
sous-item. Un item/sous-item sans l'un ou l'autre est toujours visible.

Le filtrage réel se fait dans `src/components/layout/app-sidebar.tsx`
(`getVisibleNavGroups`) : il retire récursivement les items sans la
permission/le rôle requis, puis retire les groupes devenus vides. Pas
besoin d'y toucher pour un nouvel item — juste déclarer `permission`/
`role` dans `sidebar-data.ts`.

### 2. Ajouter une nouvelle page

#### 2.1. Page "Liste"

1. **`data/schema.ts`** — le type de l'entité + le schéma zod du
   formulaire :

   ```ts
   const _productSchema = z.object({
     id: z.string(), name: z.string(), sku: z.string(),
     default_price: z.string(),
     created_at: z.coerce.date(), updated_at: z.coerce.date(),
   })
   export type Product = z.infer<typeof _productSchema>

   export const productFormSchema = z.object({
     name: z.string().min(1, 'Name is required.'),
     sku: z.string().min(1, 'SKU is required.'),
     default_price: z.string().min(1).regex(/^\d+(\.\d{1,2})?$/),
   })
   export type ProductForm = z.infer<typeof productFormSchema>
   ```

2. **`api.ts`** — les appels HTTP (voir § 4 pour `apiClient`) :

   ```ts
   export async function fetchAllProducts(): Promise<Product[]> { ... }
   export async function createProduct(payload: ProductForm): Promise<Product> { ... }
   export async function updateProduct(id: string, payload: ProductForm): Promise<Product> { ... }
   export async function deleteProduct(id: string): Promise<void> { ... }
   ```

3. **`hooks.ts`** — un hook TanStack Query par opération, avec
   invalidation du cache + toast au succès :

   ```ts
   const PRODUCTS_QUERY_KEY = ['products']

   export function useProducts() {
     return useQuery({ queryKey: PRODUCTS_QUERY_KEY, queryFn: fetchAllProducts })
   }
   export function useCreateProduct() {
     const queryClient = useQueryClient()
     return useMutation({
       mutationFn: (payload: ProductForm) => createProduct(payload),
       onSuccess: () => {
         queryClient.invalidateQueries({ queryKey: PRODUCTS_QUERY_KEY })
         toast.success('Product created.')
       },
     })
   }
   // useUpdateProduct, useDeleteProduct : même pattern
   ```

4. **`components/products-columns.tsx`** — colonnes `ColumnDef[]` pour
   TanStack Table (copier une feature existante et adapter les champs).
   Si une colonne doit résoudre une clé étrangère en libellé (ex. le nom
   du client sur une ligne de vente), en faire une **factory** —
   `createVentesColumns(customerNameById)` — plutôt qu'un tableau statique
   (voir `ventes-columns.tsx`).

5. **`components/products-table.tsx`** — le composant `DataTable`
   (copier depuis une feature existante, `useTableUrlState` synchronise
   déjà tri/pagination/filtres avec l'URL).

6. **`components/products-provider.tsx`** — contexte React minimal, ne
   sert plus qu'à l'état du dialog de suppression (create/edit sont des
   pages, pas des dialogs, depuis la refonte — voir § 2.2) :

   ```ts
   type ProductsDialogType = 'delete'
   // { open, setOpen, currentRow, setCurrentRow } via useDialogState
   ```

7. **`components/products-primary-buttons.tsx`** — bouton "Add Product",
   masqué si pas la permission `add_product`, qui **navigue** vers la
   page de saisie (pas un `setOpen('add')`) :

   ```tsx
   export function ProductsPrimaryButtons() {
     if (!hasPermission('add_product')) return null
     return (
       <Button asChild>
         <Link to='/products/saisie'>Add Product</Link>
       </Button>
     )
   }
   ```

8. **`components/products-delete-dialog.tsx`** — `ConfirmDialog`
   générique (`src/components/confirm-dialog.tsx`) qui demande de retaper
   un champ (nom/SKU/id) avant d'appeler `useDeleteProduct().mutate(id)`.

9. **`components/products-dialogs.tsx`** — monte juste le delete dialog :

   ```tsx
   export function ProductsDialogs() {
     const { open, setOpen, currentRow, setCurrentRow } = useProductsContext()
     return currentRow && (
       <ProductsDeleteDialog
         open={open === 'delete'}
         onOpenChange={() => { setOpen('delete'); setTimeout(() => setCurrentRow(null), 500) }}
         currentRow={currentRow}
       />
     )
   }
   ```

10. **`index.tsx`** — assemble tout (Header + Main + Table), lit
    `search`/`navigate` depuis la route :

    ```tsx
    const route = getRouteApi('/_authenticated/products/')

    export function Products() {
      const search = route.useSearch()
      const navigate = route.useNavigate()
      const { data, isLoading, isError } = useProducts()
      return (
        <ProductsProvider>
          <Main className='flex flex-1 flex-col gap-4 sm:gap-6'>
            <div className='flex flex-wrap items-end justify-between gap-2'>
              <div><h2>Products</h2></div>
              <ProductsPrimaryButtons />
            </div>
            {isLoading ? <Loader2 className='animate-spin' />
              : isError ? <p>Failed to load products.</p>
              : <ProductsTable data={data ?? []} search={search} navigate={navigate} />}
          </Main>
          <ProductsDialogs />
        </ProductsProvider>
      )
    }
    ```

    Le `<Header>` (Search/ThemeSwitch/ConfigDrawer/ProfileDropdown) n'a
    **pas** à être répété ici — il est rendu une seule fois par
    `AuthenticatedLayout` (voir § 3).

##### 2.1.2. Avec les actions (menu ⋮)

`components/data-table-row-actions.tsx` — menu contextuel par ligne,
chaque action conditionnée à sa permission :

```tsx
export function DataTableRowActions({ row }: { row: Row<Product> }) {
  const { setOpen, setCurrentRow } = useProductsContext()
  const canEdit = hasPermission('change_product')
  const canDelete = hasPermission('delete_product')
  if (!canEdit && !canDelete) return null

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild><Button variant='ghost'>⋮</Button></DropdownMenuTrigger>
      <DropdownMenuContent align='end'>
        {canEdit && (
          <DropdownMenuItem asChild>
            <Link to='/products/saisie/$id' params={{ id: row.original.id }}>Edit</Link>
          </DropdownMenuItem>
        )}
        {canDelete && (
          <DropdownMenuItem
            onClick={() => { setCurrentRow(row.original); setOpen('delete') }}
            className='text-red-500!'
          >
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

Edit **navigue** vers la page de saisie (§ 2.2.1) ; seul Delete reste géré
par le provider/dialog. Pour une ressource avec des actions métier
supplémentaires (ex. `Valider`/`Annuler` sur `Vente`), les ajouter ici de
la même façon, conditionnées à leur propre permission et/ou au statut de
la ligne (voir `ventes/components/data-table-row-actions.tsx`).

#### 2.2. Page "Saisie"

1. **`components/products-form.tsx`** — le formulaire lui-même (pas de
   wrapper `Dialog` — c'est une page maintenant), avec ses propres boutons
   Cancel/Save en pied de formulaire :

   ```tsx
   type ProductsFormProps = {
     currentRow?: Product
     onSuccess: () => void
     onCancel: () => void
   }

   export function ProductsForm({ currentRow, onSuccess, onCancel }: ProductsFormProps) {
     const isEdit = !!currentRow
     const createProduct = useCreateProduct()
     const updateProduct = useUpdateProduct()
     const form = useForm<ProductForm>({
       resolver: zodResolver(productFormSchema),
       defaultValues: isEdit ? { name: currentRow.name, sku: currentRow.sku, default_price: currentRow.default_price }
                              : { name: '', sku: '', default_price: '' },
     })

     function onSubmit(values: ProductForm) {
       const mutation = isEdit
         ? updateProduct.mutateAsync({ id: currentRow.id, payload: values })
         : createProduct.mutateAsync(values)
       mutation.then(() => { form.reset(); onSuccess() })
     }

     return (
       <Form {...form}>
         <form onSubmit={form.handleSubmit(onSubmit)} className='max-w-xl space-y-4'>
           {/* FormField par champ, cf. customers-form.tsx / products-form.tsx */}
           <div className='flex justify-end gap-2 pt-2'>
             <Button type='button' variant='outline' onClick={onCancel}>Cancel</Button>
             <Button type='submit'>Save changes</Button>
           </div>
         </form>
       </Form>
     )
   }
   ```

2. **`saisie.tsx`** (à la racine de la feature, pas dans `components/`) —
   la page qui monte Header + Main + le formulaire, et bascule entre
   create/edit selon qu'un id est passé :

   ```tsx
   type ProductsSaisieProps = { productId?: string }

   export function ProductsSaisie({ productId }: ProductsSaisieProps) {
     const navigate = useNavigate()
     const isEdit = !!productId
     const { data, isLoading } = useProducts()
     const currentRow = isEdit ? data?.find((p) => p.id === productId) : undefined

     function goToList() { navigate({ to: '/products' }) }

     return (
       <Main className='flex flex-1 flex-col gap-4 sm:gap-6'>
         <h2>{isEdit ? 'Edit Product' : 'Add New Product'}</h2>
         {isEdit && isLoading ? <Loader2 className='animate-spin' />
           : isEdit && !currentRow ? <p>Product not found.</p>
           : <ProductsForm currentRow={currentRow} onSuccess={goToList} onCancel={goToList} />}
       </Main>
     )
   }
   ```

   **Pourquoi chercher `currentRow` dans `useProducts()`** plutôt que
   d'appeler un endpoint `/products/{id}/` dédié : la liste complète est
   déjà chargée et cachée par TanStack Query (queryKey `['products']`),
   donc pas besoin d'un aller-retour réseau supplémentaire ni d'ajouter
   une fonction `fetchProduct(id)` côté `api.ts`. Si la ressource devient
   trop volumineuse pour tout charger en liste, revoir cette approche.

##### 2.2.1. Avec modification (édition)

L'édition réutilise le **même** composant `ProductsForm` et la **même**
page `ProductsSaisie` que la création — seule la prop `currentRow`
(trouvée via `productId`) change le comportement (`isEdit`). Voir § 3
pour les deux routes nécessaires (`/products/saisie` et
`/products/saisie/$id`).

### 3. Créer les routes (TanStack Router)

Ce projet utilise le **routing par fichiers** de TanStack Router
(`@tanstack/router-plugin/vite`) : chaque fichier sous `src/routes/`
génère une route, et `src/routeTree.gen.ts` est **auto-généré** — ne
jamais l'éditer à la main. Il se régénère automatiquement pendant `pnpm
dev` ou `pnpm build`.

Pour Products, il faut 3 fichiers dans
`src/routes/_authenticated/products/` :

```
products/
├── index.tsx          # "/products"            -> Liste
└── saisie/
    ├── index.tsx       # "/products/saisie"      -> Saisie (create)
    └── $id.tsx         # "/products/saisie/$id"  -> Saisie (edit)
```

```tsx
// products/index.tsx
export const Route = createFileRoute('/_authenticated/products/')({
  validateSearch: productsSearchSchema,   // z.object({ page, pageSize, name })
  component: Products,
})

// products/saisie/index.tsx
export const Route = createFileRoute('/_authenticated/products/saisie/')({
  component: ProductsSaisie,
})

// products/saisie/$id.tsx
export const Route = createFileRoute('/_authenticated/products/saisie/$id')({
  component: RouteComponent,
})
function RouteComponent() {
  const { id } = Route.useParams()
  return <ProductsSaisie productId={id} />
}
```

**Piège rencontré et à éviter absolument** : ne PAS créer `saisie.tsx`
et `saisie.$id.tsx` comme deux fichiers **plats** au même niveau (au lieu
du dossier `saisie/` ci-dessus). TanStack Router interprète la notation
par points comme du **nesting parent/enfant** : `saisie.$id.tsx`
deviendrait un enfant de la route `saisie.tsx`, qui ne rend pas
d'`<Outlet/>` — résultat, la page d'édition affiche silencieusement le
contenu de la page de création (aucune erreur au build, juste un
comportement incorrect au runtime). Utiliser un vrai dossier `saisie/`
avec `index.tsx` + `$id.tsx` comme ci-dessus évite ce nesting implicite.

Après avoir ajouté des fichiers de route, lancer `pnpm dev` au moins une
fois (même quelques secondes) pour que `routeTree.gen.ts` se régénère
avant de lancer `pnpm build` — sinon `tsc` échoue sur des routes qu'il ne
connaît pas encore.

### 4. Liaison vers le backend

- **`src/lib/api-client.ts`** — instance axios unique, `baseURL:
  import.meta.env.VITE_API_BASE_URL` (voir `.env`), intercepteur qui
  ajoute `Authorization: Bearer <access>` et rafraîchit automatiquement le
  token sur un 401 via `/api/token/refresh/` (déconnexion si le refresh
  échoue). Toujours passer par `apiClient`, jamais par un `fetch`/`axios`
  brut, pour bénéficier de ça gratuitement.
- **`src/lib/pagination.ts`** — type `PaginatedResponse<T>` (DRF pagine
  par défaut), et le pattern `fetchAllX()` boucle sur `data.next` pour
  ramener toutes les pages d'un coup (les tables sont paginées côté
  client, pas côté serveur, dans ce POC).
- **`src/stores/auth-store.ts`** (Zustand) — `auth.user` (avec `roles` et
  `permissions`, remontés par `GET /api/auth/me/` au login), et les
  helpers `hasRole('admin')` / `hasPermission('add_product')` utilisés
  partout (sidebar, primary-buttons, row-actions) pour cacher ce que
  l'utilisateur n'a pas le droit de faire. Le nom de permission côté
  frontend est **toujours** `<action>_<modèle>` en minuscules
  (`add_product`, `view_vente`...) — exactement le `codename` Django
  généré automatiquement (voir backend § 2).
- **Garde de route** — `src/routes/_authenticated/route.tsx` redirige
  vers `/sign-in` si pas de token, et vers `/errors/forbidden` sur les
  routes `/users`/`/roles` si l'utilisateur n'a pas le rôle `admin`
  (`beforeLoad`). Pour une nouvelle page réservée à un rôle/une
  permission précise, reproduire ce `beforeLoad` dans son propre fichier
  de route.

---

## Côté backend

Convention du projet : **un fichier par classe**, à la manière Java,
plutôt que des modules `models.py`/`serializers.py`/`views.py`
monolithiques. Chaque package expose ses classes via `__init__.py`.

```
apps/ventes/
├── models/product.py
├── serializers/product_serializer.py
├── views/product_viewset.py
├── admin/product_admin.py
├── migrations/
├── factories.py
├── tests.py
└── urls.py
```

### 1. Créer une entité (modèle)

1. **Le modèle** — hérite de `TimestampedModel` (ajoute `created_at`/
   `updated_at` automatiquement), avec un `id` texte généré côté serveur
   via une séquence Postgres (jamais fourni par le client) :

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
   (`from .product import Product`).

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

5. **Factory** (pour les tests) — voir `apps/ventes/factories.py`,
   pattern `factory_boy` classique.

### 2. ViewSets et API

1. **Le serializer** :

   ```python
   # apps/ventes/serializers/product_serializer.py
   from rest_framework import serializers
   from apps.ventes.models import Product

   class ProductSerializer(serializers.ModelSerializer):
       class Meta:
           model = Product
           fields = ['id', 'name', 'sku', 'default_price']
   ```

2. **Le viewset** — un `ModelViewSet` DRF standard suffit, avec
   `HasRolePermission` comme unique classe de permission :

   ```python
   # apps/ventes/views/product_viewset.py
   from rest_framework import viewsets
   from apps.accounts.permissions import HasRolePermission
   from apps.ventes.models import Product
   from apps.ventes.serializers import ProductSerializer

   class ProductViewSet(viewsets.ModelViewSet):
       serializer_class = ProductSerializer
       queryset = Product.objects.all()
       permission_classes = [HasRolePermission]
       search_fields = ['name', 'sku']       # active ?search=
       ordering_fields = ['name', 'default_price']  # active ?ordering=
   ```

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
   `delete_product`) sont **créées automatiquement par Django** dès que
   le modèle existe (post-migration) — pas besoin de les déclarer à la
   main. Un utilisateur y a accès si **au moins un de ses rôles**
   possède la permission (`user.roles.filter(permissions__codename=...)`).

3. **Enregistrer les routes** — dans `urls.py` de l'app (via
   `DefaultRouter`) :

   ```python
   # apps/ventes/urls.py
   router = DefaultRouter()
   router.register('ventes', VenteViewSet, basename='vente')
   router.register('products', ProductViewSet, basename='product')
   urlpatterns = router.urls
   ```

   Puis vérifier que `config/urls.py` inclut bien
   `path('api/', include('apps.ventes.urls'))` (déjà le cas si le
   modèle vit dans une app déjà branchée — sinon ajouter la ligne).

4. **Donner la permission aux rôles par défaut** (`admin`/`editor`/
   `user`) — sans ça, la ressource existe mais personne n'y a accès tant
   qu'un admin ne configure pas manuellement la matrice de permissions
   (`/api/roles/`, voir `GUIDE_UTILISATION.md`). Pour la seeder par
   défaut à la création du modèle, ajouter le couple
   `(app_label, model_name)` dans la migration de données correspondante
   (voir `apps/accounts/migrations/0006_seed_role_permissions.py`,
   variable `targets`) :

   ```python
   targets = [
       ('accounts', 'customer'),
       ('ventes', 'product'),
       ('ventes', 'vente'),
       ('ventes', 'ma_nouvelle_ressource'),  # à ajouter
   ]
   ```

5. **Exposer les métadonnées** (optionnel, utilisé pour l'introspection
   `GET /api/meta/<resource>/`) — ajouter le serializer dans
   `RESOURCE_SERIALIZER_MAP` d'`apps/core/views.py`.

6. **Tests** — voir `apps/ventes/tests.py` pour le pattern (pytest +
   `User.objects.create_user(...)` + assignation de rôle en dur pour
   tester les permissions par cas).

Une fois tout ça en place côté backend, la ressource est immédiatement
utilisable côté frontend en suivant la partie précédente de ce guide
(`api.ts`/`hooks.ts` pointant vers les nouveaux endpoints `/api/<ressource>/`).
