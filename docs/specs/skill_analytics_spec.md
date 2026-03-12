# Skill Analytics Specification

## skill_metric: Skill Progress
## data_sources
- Learning activity events (course/module completion, practice sessions, assessment attempts)
- Time-series learner profile snapshots
- Skill-to-content mapping metadata

## algorithm
- Compute baseline proficiency per skill from first valid assessment or inferred starting level.
- Track proficiency deltas over time using weighted signals from completions, assessment scores, and recency.
- Produce progress as:
  - absolute change (`current_proficiency - baseline_proficiency`)
  - velocity (`change / time_window`)
  - milestone attainment (% of target level reached)

---

## skill_metric: Skill Gap Detection
## data_sources
- Target skill requirements (role, team, certification, or learning path)
- Current learner/team proficiency by skill
- Organizational benchmark distributions

## algorithm
- For each required skill, compute gap magnitude:
  - `gap = target_level - current_level`
- Classify gap severity with thresholds (e.g., critical, moderate, minor, none).
- Prioritize gaps by weighted impact:
  - `priority = gap * business_criticality * role_weight * urgency_factor`
- Output ranked gap list with recommended interventions (courses, coaching, projects).

---

## skill_metric: Skill Mastery Scoring
## data_sources
- Assessment performance (scores, attempt counts, question difficulty)
- Practical evidence (project outcomes, peer/manager validation, rubric evaluations)
- Retention signals (spaced re-checks, decay indicators)

## algorithm
- Normalize each evidence type to a common scale (0–1).
- Compute composite mastery score:
  - `mastery = w_assessment*A + w_practice*P + w_validation*V + w_retention*R`
- Apply confidence adjustment based on evidence volume/quality.
- Map numeric score to mastery bands (e.g., novice, developing, proficient, expert).
- Recalculate periodically with decay handling to reflect true current mastery.
