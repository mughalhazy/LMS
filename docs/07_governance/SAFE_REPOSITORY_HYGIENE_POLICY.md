# SAFE_REPOSITORY_HYGIENE_POLICY

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-22
Owner: Shared

Source: GOVERNANCE REFINEMENT — SAFE REPOSITORY HYGIENE.md
Companion: REVISED_DECISION_ESCALATION_MATRIX.md, REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md

---

## PURPOSE

This document defines the `SAFE_REPOSITORY_HYGIENE` execution tier — a new classification between `AUTONOMOUS` and `REQUIRES_APPROVAL` in the project governance model.

The tier exists because audit, normalization, and documentation governance phases generate many low-risk maintenance actions that were previously requiring owner approval equal in weight to architecture or security changes. This was incorrect. Owner attention is a scarce resource and must be focused on decisions with architectural, security, or runtime consequences.

---

## DEFINITION

`SAFE_REPOSITORY_HYGIENE` (abbreviated **SRH**) is a class of repository maintenance action that:

1. Does **not** modify business logic
2. Does **not** modify any API (routes, schemas, response shapes)
3. Does **not** modify database structures (no migrations, no schema changes)
4. Does **not** modify runtime behavior (no changes to how the application executes)
5. Does **not** modify infrastructure configuration
6. Does **not** modify deployment behavior
7. Does **not** modify security boundaries or authentication
8. Does **not** modify permissions or RBAC
9. Does **not** touch PROTECTED_AREAS (anchors, shared models, event topics, payment adapters, service manifest)

**And achieves one or more of:**

- Improves repository organization or discoverability
- Improves documentation quality, accuracy, or authority clarity
- Removes generated artifacts that should not be tracked
- Corrects file placement without changing file content
- Adds orientation documentation that does not claim authority
- Updates metadata, status fields, or classification labels
- Consolidates or archives reports and historical documents
- Improves .gitignore coverage for non-source artifacts

---

## EXECUTION AUTHORITY

An AI session may execute SRH actions **without owner approval in the current session**, provided:

1. The action has been explicitly classified as SRH in a governance audit report (APPROVAL_RECLASSIFICATION_REPORT.md or equivalent)
2. The action does not touch any PROTECTED_AREA
3. The action is fully reversible by `git checkout` or `git revert`
4. No content is deleted — only moved, renamed, reclassified, or added

**When uncertain:** Use the ESCALATION PROTOCOL in DECISION_ESCALATION_MATRIX.md. The default is still "do not proceed, ask."

---

## CANONICAL EXAMPLES

The following action types are SRH by definition:

| Action Type | Example | Not SRH If... |
|---|---|---|
| Add README.md to code directory | Adding backend/README.md | README claims runtime authority |
| Add LEGACY or DEPRECATED banner | Adding LEGACY notice to services/academy-ops/ | Banner modifies code imports |
| Add SUPERSEDED notice to docs | Adding SUPERSEDED notice to doc-catalogue.md | Modifies a protected anchor |
| Move documentation files | Moving a .md report from one docs/ dir to another | Target dir is docs/anchors/ |
| Move validation/QC scripts | Moving docs/qc/*.py to validation/ | Script imports protected shared models |
| Move archive documents | Moving a stale session doc to workspace/archive/ | Source is a protected anchor |
| Generate new reports | Creating docs/08_reports/AUDIT_REPORT.md | Report claims architecture authority |
| Update document metadata | Changing Status field from Active to HIST | File is a protected anchor |
| Fix cross-references | Updating a "see also" link in a design doc | Changes authoritative content |
| Add .gitignore entries | Adding .pytest_cache/ to .gitignore | Removes a currently-needed tracked file |
| Consolidate duplicate reports | Merging two historical QC reports | Loses audit trail |
| Update classification matrices | Adding entries to DOCUMENT_INVENTORY.md | Contradicts a protected anchor |
| Create new governance reports | Writing APPROVAL_RECLASSIFICATION_REPORT.md | No exception |
| Add per-service QC notes | Adding a status note to a service README.md | Modifies the service's code or spec |

---

## HARD BOUNDARIES — NEVER SRH

The following are NEVER SRH regardless of how the action is framed:

| Action | Classification | Reason |
|---|---|---|
| Modifying docs/anchors/*.md | REQUIRES_APPROVAL | Anchors are protected; changes cascade |
| Modifying shared/models/*.py | REQUIRES_APPROVAL | Cross-service data contracts |
| Modifying integrations/payments/*.py | REQUIRES_APPROVAL | Production-confirmed payment code |
| Modifying integrations/communication/*.py | REQUIRES_APPROVAL | Notification infrastructure |
| Modifying service-manifest.json | REQUIRES_APPROVAL | Registry of all 72 deployed services |
| Modifying event_topics.json | REQUIRES_APPROVAL | 39 topics; cross-service contracts |
| Deleting any file | REQUIRES_APPROVAL or PROHIBITED | Loss of audit trail; potential data loss |
| Moving backend/services/ code | REQUIRES_APPROVAL | Production service code |
| Moving integrations/payments/ or integrations/communication/ | REQUIRES_APPROVAL | Protected areas |
| Changing .py file logic | REQUIRES_APPROVAL | Runtime behavior |
| Changing .yml/.yaml infrastructure config | REQUIRES_APPROVAL | Deployment behavior |
| Any action touching C: drive | PROHIBITED | Workspace sealed to D: |

---

## DISTINGUISHING FROM AUTONOMOUS

`AUTONOMOUS` covers actions the AI can always do without any classification step:
- Reading files
- Creating reports in docs/08_reports/
- Fixing typos
- Adding tests

`SAFE_REPOSITORY_HYGIENE` covers actions that require classification before execution:
- Moving files (even non-code files)
- Adding to .gitignore
- Reclassifying documents
- Adding banners to documents in active directories (not archives)

The distinction matters because SRH actions require an explicit classification step. An action is not SRH just because it seems harmless — it must be recognized and recorded as SRH in a governance document before execution.

---

## CLASSIFICATION PROCESS

When an audit identifies a maintenance action:

1. **Document the action** in an audit report with sufficient detail
2. **Classify the action** in APPROVAL_RECLASSIFICATION_REPORT.md or equivalent as `SRH`, `REQUIRES_APPROVAL`, or `PROHIBITED`
3. **State the rationale** for the classification
4. **Execute** if SRH — or escalate if REQUIRES_APPROVAL

This process ensures every maintenance action has a documented classification before it is executed.

---

## RISK TOLERANCE

SRH actions are low-risk but not zero-risk. Specifically:

- **File moves** can break relative imports. Validation scripts with `../..` paths must have paths verified before moving.
- **Status reclassifications** can mislead future AI sessions if applied incorrectly.
- **README additions** can claim incorrect authority if poorly worded.

All SRH actions must be logged in session output. The classification decision is part of the audit trail.

---

## RELATIONSHIP TO OTHER GOVERNANCE DOCUMENTS

| Document | Relationship |
|---|---|
| REVISED_DECISION_ESCALATION_MATRIX.md | SRH tier is embedded in the complete matrix |
| REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md | Step-by-step execution instructions for SRH actions |
| APPROVAL_RECLASSIFICATION_REPORT.md | Reclassification of all open audit items to SRH/REQUIRES_APPROVAL/PROHIBITED |
| AI_OPERATING_CONTEXT.md | References DECISION_ESCALATION_MATRIX.md — update required to surface SRH |
