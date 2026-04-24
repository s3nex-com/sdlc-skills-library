# API design patterns for web products

## REST vs GraphQL vs tRPC — decision first

| Criterion | REST | GraphQL | tRPC |
|-----------|------|---------|------|
| Client diversity (mobile, web, third-party) | Best — universal | Good | Only works for TypeScript full-stack |
| Type safety without a build step | No — requires codegen | No — requires codegen | Yes — types shared natively |
| Over/under-fetching | Worse — fixed response shape | Best — client specifies exactly what it needs | Good |
| Caching | Simple — HTTP cache, CDN | Complex — requires query-level cache keys | Good — React Query integration |
| Ecosystem / hiring familiarity | Widest | Wide | TypeScript teams only |
| Third-party API consumers | Yes | Yes | No |
| Real-time subscriptions | Needs SSE or WebSocket separately | Native subscriptions | Native subscriptions |

**When to pick:**
- **REST**: when you have or anticipate external API consumers, mobile clients, or a non-TypeScript backend.
- **GraphQL**: when the frontend needs highly varied queries and you want to avoid N+1 by design (DataLoader). Accept the tooling cost.
- **tRPC**: when your entire stack is TypeScript and you want the fastest iteration with zero API drift. Not suitable if you ever plan to expose the API externally.

---

## Spec-first workflow (REST)

Write the OpenAPI spec before implementation, not after.

```
1. Design API shape in OpenAPI 3.1 YAML
2. Review spec with consumers (frontend team, mobile team) — iterate before writing code
3. Freeze the spec — mark it as reviewed in git
4. Generate server stubs and typed client from the spec
5. Implement against the stubs
6. CI validates the running server's responses match the spec (contract test)
```

Tools:
- Spec editor: Stoplight Studio, Swagger Editor, or raw YAML in VS Code with the OpenAPI extension
- Server stubs: `openapi-generator` (Java/Node/Python)
- Typed client: `openapi-typescript` + `openapi-fetch` (TypeScript), `openapi-generator` (any language)
- CI validation: `dredd`, `schemathesis`, or Pact

---

## Error schema — be consistent

Pick one error shape and use it everywhere. Do not return a string sometimes and an object other times.

```json
{
  "error": {
    "code": "ITEM_NOT_FOUND",
    "message": "Item with ID abc123 does not exist",
    "details": {
      "itemId": "abc123"
    }
  }
}
```

| Field | Purpose |
|-------|---------|
| `code` | Machine-readable constant — safe for client switch statements |
| `message` | Human-readable — for logs and developer debugging, not end-user display |
| `details` | Structured context — validation errors, field names, constraint violations |

Map HTTP status codes consistently:

| Status | When |
|--------|------|
| 400 | Client sent invalid data (validation failure) |
| 401 | Not authenticated (missing or invalid token) |
| 403 | Authenticated but lacks permission (wrong role) |
| 404 | Resource does not exist (or is hidden for security reasons) |
| 409 | Conflict — duplicate, optimistic lock failure |
| 422 | Semantically invalid (passes validation but violates business rule) |
| 429 | Rate limited |
| 500 | Server error — do not leak stack traces |

---

## Pagination

**Cursor-based** (recommended for most cases):

```json
GET /items?cursor=eyJpZCI6ImFiYyJ9&limit=25

{
  "items": [...],
  "nextCursor": "eyJpZCI6Inhsel0...",
  "hasMore": true
}
```

- Stable under concurrent inserts/deletes — no skipped or duplicated items
- O(1) per page (index scan from cursor position)
- Cannot jump to page 5 directly — acceptable for most UIs

**Offset-based** (acceptable for admin UIs, reports):

```json
GET /items?offset=50&limit=25

{
  "items": [...],
  "total": 342,
  "offset": 50,
  "limit": 25
}
```

- Can jump to any page — needed for "go to page N" UIs
- Unstable under concurrent mutations (rows shift in/out)
- O(offset) cost on large offsets

---

## Versioning policy

**URL path versioning** (`/v1/`, `/v2/`) for public APIs:

```
https://api.example.com/v1/items
https://api.example.com/v2/items  ← new breaking version
```

**Header versioning** for internal APIs (avoids URL clutter):

```
GET /items
X-API-Version: 2024-01-01
```

**Non-breaking changes** (no version bump needed):
- Adding new optional fields to responses
- Adding new optional query parameters
- Adding new endpoints

**Breaking changes** (require a new version):
- Removing or renaming fields
- Changing field types
- Removing endpoints
- Changing required parameters

**Deprecation headers** for in-progress deprecations:

```
Deprecation: true
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Link: <https://docs.example.com/migration/v2>; rel="successor-version"
```

---

## Typed client generation (TypeScript)

**From OpenAPI spec:**

```bash
npm install openapi-typescript openapi-fetch
npx openapi-typescript openapi.yaml -o src/lib/api.d.ts
```

```typescript
import createClient from 'openapi-fetch';
import type { paths } from './lib/api.d';

const client = createClient<paths>({ baseUrl: '/api' });

// Fully typed — TypeScript knows the request and response shape
const { data, error } = await client.GET('/items/{id}', {
  params: { path: { id: 'abc123' } },
});
```

**From GraphQL schema:**

```bash
npm install -D @graphql-codegen/cli @graphql-codegen/typescript @graphql-codegen/typescript-operations
# codegen.yml: schema: src/schema.graphql, documents: src/**/*.graphql
npx graphql-codegen
```

**Commit the generated types to the repo.** CI should verify the types are up to date (`openapi-typescript` → compare output with committed file; fail if different).

---

## N+1 protection (GraphQL)

Every resolver that loads related data must use DataLoader:

```typescript
// Wrong — N+1 queries
const workspaceLoader = new DataLoader<string, Workspace>(async (ids) => {
  const workspaces = await db.workspace.findMany({
    where: { id: { in: ids as string[] } },
  });
  return ids.map(id => workspaces.find(w => w.id === id) ?? null);
});
```

Set maximum query complexity and depth limits to prevent denial-of-service via deeply nested queries:

```typescript
import depthLimit from 'graphql-depth-limit';
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  validationRules: [
    depthLimit(10),
    createComplexityLimitRule(1000),
  ],
});
```
