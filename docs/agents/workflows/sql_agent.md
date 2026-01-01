# SQL Agent Playbook

## Goal
Generate safe, correct SQL that answers the question using the available schema.

## Constraints
- Use read-only queries only (no INSERT/UPDATE/DELETE/DROP).
- Always minimize result size (LIMIT unless aggregate).
- Prefer explicit column lists (avoid SELECT * unless asked).

## Planner responsibilities
- Restate the question in SQL terms (entities, filters, metrics).
- Identify candidate tables and required schema inspection.
- Define success criteria (correct metric, correct grouping, expected time window).
- Choose a validation-first plan (LIMIT sample first; then final aggregation).

## Executor responsibilities
1) Inspect schema:
   - List relevant tables.
   - Fetch schema for likely tables.
   - Identify join keys.
2) Draft query:
   - Start with a small query (LIMIT 10) to validate joins.
   - Add filters and aggregates.
3) Validate + execute:
   - Execute query.
   - If errors, fix iteratively using the error message.
4) Produce final SQL artifact:
   - Ensure constraints are satisfied (read-only, LIMIT where appropriate).

## Reviewer checklist
- Read-only only? No destructive statements?
- LIMIT applied when returning rows?
- No SELECT * unless explicitly requested?
- Join safety: cardinality issues, correct keys, correct join type?
- Filters align with question? Time window included if required?
- Output columns match the request?

## Finalizer format
- Final SQL block (single source of truth)
- 3–6 bullets: what it does + assumptions
- Optional: brief note on performance considerations (indexes/join keys)

## Example template
```sql
-- Question: <...>
WITH base AS (
  SELECT
    t.id,
    t.created_at,
    t.status
  FROM analytics.orders t
  WHERE t.created_at >= DATE '2025-01-01'
)
SELECT
  status,
  COUNT(*) AS order_count
FROM base
GROUP BY 1
ORDER BY order_count DESC
LIMIT 100;
```
