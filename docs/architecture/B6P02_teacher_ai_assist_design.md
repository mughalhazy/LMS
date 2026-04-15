# B6P02 — Teacher AI Assist Design

## 1) Objective
Define **assistive-only AI tools** for teachers that reduce content-authoring time while preserving full teacher control.

This capability covers:
- course outline generation
- quiz draft creation
- improvement suggestions
- content summarization

This capability does **not** publish or execute teacher decisions; it only drafts and recommends.

---

## 2) Capability Design

### 2.1 Capability Metadata
| Field | Value |
|---|---|
| capability_id | `intelligence.teacher_ai_assist` |
| capability_type | `ai_assistive` |
| primary_users | teacher, instructional designer |
| integration_mode | embedded teacher authoring workflow |
| success_goal | reduce teacher drafting effort and iteration cycles |

### 2.2 Functional Scope
| Function | Inputs | Output Type | Teacher Action Required |
|---|---|---|---|
| Generate course outline | topic, level, duration, learning outcomes, pedagogy preferences | module/lesson draft outline | review, edit, save |
| Create quiz drafts | selected lesson/module outcomes, desired difficulty mix, question type constraints | draft question set + rationale + answer key draft | review, edit, assign/publish via assessment workflow |
| Suggest improvements | existing draft lesson/quiz metadata, readability targets, curriculum alignment hints | suggested edits and alternatives | accept/reject each suggestion |
| Summarize content | lesson text, uploaded notes, transcript chunks | teacher-facing summary variants (short/standard/detailed) | choose summary and insert manually |

### 2.3 Guardrails (QC FIX RE QC 10/10)
1. **No auto-publishing**: AI cannot publish courses, lessons, or quizzes. Only teacher-initiated publish through existing workflow.
2. **Assistive-only posture**: AI outputs are proposals/drafts; teacher remains the decision authority.
3. **No assessment engine overlap**: AI can draft quiz items, but scoring logic, exam delivery rules, attempt policies, and grade finalization stay in assessment engine.
4. **Suggestion vs execution split**: AI service returns recommendations with confidence/rationale; execution is performed only by teacher actions in course tooling.
5. **No duplication of content logic**: canonical validation rules (taxonomy alignment, publish eligibility, content versioning) remain in content/course services; AI references them but does not re-implement them.

### 2.4 Non-Functional Expectations
- Explainability: each suggestion includes reason and source context pointer.
- Editability: every generated artifact is editable before persistence.
- Auditability: store prompt-to-output trace metadata and teacher accept/reject actions.
- Latency targets: fast draft generation for in-flow authoring experience.

---

## 3) Workflow Integration

### 3.1 Integration with Course Creation Workflows
Teacher AI Assist is embedded at four points in existing course authoring:

1. **Course setup step**
   - Teacher enters goals/audience.
   - AI proposes outline draft.
   - Teacher edits + confirms before saving draft.

2. **Lesson authoring step**
   - Teacher opens lesson draft.
   - AI suggests enrichment, clarity improvements, remediation variants.
   - Teacher accepts/rejects per suggestion.

3. **Quiz authoring handoff step**
   - Teacher requests quiz drafts from selected outcomes.
   - AI generates candidate questions only.
   - Teacher explicitly forwards approved items into assessment workflow.

4. **Pre-publish review step**
   - Teacher requests summary for quality review/checklists.
   - AI provides concise overview and identified gaps.
   - Teacher resolves issues and uses standard publish flow.

### 3.2 Separation of Suggestion vs Execution
| Stage | Owned by | AI Role | Execution Authority |
|---|---|---|---|
| Draft generation | teacher authoring UI + AI assist service | produce draft/suggestions | none (proposal only) |
| Validation | content/course services | optional validation hints | authoritative service rules |
| Publish | course workflow service | no direct role | teacher-triggered publish only |
| Assessment release/scoring | assessment engine | no direct role except draft suggestions upstream | assessment engine + teacher policies |

### 3.3 Service Boundaries and Contracts
- **AI Assist Service**
  - owns prompt orchestration, suggestion formatting, rationale payloads.
  - stores assistive artifacts as draft suggestions, not canonical course truth.

- **Course/Content Services (system of record)**
  - own modules, lessons, version history, publish state.
  - apply final validations and persistence.

- **Assessment Engine (system of record for assessments)**
  - owns quiz lifecycle, delivery policy, grading and analytics computation.
  - receives only teacher-approved quiz items.

### 3.4 Event and Data Flow (High Level)
1. Teacher requests assist action from authoring UI.
2. AI Assist Service returns suggestion payload (`draft_id`, `suggestion_type`, `rationale`, `confidence`).
3. Teacher applies manual edits and accepts/rejects suggestions.
4. Teacher saves to content/course services as normal draft updates.
5. Optional audit events emitted for assist usage and acceptance metrics.

---

## 4) Time-Saving Design
- One-click initial outline drafts reduce blank-page authoring time.
- Batched quiz draft generation reduces repetitive question writing effort.
- In-context improvement suggestions reduce back-and-forth review rounds.
- Multi-length summarization accelerates teacher review before release.
- Reusable prompt presets (subject, level, tone) reduce repeated setup.

---

## 5) Acceptance Criteria
1. Teacher can generate outlines, quiz drafts, suggestions, and summaries inside course creation workflow.
2. Every AI artifact is editable before save/publish.
3. No endpoint or background job can auto-publish AI-generated content.
4. Assessment scoring/publishing logic remains exclusively in assessment engine.
5. Suggestion payloads are clearly marked as non-authoritative recommendations.
6. No duplicated publish/validation business logic exists in AI assist service.

---

## 6) Out-of-Scope
- Autonomous course publishing.
- Autonomous grading or assessment release.
- Replacement of teacher instructional judgment.
- Migration of canonical content or assessment logic into AI service.
