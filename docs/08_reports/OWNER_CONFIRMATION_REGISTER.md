# OWNER CONFIRMATION REGISTER

Status: Active
Date: 2026-06-23
Phase: Phase 2.95 — Residual Decision Collapse
Owner: Human (confirmation required)

---

## Purpose

This register lists all decisions classified as OWNER_CONFIRMATION_ONLY during Phase 2.95. Each has a recommended path that implementation may follow unless the owner explicitly rejects it. No action is blocked while awaiting confirmation.

---

## Usage Rule

**Implementation proceeds on the recommended path. If the owner provides a different instruction, adjust before that sprint's implementation begins. Silence = acceptance.**

---

## OC-001: CheckoutService Persistence Timeline

| Field | Value |
|---|---|
| **ID** | OC-001 |
| **Source** | PDC-001 |
| **Question** | When should checkout-service receive SQLite persistence? |
| **Recommended path** | Keep InMemoryCheckoutStore for development. Add `store_db.py` to checkout-service in a dedicated persistence sprint. Frontend is unaffected in both states. |
| **What changes if rejected** | If owner wants persistence now, add `store_db.py` to checkout-service (same pattern as enrollment-service). No frontend changes. |
| **Frontend blocking** | No |
| **Sprint needed if confirmed** | Persistence sprint (backend only) |
| **Confirmation action required** | State preferred timeline: "persistence sprint before frontend launch" or "defer to post-launch." |

---

## OC-002: Cloud Deployment Target

| Field | Value |
|---|---|
| **ID** | OC-002 |
| **Source** | PDC-002 |
| **Question** | Which cloud provider and deployment target for production? |
| **Recommended path** | Use Docker Compose (`infrastructure/deployment/docker-compose.yml`) for local development and staging. Select cloud provider when ready for production deployment. |
| **What changes if rejected** | If owner selects a cloud provider now, align `deploy-backend.yml` to target cloud. No frontend changes. |
| **Frontend blocking** | No |
| **Sprint needed if confirmed** | DevOps/infrastructure sprint |
| **Confirmation action required** | State preferred cloud target when known (AWS / GCP / Azure / DigitalOcean / self-hosted VPS). |

---

## OC-003: File Upload API Endpoint

| Field | Value |
|---|---|
| **ID** | OC-003 |
| **Source** | PDC-003 |
| **Question** | Which HTTP service exposes the file/binary upload endpoint — content-service, media-service, or a new file-storage HTTP wrapper? |
| **Recommended path** | content-service handles content metadata registration. Binary upload (video, document, SCORM, image) targets media-service or a future file-storage HTTP wrapper. Frontend "upload content" form renders with a stub binary upload action until the endpoint is confirmed in a content sprint. |
| **What changes if rejected** | If owner wants file-storage HTTP wrapper first, add `backend/services/file-storage/app/main.py` (ASGI shim pattern) and register in manifest before content upload screen is implemented. |
| **Frontend blocking** | No — content metadata form can be built; binary upload is a stub until sprint confirms endpoint |
| **Sprint needed if confirmed** | Content sprint |
| **Confirmation action required** | Confirm which service owns binary upload: (A) content-service, (B) media-service, or (C) new file-storage HTTP wrapper. |

---

## OC-004: AI Tutor Scope Boundary

| Field | Value |
|---|---|
| **ID** | OC-004 |
| **Source** | PDC-007 |
| **Question** | Is the frontend AI feature limited to ai-tutor-service capabilities, or should the full "AI learning copilot" design be included in the initial build? |
| **Recommended path** | Build to confirmed services only: ai-tutor chat panel per lesson, recommendations widget on learner dashboard, course generation for admins. The broader "AI copilot" overlay (design doc) is deferred to a separate AI sprint. |
| **What changes if rejected** | If owner wants the full copilot vision immediately, an additional "copilot sprint" is needed to define the overlay design and map it to service capabilities before frontend builds those screens. |
| **Frontend blocking** | No — ai-tutor-service, recommendation-service, and course-generation-service screens can be built immediately |
| **Sprint needed if confirmed** | AI copilot sprint (design + implementation) if full vision chosen |
| **Confirmation action required** | Confirm: "ai-tutor-service scope is sufficient for MVP" or "include full copilot vision — defer to AI sprint." |

---

## Confirmation Summary — PHASE 3.25 UPDATE

| ID | Decision | Status | Path Proceeded |
|---|---|---|---|
| OC-001 | Checkout persistence | ✅ PROCEEDED — silence accepted (2026-06-23) | Keep InMemoryCheckoutStore for development; SQLiteCheckoutStore in persistence sprint |
| OC-002 | Cloud target | ✅ PROCEEDED — silence accepted (2026-06-23) | Docker Compose + GitHub Actions as confirmed default; cloud provider at owner discretion before production |
| OC-003 | File upload API | ✅ PROCEEDED — silence accepted (2026-06-23) | Content-service metadata + media-service binary; FileUpload component rendered with stub binary endpoint |
| OC-004 | AI tutor scope | ✅ PROCEEDED — silence accepted (2026-06-23) | ai-tutor-service + recommendation-service + course-gen-service built in initial sprint; copilot overlay = FGAP-003 |

**All 4 OWNER_CONFIRMATION_ONLY items: PROCEEDED per "silence = acceptance" rule.**
Frontend Authority Capture and Phase 3.25 gap elimination executed on all 4 recommended paths.

---

## Non-Action Default — RESOLVED

All 4 items proceeded on recommended paths. Register is CLOSED.

---

## See Also: Implementation Gaps

Items previously listed here as OC-005 (PWA offline) have been reclassified as IMPLEMENTATION_GAP. These are planned features requiring a sprint — not binary owner choices. See `FEATURE_GAP_REGISTER.md` for the full gap list (FGAP-001 through FGAP-006).
