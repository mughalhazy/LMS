# PROJECT MEMORY GOVERNANCE

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: AI + Human

---

## Purpose

This document establishes the governance rules for the Project Memory Layer. It defines who can change what, when items can be reopened, how duplicates are handled, and what the authority hierarchy is.

---

## Authority Hierarchy

The Project Memory Layer sits at TIER 5 in the document authority hierarchy:

| TIER | Layer | Documents |
|---|---|---|
| 0 | Product Authority | PROJECT_CHARTER.md |
| 1 | Governance Anchors | docs/anchors/*.md |
| 2 | Architectural Contracts | docs/00_authority/*.md |
| 3 | Service Specifications | docs/specs/*.md |
| 4 | Implementation Docs | docs/01_backend/, docs/03_frontend_authority/ |
| 5 | AI-Generated History | docs/08_reports/, docs/09_project_memory/ |

**Rule: When a memory layer entry conflicts with a TIER 0–4 document, the higher tier wins. The memory layer must be updated to reflect the TIER 2–4 authority, not the other way around.**

The memory layer is institutional memory, not design authority. It records what was decided; the authority documents record what is true.

---

## Classification Rules

### AUTO-CLOSED

Apply this classification only if ALL of the following are true:
- The answer is proven directly from repository evidence (code, config, spec, contract)
- No assumptions were made
- The answer is stable under normal code evolution

Do NOT auto-close if:
- The evidence requires interpretation
- The answer depends on a future decision
- Two sources conflict on the answer

### SAFE-DEFAULT

Apply this classification only if ALL of the following are true:
- One path is overwhelmingly supported by evidence
- Implementation can proceed without risk
- No commercial or legal exposure is introduced
- The owner has had opportunity to override and has not

Do NOT apply SAFE-DEFAULT if:
- Multiple paths are equally supported
- Commercial risk exists
- Legal compliance is unclear
- The owner has expressed a different preference

### OWNER-DECISION

Apply this classification only if ALL of the following are true:
- The repository cannot answer
- The architecture cannot answer
- Documentation cannot answer
- The decision affects product behavior or security posture

Do NOT create new OWNER-DECISION items for:
- Technical implementation details (these are AUTO-CLOSED or SAFE-DEFAULT)
- Documentation updates (autonomous per REVISED_DECISION_ESCALATION_MATRIX)
- Sprint planning (these are engineering decisions)

### EXTERNAL-DEPENDENCY

Apply this classification only if the item:
- Requires credentials only a human can generate
- Requires vendor account registration
- Requires external approval or legal agreement
- Requires physical infrastructure provisioning

Do NOT classify software gaps as EXTERNAL-DEPENDENCY.

### OUT-OF-SCOPE

Apply this classification only if:
- The feature is explicitly deferred in FEATURE_SCOPE.md, or
- The feature is an implementation gap (FGAP) confirmed in FEATURE_GAP_REGISTER.md, or
- The feature belongs to a formal future phase, or
- The feature is formally excluded from this platform

Do NOT classify missing features as OUT-OF-SCOPE without confirming product intent exists.

---

## Reopen Governance

Items may ONLY be reopened when one or more of these conditions is met:

| Reopen Trigger | Example |
|---|---|
| Evidence changed | New code inspection reveals different implementation |
| Implementation changed | Sprint modifies what was previously confirmed |
| Architecture changed | Major refactor changes how a component works |
| Owner explicitly reverses a decision | Owner says "we're switching from Docker Compose to Kubernetes now" |
| External dependency becomes available | JazzCash credentials are provisioned |

**Items may NOT be reopened for:**
- A new AI session not knowing the item was already resolved
- A new developer re-asking a question without checking this register
- Speculative reconsideration without new evidence

When reopening an item:
1. Add "REOPENED [date] — Reason: [trigger]" to the item's Current Status field
2. Update the Evidence Source with new evidence
3. Re-classify if the new evidence changes the classification
4. Update FINAL_CLASSIFIED_REGISTER.md to reflect the new status

---

## Duplicate Prevention

Before creating a new memory layer entry:

1. Search FINAL_CLASSIFIED_REGISTER.md for the topic
2. Search all 5 subordinate registers for the original ID (OA-NNN, GAP-NNN, TBD-NNN, PDC-NNN, etc.)
3. If found: update the existing entry rather than creating a new one
4. If genuinely new: create with next available PM-ID

**Never create duplicate entries.** Duplicate entries split institutional memory and cause confusion.

---

## Project Completion Rules

Project development phases do NOT require:
- All EXTERNAL-DEPENDENCY items resolved (provisioning happens during deployment)
- All OUT-OF-SCOPE items completed (they are deferred by design)

Project phases DO require:
- All AUTO-CLOSED items remain closed (do not reopen without new evidence)
- All SAFE-DEFAULT items are implemented per the default path (or owner has explicitly reversed)
- All OWNER-DECISION items are actioned before production launch

Production launch additionally requires:
- PM-OD-001 (JWT key) resolved — auth is production-broken without it
- PM-ED-001, PM-ED-002 (JazzCash, EasyPaisa) resolved — payments blocked without it
- PM-ED-003 (SMTP) resolved — transactional email blocked
- PM-ED-004 (domain), PM-ED-005 (SSL) resolved — no production access without them
- PM-ED-007 (FBR) resolved — regulatory compliance before public revenue

---

## Who Can Modify This Register

| Action | Who |
|---|---|
| Add new AUTO-CLOSED or SAFE-DEFAULT item | AI (autonomous) |
| Add new OWNER-DECISION item | AI (then notify owner) |
| Add new EXTERNAL-DEPENDENCY item | AI (then notify owner) |
| Add new OUT-OF-SCOPE item | AI (with FEATURE_SCOPE evidence) |
| Reopen a closed item | AI (with trigger evidence) |
| Reverse a SAFE-DEFAULT | Owner explicitly (AI executes) |
| Approve anchor modifications (PM-OD-002, PM-OD-003) | Owner only |
| Generate JWT key pair (PM-OD-001) | Owner/operator only |

---

## Memory Layer Maintenance Schedule

The memory layer should be updated:

| Event | Update Action |
|---|---|
| New implementation sprint completes | Update status of relevant SAFE-DEFAULT items |
| New feature deployed | Close related OUT-OF-SCOPE items (move to FINAL_CLASSIFIED) |
| New gap discovered | Add new entry; classify per rules above |
| Architecture changes | Review and update all AUTO-CLOSED items referencing changed code |
| Owner reverses a decision | Update SAFE-DEFAULT entry; update affected authority docs |
| External dependency provisioned | Update EXTERNAL-DEPENDENCY entry to RESOLVED |

The FINAL_CLASSIFIED_REGISTER.md Phase History table should be updated at the start of each new phase.

---

## Integration with Other Registers

The memory layer does not replace; it supplements:

| Register | Relationship to Memory Layer |
|---|---|
| BACKEND_GAP_REGISTER.md | Source of evidence for PM-AC/PM-SD items about backend gaps |
| BACKEND_RISK_REGISTER.md | Source of evidence for PM-OD/PM-SD items about risks |
| FEATURE_GAP_REGISTER.md | Source of PM-OS items (FGAPs map 1:1 to PM-OS entries) |
| TBD_RESOLUTION_REGISTER.md | Source of PM-AC items for TBD resolutions |
| PRODUCT_DECISION_REGISTER.md | Source of PM-AC and PM-SD items for PDC decisions |
| OWNER_CONFIRMATION_REGISTER.md | Source of PM-SD items for OC decisions |
| UNRESOLVABLE_ITEMS_REGISTER.md | Source of PM-OD items (OR items map 1:1 to PM-OD entries) |
| FINAL_CLASSIFIED_REGISTER.md (08_reports/) | Predecessor to this register; updated here |

When a source register is updated, check whether the corresponding memory layer entry needs updating.

---

## The Non-Rediscovery Guarantee

The goal of this memory layer is to ensure:

> **No decision, resolution, or confirmation that was derived with effort must ever be re-derived.**

If a future AI session would spend time investigating something this register already answers, the register has failed. When a fact is added to this register, it is added precisely because the work to establish it was significant and should not be repeated.

The measure of success: a new AI session that loads FINAL_CLASSIFIED_REGISTER.md before any investigation should be able to answer 90% of common questions about prior decisions without any additional code inspection.
