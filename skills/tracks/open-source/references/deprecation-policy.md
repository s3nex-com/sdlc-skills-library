# Deprecation policy

Removing public API is a MAJOR semver event. Deprecating it is not — but deprecation is the only path to a removal that does not ambush users. This reference defines the lifecycle, the warning conventions, and what a migration guide must contain. Skip any step and the removal turns into a support incident.

---

## The lifecycle

Every deprecated symbol travels through four stages. Skipping stages is the most common cause of downstream breakage.

```
stage 1: ANNOUNCED    — changelog entry, docs updated, warning emitted
stage 2: WARNING      — runtime warnings on use, migration path documented
stage 3: ERROR-OR-NOOP — in final minor before removal, become hard errors (or silent noop if that is safer)
stage 4: REMOVED      — deleted in next major release
```

### Minimum deprecation windows

| Mode | Window |
|------|--------|
| Nano | 1 release (MINOR) before removal |
| Lean | 2 releases (MINOR) before removal |
| Standard | 3 releases or 6 months, whichever is longer |
| Rigorous | 12 months minimum, or longer if the symbol is in widespread use |

The window is the *minimum*. Widely-used symbols get longer windows. Rarely-used symbols can use the minimum. A symbol is "widely used" if download analytics, GitHub code search, or public dependents suggest meaningful adoption. If you cannot measure, assume wide use.

---

## Stage 1 — announce

At the moment the deprecation is decided and merged:

