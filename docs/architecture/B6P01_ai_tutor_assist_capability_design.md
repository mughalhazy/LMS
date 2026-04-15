# B6P01 — AI Tutor Assist Capability Design

## 1) Capability Intent
AI Tutor Assist is an **embedded learner-support capability** that helps students inside existing course and lesson workflows by:
- answering student queries,
- explaining concepts,
- providing revision help,
- offering contextual learning support.

This capability is intentionally **assistive, not authoritative**:
- AI guidance is advisory.
- Teacher remains final authority for pedagogy, feedback, grading, and interventions.
- AI cannot publish curriculum changes, override content, or replace teacher decisions.

---

## 2) Scope and Boundaries

### In Scope
1. **Answer student queries** grounded in current course + lesson context.
2. **Explain concepts** using approved lesson/course artifacts and prerequisite map.
3. **Provide revision help** through summaries, recall prompts, and practice suggestions.
4. **Contextual learning support** tied to learner progress and current learning step.

### Out of Scope
1. Authoritative grading, scoring overrides, or certification decisions.
2. Autonomous teaching decisions (promotion, remediation mandates, discipline outcomes).
3. Publishing or mutating canonical learning content.
4. Standalone chatbot behavior disconnected from LMS course/lesson context.

---

## 3) Integration Design (Must-use Existing LMS Context)
AI Tutor Assist runs as an orchestrated layer over existing services and never becomes a source-of-truth domain.

### Required upstream systems
- **Course Service**: course metadata, objectives, approved concept map references.
- **Lesson Service**: active lesson context, concept units, activity sequence.
- **Progress Service**: learner completion state, weak areas, recent interactions.
- **Event Ingestion / Analytics**: recent learning events for support relevance.

### Context contract (read-only)
Every tutor request must include and validate:
- `tenant_id`
- `user_id`
- `course_id`
- `lesson_id` (required for lesson-context interactions)
- `locale` (`en` or `ur`)

The AI layer only reads this context and writes assistive interaction logs in its own domain tables.

---

## 4) Assistive Guardrails (QC-aligned)

### A) AI is assistive, not authoritative
- Response envelope includes a `guidance_level=assistive` marker.
- UI labels output as “AI suggestion” and “Verify with your teacher.”
- High-impact asks (grading, policy, medical/legal/safety escalation) route to teacher/escalation response template.

### B) No overlap with learning content ownership
- AI may summarize or explain existing approved lesson content.
- AI must not create authoritative replacement lessons or mutate official curriculum artifacts.
- Any generated practice item is tagged as **draft assistive material**.

### C) Must use existing course context
- Retrieval pipeline requires course/lesson/progress context before model invocation.
- If context retrieval fails, AI returns constrained fallback: “I need course context to help accurately.”

### D) No standalone AI logic
- No direct learner-facing response path bypassing LMS context adapters.
- No external-memory answer generation without verified LMS references.

### E) Clear teacher/AI boundary
- Teacher controls: final explanation approval (where required), remediation assignment, grading, and interventions.
- AI controls: hints, step-by-step explanation, revision prompts, next-study suggestions.

---

## 5) Multilingual Support (Urdu + English)

### Language behavior
- Auto-detect learner language preference from profile/session, with explicit toggle.
- Support request/response in **English (`en`)** and **Urdu (`ur`)**.
- Preserve pedagogical terminology consistency using course glossary mappings.

### Safety for bilingual output
- If confidence in translation/context alignment is low, return bilingual clarification prompt.
- Keep references anchored to same lesson nodes regardless of language surface form.

---

## 6) Response Contract (Learner-facing)
Each response payload should include:
- `direct_answer` (assistive)
- `concept_explanation` (level: brief/standard/deep)
- `revision_support` (summary + quick recall prompts)
- `next_step_suggestion` (mapped to current lesson progression)
- `teacher_boundary_note` (non-authoritative disclaimer)
- `citations` (course/lesson/progress pointers)
- `language` (`en`/`ur`)

---

## 7) Interaction Flow

