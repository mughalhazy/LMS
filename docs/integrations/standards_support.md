standard
supported_features
implementation_notes

SCORM 1.2
- Launch and tracking via LMS API (`LMSInitialize`, `LMSSetValue`, `LMSCommit`, `LMSFinish`)
- Completion status, score reporting, lesson location, suspend/resume data
- Basic sequencing through SCO-level navigation within a package
Use a SCORM runtime wrapper for browser communication, enforce 4KB suspend_data limits, and normalize completion data into internal progress records.

SCORM 2004
- Full SCORM Runtime API support (`Initialize`, `GetValue`, `SetValue`, `Commit`, `Terminate`)
- Sequencing and Navigation (Simple Sequencing rules)
- Richer data model including interactions, objectives, and success/completion separation
Support 2nd/3rd/4th edition manifests, validate sequencing rules at import time, and map `cmi.success_status` + `cmi.completion_status` to LMS completion policies.

xAPI
- Statement ingestion (`actor`, `verb`, `object`, `result`, `context`)
- LRS integration for storing and querying learning records
- Support for learning events outside LMS (mobile apps, simulations, offline sync)
Provide an xAPI endpoint and/or connector to external LRS, secure with OAuth2, and implement verb/profile governance to avoid inconsistent reporting semantics.

LTI 1.3
- OIDC login initiation and LTI message launch (Resource Link Request)
- Deep Linking (Content-Item selection)
- Names and Role Provisioning Services (NRPS) and Assignments & Grades Service (AGS)
Implement JWT validation with platform JWKS rotation, enforce nonce/state checks, and maintain per-platform registrations (issuer, client_id, deployment_id, keyset URL).