1. Changelog entry under `### Deprecated` with the symbol name, replacement, and planned removal version.
2. Docstring / JSDoc / type-level deprecation tag (`@deprecated` in JS, `warnings.warn` in Python, `#[deprecated]` in Rust, `Deprecated` attribute in C#).
3. Migration section in docs pointing from the deprecated symbol to the replacement, with before / after code snippets.
4. GitHub Issue labelled `deprecation` tracking the removal in the future MAJOR milestone.

The deprecation is announced in the MINOR or PATCH release it lands in. Do not wait for a MAJOR — that defeats the purpose.

---

## Stage 2 — warn at runtime

A silent deprecation is not a deprecation. Users who read the changelog see it; users who don't, don't. Runtime warnings reach everyone.

Language conventions:

- **Python**: `warnings.warn("X is deprecated; use Y instead", DeprecationWarning, stacklevel=2)`. Downstream users can silence with `warnings.filterwarnings`.
- **Node.js**: `process.emitWarning("X is deprecated; use Y instead", "DeprecationWarning", "DEP0123")`. Use a stable deprecation code so users can grep for it.
- **Rust**: `#[deprecated(since = "2.1.0", note = "use Y instead")]`. Compiler surfaces the warning.
- **Go**: A `// Deprecated: use Y instead.` doc comment on the exported identifier. `staticcheck` and `go vet` surface the warning.
- **Java / Kotlin**: `@Deprecated(since = "2.1.0", forRemoval = true)` with a message. IDE and compiler surface it.
- **C# / .NET**: `[Obsolete("use Y instead", error: false)]`.

Warn once per process per call site when practical. Flooding stderr on every call is user-hostile and trains users to suppress warnings.

### Warning suppression

Document the suppression mechanism in the deprecation note so users who consciously accept the risk can silence the noise without disabling the category globally. For example:

```python
import warnings
warnings.filterwarnings("ignore", message=r"X is deprecated", category=DeprecationWarning)
```

For libraries used in test suites that treat warnings as errors, offer a scoped opt-out keyed on the specific deprecation, not on `DeprecationWarning` as a class.

---

## Stage 3 — error or noop in the final minor

In the last MINOR before the MAJOR that removes the symbol, escalate the signal:

- **Error mode (most cases):** the symbol now raises / throws / panics on use. The error message points to the migration guide. This converts silent reliance into a loud failure that still leaves a rollback path (pin to the previous minor).
- **Noop mode (rare):** if the symbol's only effect is observable side effects and silent removal is safer than throwing (e.g. a deprecated telemetry hook), leave the symbol in place but make it a documented noop. Document it loudly.

Pick error mode by default. Only use noop mode when throwing would cascade into user-visible incidents worse than silent drift.

---

## Stage 4 — remove in the next MAJOR

The removal is the MAJOR event. The release PR must:

1. Delete the symbol and every internal reference.
2. Move the changelog entry from `Deprecated` to `Removed` in the MAJOR version's section.
3. Link the migration guide in the release notes.
4. Verify `diff_contracts.py` reports REMOVED for the symbol and the MAJOR bump is claimed in the release PR.

After the MAJOR ships, keep the migration guide in the docs under a "Migrating from vN to vN+1" section for at least one more major cycle.

---

## Migration guide requirements

A migration guide without these elements is a blog post, not a migration guide:

- **Before / after code snippets** for every deprecated symbol, not just "use Y instead"
- **Semantic differences** called out explicitly — "Y returns a Promise, X was synchronous"
- **Edge cases** — what happens when the replacement is not a drop-in (null handling, error types, options with different defaults)
- **Codemod if feasible** — for large API renames or signature changes, ship a codemod (`jscodeshift`, `libcst`, `ast-grep`, language-specific equivalents) that rewrites user code automatically. A one-command migration reduces upgrade friction to near zero.
- **Estimated effort** — rough scale ("1 hour for a typical project", "multi-day for projects that depended on the deprecated callback") so downstream can plan

Place migration guides at a stable URL (`docs/migrations/v2-to-v3.md`) so the link in runtime warnings does not rot.

---

## Transitive breaking changes

You can break users without touching your own API if:

- A dependency you re-export changes shape. If you re-export `Foo` from `dependency-x` and `dependency-x` changes `Foo`, your users see the change through you.
- A peer dependency you require tightens its range or changes its API.
- A runtime requirement you depend on (Node version, libc version) moves forward.

Treat transitive breaks as first-class breaks. They go through the same lifecycle:

1. Announce in the changelog under `Changed` or `Deprecated`.
2. Emit a warning at import or first-use where feasible.
3. Wait the deprecation window.
4. Bump MAJOR when the transitive break lands.

If you cannot avoid the transitive break without the window (e.g. a security fix in an upstream dependency), publish a MAJOR bump and an explanation. Do not hide it in a minor.

---

## Worked example — a full deprecation cycle

`my-db-client@1.4.0` exposes `connect(url, options)` where `options.reconnect` defaults to `true`. The team decides the default is wrong: silent reconnection masks real outages. The target is to remove `options.reconnect` entirely and make reconnection explicit through a separate `withReconnect(client, policy)` wrapper.

**`1.5.0` (announced):**
- Changelog: "`options.reconnect` deprecated; use `withReconnect(client, policy)` instead. Planned removal in `2.0.0`."
- `@deprecated` marker on the type definition for the option.
- Docs updated with a before/after migration section.
- Runtime: no warning yet (low-friction minor release).

**`1.6.0` (warning):**
- `connect()` now emits a deprecation warning at first use if `reconnect` is set in options. Warning text: `"options.reconnect is deprecated; use withReconnect(). See https://example.com/docs/migrations/v1-to-v2."`
- Warning code: `DEP0001` so users can grep logs.

**`1.7.0` and `1.8.0` (window continues):**
- Deprecation remains active. Documentation continues to route new users to `withReconnect`.

**`1.9.0` (final minor before MAJOR):**
- Setting `options.reconnect` now throws: `"options.reconnect was removed in 2.0.0. Migrate to withReconnect(client, policy). See https://example.com/docs/migrations/v1-to-v2."` in the *upcoming* 2.0.
- Actually, decision: keep throwing to 1.9 to force detection while users are still on the 1.x line where rollback is trivial.

**`2.0.0` (removal):**
- `options.reconnect` deleted. `connect()` no longer reads the field. Changelog entry under Removed references the migration guide.
- Codemod published at `npm create my-db-client-migrate` that rewrites `connect(url, { reconnect: true, ... })` into `withReconnect(connect(url, { ... }), defaultPolicy)`.

Total elapsed time: approximately 6 months across five minor releases and one major. No downstream incidents reported at the `2.0.0` cut because the warning window gave users time to act.