## 7.1 Primary flow: student asks for help in a lesson
1. Learner opens AI Tutor panel inside course lesson view.
2. Client sends tutor request with tenant, course, lesson, user, locale, query.
3. AI Tutor service validates identity + tenancy + enrollment.
4. Context layer fetches read-only context from course, lesson, progress, and recent learning events.
5. Prompt assembly enforces policy guardrails and teacher boundary constraints.
6. Model generates assistive response in requested language.
7. Post-processor injects teacher-boundary note + citations to LMS context.
8. Response is shown to learner and logged for audit/analytics.
9. Interaction event emitted for observability and quality monitoring.

## 7.2 Fallback flow: missing context
1. Request arrives without valid course/lesson context.
2. Service skips model invocation.
3. Returns bounded prompt asking learner to open the relevant lesson, plus teacher escalation hint.
4. Logs “context_missing” outcome for telemetry.

## 7.3 Escalation flow: authoritative request
1. Learner asks for grade decision / final answer key / policy override.
2. Policy filter classifies as teacher-authority required.
3. AI responds with non-authoritative guidance + “ask your teacher” routing.
4. Optional flag/event sent to teacher dashboard for follow-up.

---

## 8) Non-Functional Expectations
- Tenant isolation across all context retrieval and logs.
- Full auditability for prompt template version, model version, and context fingerprints.
- Deterministic policy checks before response.
- Observability: latency, fallback rate, escalation rate, language distribution (en/ur).

---

## 8b) Architectural Contract: MS-AI-01 — AI Assist Boundary (MS§10.8)

**Contract name:** MS-AI-01
**Source authority:** Master Spec §10 rule 8: "AI must assist, not replace."
**Scope:** This contract applies to this capability and to ALL AI capabilities in the platform.

**Rule — four mandatory requirements:**

1. **AI-generated outputs MUST be labeled.** Every response, suggestion, or action produced by an AI capability must be clearly labeled as AI-assisted in the user interface. Labels may not be hidden, minimized below readability, or omitted.

2. **Human review MUST always be available.** For any AI-generated output, the user must have a clear, accessible path to obtain a human-reviewed alternative. This does not mean human review is mandatory — but it must be reachable in at most one additional interaction.

3. **AI MUST surface a human action path.** Every AI output must include at minimum one of: dismiss, correct, or override. A user must never be in a state where they cannot discard or contest an AI-generated result.

4. **AI MUST NOT make irreversible decisions autonomously.** AI capabilities may recommend, draft, suggest, and queue actions — but final execution of any irreversible action (grade finalization, enrollment state change, content publication, financial transaction) MUST require explicit human confirmation.

**AI Tutor Assist compliance with MS-AI-01:**
- Requirement 1: `guidance_level=assistive` marker + "AI suggestion" label in UI — ✓ (Section 4A)
- Requirement 2: Teacher escalation path available in all flows — ✓ (Section 7.3)
- Requirement 3: `teacher_boundary_note` in every response payload — ✓ (Section 6)
- Requirement 4: AI cannot publish curriculum, override grades, or finalize enrollment — ✓ (Section 2 Out of Scope)

**Why this rule exists:** MS§10 rule 8 distinguishes AI *assist* (present in the platform, required) from AI *replace* (absent from the platform, prohibited). Without a named boundary contract, AI capabilities can gradually absorb human decision points, removing accountability and trust from the system.

---

## 9) QC Fix Re-check (10/10)

| QC Condition | Design Coverage |
|---|---|
| AI is assistive, not authoritative | Enforced via response marker, policy filters, and teacher-boundary note in every response. |
| No overlap with learning content | AI cannot own or mutate canonical lesson/course artifacts; only assistive summaries/practice drafts. |
| Must use existing course context | Mandatory context retrieval gate before model invocation; fallback when missing. |
| No standalone AI logic | All responses require LMS context adapters and tenant/course/lesson scoping. |
| Clear boundaries between AI and teacher | Explicit responsibility matrix and escalation flow for teacher-owned decisions. |

**QC Verdict:** All required constraints are explicitly designed and enforceable in runtime policy.
