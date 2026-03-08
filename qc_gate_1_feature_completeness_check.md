issue_type
missing_module
module
engagement_and_motivation
description
Feature inventory does not define a dedicated gamification/engagement capability (e.g., points, leaderboards, missions, social badges). For enterprise LMS deployments, these are commonly required to improve voluntary learning participation beyond compliance training.
severity
medium
recommended_fix
Add a new module (or expand `learning management`) with features such as Gamification Rules, Points & Leaderboards, Challenges/Campaigns, and Engagement Analytics.

issue_type
overlap_duplicate_risk
module
learning management + mobile access
description
`Learning Notifications` (learning management) and `Mobile Push Notifications` (mobile access) overlap functionally as assignment/due-date alerting capabilities. This can create ownership ambiguity and duplicate implementation if channel orchestration is not explicitly separated from channel delivery.
severity
medium
recommended_fix
Define `Learning Notifications` as orchestration/policy (triggering, cadence, audience rules) and `Mobile Push Notifications` as a delivery channel implementation. Document cross-module ownership and avoid duplicate business logic.

issue_type
grouping_adjustment
module
course authoring
description
`SCORM/xAPI/AICC Packaging` is grouped under course authoring, but in enterprise LMS operating models this is often split between authoring and standards/compliance governance. Current placement is acceptable but may obscure operational ownership for compatibility validation.
severity
low
recommended_fix
Keep feature in authoring but add a shared ownership note to standards/compliance operations (e.g., validation service, conformance testing) to prevent lifecycle gaps.
