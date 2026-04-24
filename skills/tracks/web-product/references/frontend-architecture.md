# Frontend architecture for web products

## State management — the two kinds

Confusing server state and client state is the root cause of most frontend bugs in web products.

| Type | What it is | Right tool |
|------|-----------|------------|
| **Server state** | Data that lives on the server; fetched, cached, and synchronised with the API | TanStack Query (React Query), SWR |
| **Client state** | UI state that only exists in the browser; not persisted | Zustand, Jotai, React useState |

**Do not put server state into a client state store** (Redux, Zustand). This creates a second source of truth that diverges from the server. Every manual cache invalidation you write is a bug waiting to happen.

```typescript
// Wrong — server data in client state
const useItemsStore = create((set) => ({
  items: [],
  fetchItems: async () => {
    const data = await api.getItems();
    set({ items: data });
  },
}));

// Correct — server state in TanStack Query
function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: () => api.getItems(),
    staleTime: 30_000,  // 30 seconds before refetch
  });
}
```

**When to use client state:**
- Modal open/closed
- Active tab selection
- Multi-step form wizard state
- Theme preference (before it's persisted)
- Draft content that has not been submitted yet

---

## Optimistic UI

Show the result before the server confirms it. Rollback on error.

```typescript
function useCreateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (newItem: NewItem) => api.createItem(newItem),

    onMutate: async (newItem) => {
      // Cancel in-flight refetches to avoid overwriting our optimistic update
      await queryClient.cancelQueries({ queryKey: ['items'] });

      // Snapshot the previous value for rollback
      const previous = queryClient.getQueryData(['items']);

      // Optimistically update
      queryClient.setQueryData(['items'], (old: Item[]) => [
        ...old,
        { id: 'temp-' + Date.now(), ...newItem },
      ]);

      return { previous };
    },

    onError: (error, newItem, context) => {
      // Rollback to snapshot
      queryClient.setQueryData(['items'], context?.previous);
      toast.error('Failed to create item. Please try again.');
    },

    onSettled: () => {
      // Always refetch after success or error to sync with server
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
  });
}
```

**When to use optimistic UI:**
- Actions that are very likely to succeed (create item, toggle, delete)
- Low-stakes operations where showing immediate feedback matters

**When NOT to use:**
- Financial operations (payment, refund) — always wait for server confirmation
- Operations with complex side-effects that the UI needs to reflect accurately

---

## Error boundaries

Uncaught render errors crash the entire React tree. Error boundaries isolate the damage.

**Three levels:**

```tsx
// 1. Global fallback — catches everything that slips through
// In app root, wrap the whole app
<ErrorBoundary fallback={<GlobalErrorFallback />}>
  <App />
</ErrorBoundary>

// 2. Page-level — catches errors in a route without crashing other routes
function DashboardPage() {
  return (
    <ErrorBoundary fallback={<PageErrorFallback />}>
      <Dashboard />
    </ErrorBoundary>
  );
}

// 3. Component-level — isolates a widget; rest of the page still renders
function ItemList() {
  return (
    <ErrorBoundary fallback={<div>Could not load items</div>}>
      <Items />
    </ErrorBoundary>
  );
}
```

Use `react-error-boundary` for a battle-tested implementation with reset capability.

**Log errors to your error tracker from the error boundary:**

```tsx
<ErrorBoundary
  onError={(error, info) => Sentry.captureException(error, { extra: info })}
  fallback={<PageError />}
>
```

---

## Loading states — skeleton screens over spinners

Spinners cause layout shift when content loads. Skeleton screens preserve the layout and feel faster.

```tsx
// Wrong — layout jumps when data arrives
if (isLoading) return <Spinner />;
return <ItemList items={data} />;

// Correct — layout stable during load
if (isLoading) return <ItemListSkeleton />;
return <ItemList items={data} />;
```

**Skeleton screen rules:**
- Match the approximate shape of the loaded content (same number of rows, similar text lengths)
- Animate with a shimmer effect (CSS `background: linear-gradient(...)` with `animation`)
- Do not show skeletons for very fast loads (< 200ms) — use a `200ms` delay before showing the skeleton

**Error states:**
- Always show a retry button for network errors
- Distinguish "not found" (show empty state) from "server error" (show retry)
- Do not show raw error messages to end users; log them for engineers

---

## Typed client from spec

Generate the API client from the OpenAPI spec rather than hand-rolling `fetch` calls. See `api-design-patterns.md` for setup.

```typescript
// Centralise your client
// src/lib/api-client.ts
import createClient from 'openapi-fetch';
import type { paths } from './generated/api';

export const apiClient = createClient<paths>({
  baseUrl: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Usage — TypeScript knows the exact shape of request and response
const { data, error } = await apiClient.POST('/workspaces/{workspaceId}/items', {
  params: { path: { workspaceId } },
  body: { name: 'New item', description: '' },
});
// data is typed as CreateItemResponse, error is ApiError | undefined
```

**Regenerate on spec changes.** Add to your dev workflow:

```json
// package.json scripts
"generate:api": "openapi-typescript openapi.yaml -o src/lib/generated/api.d.ts",
"predev": "npm run generate:api"
```

---

## Forms

```typescript
// Use react-hook-form + Zod for validation
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  email: z.string().email('Must be a valid email'),
});

type FormData = z.infer<typeof schema>;

function InviteForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} aria-describedby="email-error" />
      {errors.email && <p id="email-error" role="alert">{errors.email.message}</p>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Inviting...' : 'Send invite'}
      </button>
    </form>
  );
}
```

**Accessibility in forms:**
- Every input must have a `<label>` (visible or `aria-label`)
- Error messages must use `role="alert"` so screen readers announce them
- Associate error with its input via `aria-describedby`
- Disable the submit button during submission to prevent double-submit

---

## Code splitting

```typescript
// Route-based splitting with React.lazy
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Billing = lazy(() => import('./pages/Billing'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/billing" element={<Billing />} />
      </Routes>
    </Suspense>
  );
}
```

**What to split lazily:**
- Every top-level route — always
- Heavy libraries (chart libraries, rich text editors, PDF renderers) — when used in a non-critical path
- Admin or settings sections — typically loaded by < 10% of users

**What NOT to split:**
- Auth pages (login, signup) — need to load fast, not delay
- Error boundaries — must always be loaded
- Core layout components

---

## Accessibility in components

Minimum requirements for every interactive component:

| Component | Requirement |
|-----------|-------------|
| Button | `type="button"` or `type="submit"` explicitly set |
| Icon-only button | `aria-label` describing the action |
| Modal / dialog | `role="dialog"`, `aria-labelledby`, focus trap, close on Escape |
| Dropdown menu | `role="menu"`, keyboard navigation (Arrow keys, Enter, Escape) |
| Toast notification | `role="alert"` for errors, `role="status"` for info |
| Loading indicator | `aria-live="polite"` or `role="status"` |
| Form error message | `role="alert"`, associated to input via `aria-describedby` |
| Data table | `<caption>`, `scope` on `<th>`, `aria-sort` for sortable columns |

**Focus management:**
- After opening a modal → move focus to the first focusable element inside it
- After closing a modal → return focus to the element that opened it
- After a page navigation (SPA) → move focus to the `<main>` heading or route content
