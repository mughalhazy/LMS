# Skill Analytics API Contract (service-internal)

## Metrics

### Progression metrics
`progression_metrics(tenant_id, learner_id, skill_id, target_level, time_window_days=30)`

Returns:
- `baseline_proficiency`
- `current_proficiency`
- `absolute_change`
- `velocity`
- `milestone_attainment`

### Gap detection
`detect_skill_gaps(tenant_id, learner_id, role_profile_id, urgency_factor=1.0)`

Returns ranked gaps with:
- `gap`
- `severity`
- `priority`
- `recommended_interventions`

### Mastery scoring
`mastery_scoring(tenant_id, learner_id, skill_id, weights...)`

Returns:
- `mastery_score`
- `confidence_adjusted_score`
- `mastery_band`
- `confidence`

### Learning trends
`learning_trends(tenant_id, learner_id, skill_id)`

Returns:
- `samples`
- `trend_slope`
- `moving_average`
- `trend_label`
