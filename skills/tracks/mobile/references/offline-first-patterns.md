# Offline-first patterns

Mobile users go offline all the time — subways, flights, elevators, hotel lobbies, bad coverage in a kitchen. A mobile app that treats the network as reliable is broken for the real world. Offline-first inverts the assumption: the local store is the source of truth for reads, the server is reconciled in the background, and writes are queued and retried. This reference covers local storage, optimistic UI, conflict resolution, the outgoing operation queue, and sync engine choices.

---

## Local-first storage

The app reads from a local store on every screen. The local store is populated by sync, never directly from the network in the hot path of a UI render.

Storage options:

| Store | Platform | When |
|-------|----------|------|
| Core Data | iOS | Complex object graphs, schema migrations, NSFetchedResultsController for live views |
| SwiftData | iOS 17+ | New iOS-only projects; thin Core Data wrapper with Swift ergonomics |
| Room | Android | Standard for Android; reactive queries via Flow |
| SQLite (GRDB / SQLDelight) | Cross | When you want direct SQL and control |
| WatermelonDB | React Native | Built for offline-first sync; lazy loading; large datasets |
| Realm | Cross | Object DB with sync; watch licensing |
| PouchDB | React Native / web | CouchDB-compatible sync protocol |
| MMKV / UserDefaults / SharedPreferences | All | Small key-value state only; not a primary store |

Pick one primary store per platform. Do not mix Core Data and SQLite in the same app — reconciliation between them is not a problem you want.

### The shape of a local store

Every entity has:

- A local ID (UUID generated on the client) that is stable from the moment the row is created locally.
- An optional server ID, null until the server acknowledges the create.
- A `sync_state`: `clean`, `pending_create`, `pending_update`, `pending_delete`, `conflict`.
- An `updated_at` timestamp, always set by the client on write.
- An optional `server_updated_at`, set when the server acknowledges.
- A version or ETag for conflict detection.

```sql
CREATE TABLE notes (
  local_id TEXT PRIMARY KEY,
  server_id TEXT UNIQUE,
  title TEXT,
  body TEXT,
  updated_at INTEGER NOT NULL,
  server_updated_at INTEGER,
  version TEXT,
  sync_state TEXT NOT NULL DEFAULT 'clean',
  pending_op_id TEXT
);
```

UI reads from `notes` filtered by `sync_state != 'pending_delete'`. UI does not know about the network.

---

## Optimistic UI

When the user creates, updates, or deletes, the UI reflects the change immediately. The change is written to the local store, the outgoing operation is enqueued, and the UI moves on. The user sees no spinner for these operations.

Swift example:

```swift
func createNote(title: String, body: String) async {
    let note = Note(
        localId: UUID().uuidString,
        serverId: nil,
        title: title,
        body: body,
        updatedAt: Date(),
        syncState: .pendingCreate
    )
    try await localStore.insert(note)
    await syncQueue.enqueue(.create(note))
    // UI already updated via the reactive query on localStore
}
```

Failure handling is backwards from a server-first app. The UI never waits for the network, so there is no error toast at the point of action. Errors surface asynchronously:

- A **per-item indicator** on the row — small cloud-with-slash or clock icon — showing the item is not yet synced. Tap for details.
- A **global banner** when the queue has been stuck for more than N minutes (default 5).
- A **conflict resolution screen** when a write fails due to a server-side conflict (see below).

Do not hide the fact that a change is not yet synced. Users want to know what state their data is in. But do not block the UI waiting for the answer.

---

## Conflict resolution

Pick a strategy per entity and make the choice explicit in the design doc.

### Last-write-wins (LWW)

Simplest. The server compares the client's `updated_at` to its own. Newer timestamp wins. Older timestamp is discarded.

Use when: data is low-stakes and rarely edited on multiple devices (user profile, UI preferences, draft autosaves).

Do NOT use when: data loss would be noticed (collaborative documents, shared lists, anything the user would call "my notes").

### Server wins on conflict, client re-applies

Server rejects writes with a version mismatch. Client receives the current server state, re-applies its local change on top (if it still makes sense), and submits again.

Use when: writes are mostly commutative field updates (toggle a checkbox, change a tag).

Implementation: server returns HTTP 409 with current resource body. Client diff-merges its pending change and retries.

