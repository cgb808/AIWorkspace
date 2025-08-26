## RLS Policy Reference (Pre-Supabase)

This document inventories planned Row-Level Security (RLS) design so we can apply it locally *before* any Supabase deployment. The corresponding executable SQL lives in `sql/rls_policies.sql`.

### Objectives
1. Support multi-tenant isolation via a lightweight `tenant_id` column.
2. Keep local development open (no accidental lock-outs) until enforcement is toggled.
3. Reuse existing role tiers: `rag_read`, `rag_write`, `rag_admin`.
4. Allow phased migration of legacy rows (NULL tenant) while still letting admin maintain them.

### Tables Covered
| Table | Purpose | Tenant Column Added |
|-------|---------|--------------------|
| `doc_embeddings` | Vector chunks (RAG) | `tenant_id TEXT` |
| `device_metrics` | Time-series metrics | `tenant_id TEXT` |
| `memory_ingest_dedup` | Memory dedup hashes | `tenant_id TEXT` (optional) |

### Session Variables
We use custom GUC keys:
| Key | Meaning |
|-----|---------|
| `app.current_tenant` | Tenant context for session (set via `app_set_tenant()`). |
| `app.require_tenant` | If `on`, policies enforce strict tenant matching. |

Helper functions:
* `app_set_tenant(tid TEXT)`
* `app_current_tenant()`
* `app_require_tenant()`
* `app_row_visible(row_tenant TEXT)` – central predicate used inside policies.

### Enforcement Modes
| Mode | `app.require_tenant` | Behavior |
|------|---------------------|----------|
| Open (default) | off | All rows visible (development) |
| Enforcing | on | Only rows with matching `tenant_id` visible; NULL rows visible only to admin |

### Policies (Summary)
| Table | Action | Roles | Predicate |
|-------|--------|-------|-----------|
| doc_embeddings | SELECT | all (read/write/admin) | `app_row_visible(tenant_id)` |
| doc_embeddings | INSERT | write/admin | tenant matches (if enforcing) |
| doc_embeddings | UPDATE | write/admin | tenant matches (if enforcing) + visible |
| doc_embeddings | DELETE | admin only | visible + admin |
| device_metrics | SELECT | all | visible |
| device_metrics | INSERT | write/admin | tenant matches (if enforcing) |
| memory_ingest_dedup | SELECT | read/write/admin | visible |
| memory_ingest_dedup | INSERT | write/admin | tenant matches (if enforcing) |

### Typical Session Workflow
```sql
-- Set tenant for session
SELECT app_set_tenant('tenant_a');
-- Optional: turn on enforcement (once data tagged)
SELECT set_config('app.require_tenant','on', false);
-- Query RAG docs (policies apply automatically)
SELECT id, left(chunk,80) FROM doc_embeddings LIMIT 5;
```

### Backfilling Legacy Rows
1. Leave enforcement OFF.
2. Tag rows: `UPDATE doc_embeddings SET tenant_id='tenant_a' WHERE tenant_id IS NULL;`
3. Repeat for other tables.
4. Enable enforcement.

### Soft Deletes vs Hard Deletes
Hard deletes remain restricted to `rag_admin`. If audit trails are required, add column:
```sql
ALTER TABLE doc_embeddings ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
```
Policy adjustment: treat `deleted_at IS NULL` as part of predicate.

### Extending to Supabase Auth
Later, map JWT claim (e.g. `tenant_id`) into `app.current_tenant` using a Postgres function invoked via `ALTER ROLE authenticator SET ...` or a per-session `SET` in an auth hook.

### Applying
```bash
psql postgresql://postgres:<admin-pass>@127.0.0.1:5433/rag_db -f sql/roles_privileges.sql
psql postgresql://postgres:<admin-pass>@127.0.0.1:5433/rag_db -f sql/rls_policies.sql
```

### Verifying
```sql
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND relkind='r';

SELECT * FROM rls_debug_effective; -- Shows current session context
```

### Disable (Temporary Troubleshoot)
```sql
ALTER TABLE doc_embeddings DISABLE ROW LEVEL SECURITY;
```

### Next Steps
1. Add `deleted_at` soft-delete column if needed.
2. Introduce per-user audit (log table) capturing policy context.
3. Integrate token claim → tenant mapping once auth layer present.

---
Document version: 0.1 (initial draft)
