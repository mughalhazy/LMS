# REPOSITORY_HYGIENE_EXECUTION_GUIDELINES

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: Shared

Companion: SAFE_REPOSITORY_HYGIENE_POLICY.md, REVISED_DECISION_ESCALATION_MATRIX.md

---

## PURPOSE

Step-by-step guidelines for executing `SAFE_REPOSITORY_HYGIENE` (SRH) actions. Covers pre-execution checks, execution patterns, post-execution verification, and session documentation requirements.

---

## BEFORE STARTING ANY SRH SESSION

Read in order:

1. `docs/07_governance/AI_OPERATING_CONTEXT.md` — project context and frozen decisions
2. `docs/07_governance/REVISED_DECISION_ESCALATION_MATRIX.md` — current tier definitions
3. `docs/07_governance/SAFE_REPOSITORY_HYGIENE_POLICY.md` — SRH definition and hard boundaries
4. `docs/08_reports/APPROVAL_RECLASSIFICATION_REPORT.md` — which specific items are classified SRH

**Do not execute any SRH action that is not on the SRH execution queue** in APPROVAL_RECLASSIFICATION_REPORT.md or an equivalent reclassification document. New items discovered mid-session must be classified before being executed.

---

## EXECUTION PATTERN: ADDING README.md FILES

### Pre-check
- Verify the target directory does not already have a README.md
- Verify the directory is not in PROTECTED_AREAS (docs/anchors/, shared/models/, event_topics.json, service-manifest.json, integrations/payments/, integrations/communication/)

### Content rules
- State the directory's purpose in 1–2 sentences
- State the classification (ACTIVE / LEGACY / NEEDS-REVIEW) if known
- Point to the authoritative documentation (do not duplicate authority content)
- Do NOT claim that this README is an authority document
- Do NOT describe architecture decisions — link to the authority doc that makes them

### Template
```markdown
# <directory-name>/

Status: [ACTIVE | LEGACY | NEEDS-REVIEW]
Classified: <date>

## Purpose
<One paragraph describing what this directory contains and why it exists>

## Used By
<What imports or depends on this directory — or "TBD: pending import analysis">

## Related Authority Docs
- <Link to the relevant governance or architecture document>
```

### Post-check
- Read the file back and confirm it contains no unintended authority claims
- Confirm no application code was modified

---

## EXECUTION PATTERN: ADDING STATUS BANNERS

Status banners add a clearly-marked notice at the top of a document to signal its lifecycle status. They do not modify the document's content.

### Pre-check
- Confirm the target document is not in docs/anchors/ (those require REQUIRES_APPROVAL)
- Confirm the banner type is appropriate: DEPRECATED, SUPERSEDED, HISTORICAL, LEGACY

### Banner templates

**DEPRECATED** (replaced by a specific document):
```
> **DEPRECATED** — Superseded by: <path/to/replacement.md>
> Reason: <one sentence>
> Retained as historical record. Last reviewed: <date>
```

**SUPERSEDED** (authority transferred):
```
> **SUPERSEDED** — Authority transferred to: <path/to/replacement.md>
> This document is retained for audit trail purposes. Last reviewed: <date>
```

**HISTORICAL** (point-in-time record, no longer active):
```
> **HISTORICAL** — This document reflects system state as of <date>.
> It is retained as an audit trail record and is not authoritative.
```

**LEGACY** (code directory, still present but superseded):
```
> **LEGACY** — This module has been superseded by: <path/to/replacement/>
> It is retained pending owner confirmation of retirement.
> Do not import this module in new code.
```

### Post-check
- Read the document top to confirm the banner is correctly placed (first content after frontmatter)
- Confirm document body was not accidentally modified

---

## EXECUTION PATTERN: MOVING DOCUMENTATION FILES

Moving a .md file from one docs/ subdirectory to another — e.g., from docs/qc/ to docs/_archive/.

### Pre-check
1. Confirm source is not in docs/anchors/ (protected)
2. Confirm destination directory exists
3. Read the file to check for any cross-references from other documents that point to the source path
4. Grep for the source filename in docs/ to find all incoming links

```powershell
Get-ChildItem "D:\SaaS\LMS\Repo\docs" -Recurse -Filter "*.md" |
  Select-String -Pattern "<filename>" | Select-Object Path, LineNumber, Line
```

### Execution
- Copy file to new location
- Add SUPERSEDED/MOVED banner at top of original file (do not delete original)
- Add note at top of new copy: "Moved from: <original path>"
- Update any known cross-references found in pre-check

### Post-check
- Confirm file exists in both source (with banner) and destination
- Confirm no documentation links are now broken

---

## EXECUTION PATTERN: MOVING VALIDATION/QC SCRIPTS