### Field-level merge with CRDTs

Each field is a CRDT (G-Counter, LWW-Register, OR-Set, RGA). Writes from multiple clients merge deterministically without a central authority.

Use when: real-time collaboration is a product requirement (shared documents, whiteboards, multiplayer state).

Libraries: Automerge, Yjs. Heavy dependency; pick only if real-time multi-device editing is a named feature.

### User intervention

On conflict, present the user with both versions and ask which to keep (or merge manually).

Use when: conflicts are rare but the cost of silent loss is high (calendar events with both device edits, long-form notes).

Keep the conflict resolution screen simple: left column = yours, right column = server, bottom = "Keep mine" / "Keep theirs" / "Merge". Never show three-way merge conflict markers in a consumer app.

---

## Outgoing operation queue

Writes are not fire-and-forget. Every outgoing change goes into a durable queue, processed in order, with retry-and-dedup.

### Properties the queue must have

**Durable.** The queue survives app kill, device reboot, OS update. Stored in the same SQLite/Core Data/Room database as the entities, not in memory or a plist.

**Ordered per entity.** All operations on note X execute in the order they were enqueued. Operations on note Y can run in parallel with note X.

**Retried with backoff.** Transient failures (timeouts, 5xx, offline) retry with exponential backoff + jitter. Default: 1s, 2s, 4s, 8s, 16s, capped at 60s, with ±25% jitter.

**Deduped.** If the queue has `update(note_X, title: "A")` followed by `update(note_X, title: "B")` still pending, coalesce to a single `update(note_X, title: "B")` before the next sync attempt.

**Terminates on permanent failure.** A 400-class error (other than 401/403 which need re-auth) is not retried. The operation is moved to a dead-letter state, the item is marked `sync_state = 'conflict'`, and the user is notified.

**Resumed on network change.** When the OS reports connectivity restored (`NWPathMonitor` on iOS, `ConnectivityManager` on Android), the queue wakes and drains.

### Queue row shape

```sql
CREATE TABLE sync_queue (
  op_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_local_id TEXT NOT NULL,
  operation TEXT NOT NULL,              -- create | update | delete
  payload BLOB NOT NULL,                -- serialized change
  enqueued_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_attempt_at INTEGER,
  last_error TEXT,
  state TEXT NOT NULL DEFAULT 'pending' -- pending | in_flight | done | dead
);

CREATE INDEX sync_queue_entity_idx ON sync_queue (entity_type, entity_local_id);
CREATE INDEX sync_queue_state_idx ON sync_queue (state, enqueued_at);
```

### Dedup logic

Before enqueueing op X on entity E, check for existing pending ops on E. If the last pending op on E is the same operation type, merge the payload (LWW at field level) and keep one row. If it is a different type (create then delete), collapse the pair to a no-op and remove both.

---

## Sync engines

Build-vs-buy decision:

**Build custom** when: the server API is RESTful and stable; sync is per-entity and predictable; team is mobile-experienced; product does not need real-time multi-device updates.

**Buy a sync engine** when: real-time presence is a feature; team is small and cannot maintain a custom engine; schema is stable enough to commit to the engine's model.

### WatermelonDB

React Native only. Lazy-loaded, handles very large datasets well (millions of rows). Sync is a pull/push protocol you implement against your server. Good fit for a RN app with a large catalogue and moderate writes.

### PouchDB

CouchDB-compatible sync protocol. If your backend is CouchDB / Cloudant / BigCouch, sync is automatic. If not, you are running a CouchDB replica server-side solely to terminate sync — usually not worth it.

### Realm / MongoDB Device Sync

Object DB with built-in sync to MongoDB Atlas. Tight integration, handles conflict resolution automatically with server-side functions for custom logic. Licensing is per-MAU beyond the free tier; confirm the economics before committing.

### Firebase Firestore

Not a sync engine exactly, but offline persistence is built in. Good for small-to-medium documents with simple query patterns. Limits: no full-text search, query cost at scale, vendor lock-in.

### Custom

Roll your own when none of the above fits the server contract. Plan for: conflict resolution code, schema migrations on both client and server, dead-letter handling, retry logic, connectivity monitoring, battery impact (see `mobile-performance.md`). Budget ~2 engineer-months for a correct first version. Most teams underestimate this by 3×.
