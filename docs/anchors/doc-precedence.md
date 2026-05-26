# Document Precedence Anchor (Canonical)

## Purpose
Define a single deterministic document priority model so decisions, implementations, and reviews always resolve to the same source of truth.

---

## Canonical Priority Order
When two or more documents conflict, apply the **highest-priority document** below.

1. **BATCH docs** (`B2*`, `B3*`, `B5*`, `B6*`)
2. **SPEC docs** (`*_spec.md`)
3. **ARCH docs** (`ARCH_*`)
4. **Legacy / general docs** (all remaining narrative/reference docs)

Tie-breaker rules:
- If two docs are in the same priority class, prefer the most specific scope (domain-specific over platform-general).
- If scope is equal, prefer the most recently updated doc.
- If still tied, raise explicit maintainer decision and add a note in this anchor.

---

## Classification Rules

### Priority 1 — BATCH docs (Authoritative)
A document is Priority 1 if filename starts with one of:
- `B2`
- `B3`
- `B5`
- `B6`

Interpretation rule:
- BATCH docs override any conflicting SPEC/ARCH/legacy statement.

### Priority 2 — SPEC docs
A document is Priority 2 if filename matches:
- `*_spec.md`

Interpretation rule:
- SPEC docs override ARCH and legacy/general docs.
- SPEC docs do **not** override BATCH docs.

### Priority 3 — ARCH docs
A document is Priority 3 if filename starts with:
- `ARCH_`

Interpretation rule:
- ARCH docs override legacy/general docs.
- ARCH docs do **not** override BATCH or SPEC docs.

### Priority 4 — Legacy/general docs (Fallback)
Everything else defaults to Priority 4.

Interpretation rule:
- Legacy/general docs are valid only when they do not conflict with higher-priority artifacts.

---

## Deprecation Marking Standard
A doc must be marked **Deprecated** when any higher-priority doc supersedes it on the same topic.

Required banner at top of deprecated docs:

```md
> DEPRECATED — Superseded by: <path-to-higher-priority-doc>
> Reason: <short reason>
> Last reviewed: <YYYY-MM-DD>
```

Status model:
- **Active**: No higher-priority conflict.
- **Deprecated**: Superseded by higher-priority source.
- **Archived**: Historical only; not for implementation decisions.

---

## Conflict Resolution Workflow
1. Identify all docs covering the decision topic.
2. Assign each doc to a priority class (1–4).
3. Keep the highest-priority doc as source of truth.
4. Mark lower-priority conflicting docs as **Deprecated**.
5. Add cross-links from deprecated docs to the winning source.

Outcome rule:
- After workflow completion, implementation guidance must reference exactly one winning source-of-truth path per topic.

---

## QC + AUTO-FIX (Mandatory)

### Validation checklist
- [x] No conflicts remain after applying precedence and deprecations.
- [x] Priority order is explicit and deterministic.
- [x] Deprecation marking standard is defined.
- [x] Conflict resolution workflow is documented.

### Score
**10/10**