Moving non-production Python scripts from docs/qc/ to validation/.

### Pre-check (critical)

Before moving any .py file:

1. **Read the script** to identify all relative path references (`../`, `../../`, `Path(__file__).parent`)
2. **Map the new relative paths** — what changes when the file moves from `docs/qc/` to `validation/`?
   - `docs/qc/` to `validation/` is: one level shallower (from 2 dirs deep to 1 dir deep in Repo)
   - Relative path adjustments: `../../backend/` becomes `../backend/`
3. **Confirm the script is non-production** — verify it is not imported by any backend service
   ```powershell
   Select-String -Path "D:\SaaS\LMS\Repo\backend\**\*.py" -Pattern "<script_name>"
   ```
4. **Confirm the script has no .pyc companion in git** — if it does, the .pyc implies production use

### Execution (per script)
1. Read script and map all path changes needed
2. Write updated script to `validation/<script_name>.py` with corrected paths
3. Add status comment at top of original in docs/qc/: `# MOVED: see validation/<script_name>.py`
4. Do NOT delete the original (deletion requires REQUIRES_APPROVAL)

### Post-check
- Run the moved script from `validation/` directory to confirm no import errors:
  ```powershell
  py -3 "D:\SaaS\LMS\Repo\validation\<script_name>.py" 2>&1 | Select-Object -First 10
  ```
- Confirm original docs/qc/ script still exists (with MOVED comment)

---

## EXECUTION PATTERN: .GITIGNORE ADDITIONS

Adding entries to .gitignore to cover artifact types that are already excluded by convention.

### Pre-check
1. Read the current `.gitignore` to confirm the entry is genuinely missing
2. Confirm the artifact type is never intentionally committed (e.g., `.pyc` — never; `package-lock.json` — always committed)
3. Confirm adding the entry would not inadvertently exclude a currently-tracked file

```powershell
# Check if adding .foo/ would untrack anything currently tracked
git -c safe.directory="D:/SaaS/LMS/Repo" -C "D:\SaaS\LMS\Repo" ls-files "*.foo" | Select-Object -First 5
```

### Execution
- Append the new entry under an appropriate comment section
- Never remove existing entries

### Post-check
- Confirm the added entry appears in the file
- Confirm no previously-tracked files are now untracked:
  ```powershell
  git -c safe.directory="D:/SaaS/LMS/Repo" -C "D:\SaaS\LMS\Repo" status
  ```

---

## EXECUTION PATTERN: CLASSIFICATION MATRIX UPDATES

Updating DOCUMENT_INVENTORY.md, DOCUMENT_CLASSIFICATION_MATRIX.md, or REPOSITORY_CLASSIFICATION_MATRIX.md to reflect changes made during hygiene.

### Rule
Classification matrices are always updated AFTER the underlying change, not before.

### Execution
- Add/update the relevant row in the matrix
- Update the "Last Reviewed" date in the document frontmatter
- If the total count changes, update any summary tables that reference the count

---

## WHAT TO DO WHEN SOMETHING UNEXPECTED IS DISCOVERED

During SRH execution, if you discover:
- A file that appears to need a change not covered by the current SRH queue
- A potential security issue
- An unexpected dependency or import that contradicts the SRH classification

**Stop executing the current action. Document the finding. Do not proceed.**

Add the finding to `docs/08_reports/REPOSITORY_NORMALIZATION_REPORT.md` or a new report as appropriate. Escalate to owner per the ESCALATION PROTOCOL in REVISED_DECISION_ESCALATION_MATRIX.md.

---

## SESSION OUTPUT REQUIREMENTS

At the end of any SRH session, produce a brief SRH execution report noting:

1. Which SRH items were executed (by SRH-NNN ID from APPROVAL_RECLASSIFICATION_REPORT.md)
2. Which items were skipped and why
3. Any new findings discovered during execution
4. Updated status of the SRH execution queue

This report may be a section in an existing session output document or a new file in docs/08_reports/.

---

## PROHIBITED DURING ANY SRH SESSION

Even though an SRH session has broad documentation authority, the following remain prohibited:

| Action | Even If It Seems Like Hygiene |
|---|---|
| Deleting any file | Must always use REQUIRES_APPROVAL |
| Modifying docs/anchors/ | Always REQUIRES_APPROVAL |
| Changing .py logic | Always REQUIRES_APPROVAL |
| Modifying shared/models/ | Always REQUIRES_APPROVAL |
| Modifying integrations/payments/ | Always REQUIRES_APPROVAL |
| Modifying service-manifest.json or event_topics.json | Always REQUIRES_APPROVAL |
| Writing to C: drive | Always PROHIBITED |
| Modifying .yml/.yaml infrastructure configs | Always REQUIRES_APPROVAL |
