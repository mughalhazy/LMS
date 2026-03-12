# LMS Skills Graph Model

| node_type | relationships | properties |
|---|---|---|
| **SkillDomain** (taxonomy L1) | `SkillDomain CONTAINS SkillCategory` | `domain_id`, `name`, `description`, `industry` |
| **SkillCategory** (taxonomy L2) | `SkillCategory BELONGS_TO SkillDomain`; `SkillCategory CONTAINS Skill` | `category_id`, `name`, `description`, `sequence_order` |
| **Skill** (taxonomy L3, atomic skill) | `Skill BELONGS_TO SkillCategory`; `Skill PREREQUISITE_OF Skill`; `Skill RELATED_TO Skill`; `Skill PART_OF SkillCluster`; `Skill TAGGED_AS SkillTag` | `skill_id`, `name`, `description`, `difficulty_base`, `version`, `status(active/deprecated)` |
| **SkillCluster** (optional rollup) | `SkillCluster GROUPS Skill`; `SkillCluster MAPS_TO RoleProfile` | `cluster_id`, `name`, `goal`, `weighting_strategy` |
| **SkillTag** | `SkillTag LABELS Skill` | `tag_id`, `name`, `type(technical/soft/tool/domain)` |
| **Course** | `Course TEACHES Skill` (edge has `coverage_level`, `hours`); `Course REQUIRES Skill` (entry requirement); `Course HAS Module`; `Course ALIGNS_TO Certification` | `course_id`, `title`, `level`, `duration_hours`, `delivery_mode`, `owner`, `status` |
| **Module** | `Module PART_OF Course`; `Module TEACHES Skill`; `Module ASSESSED_BY Assessment` | `module_id`, `title`, `order`, `duration_hours`, `learning_outcomes` |
| **Assessment** | `Assessment MEASURES Skill`; `Assessment PART_OF Module/Course`; `Assessment PRODUCES UserSkillEvidence` | `assessment_id`, `type(quiz/project/practical)`, `max_score`, `rubric_version`, `passing_score` |
| **User** | `User HAS UserSkill`; `User ENROLLED_IN Course`; `User TARGETS RoleProfile`; `User MEMBER_OF Team` | `user_id`, `name`, `org_id`, `role`, `timezone` |
| **UserSkill** (user skill level state) | `UserSkill FOR User`; `UserSkill ON Skill`; `UserSkill UPDATED_BY UserSkillEvidence`; `UserSkill VALIDATED_BY Assessor` | `user_skill_id`, `current_level`, `confidence`, `last_assessed_at`, `decay_rate`, `source(self/assessment/manager)` |
| **UserSkillEvidence** | `UserSkillEvidence FROM Assessment/Course/Experience`; `UserSkillEvidence SUPPORTS UserSkill` | `evidence_id`, `score`, `normalized_score`, `evidence_date`, `artifact_url`, `verified` |
| **SkillLevelScale** (framework for levels) | `SkillLevelScale DEFINES SkillLevel`; `Skill USES SkillLevelScale` | `scale_id`, `name` (e.g., `Novice→Expert`), `levels_count` |
| **SkillLevel** | `SkillLevel BELONGS_TO SkillLevelScale`; `UserSkill AT SkillLevel` | `level_id`, `ordinal(0-5)`, `label`, `descriptor`, `expected_behaviors` |
| **RoleProfile** | `RoleProfile REQUIRES Skill` (edge has `target_level`, `priority`); `RoleProfile OWNED_BY OrgUnit` | `role_profile_id`, `title`, `job_family`, `seniority`, `version` |

## Relationship Rules (graph constraints)

| node_type | relationships | properties |
|---|---|---|
| **Skill ↔ Skill** | `PREREQUISITE_OF` must be acyclic; `RELATED_TO` is symmetric; `PART_OF` supports many-to-many clusters | `prerequisite_strength(required/recommended)`, `relation_weight` |
| **Course ↔ Skill mapping** | Each `Course TEACHES Skill` edge stores coverage metadata and expected exit level delta | `coverage_level(intro/intermediate/advanced)`, `skill_gain_expected(0-5)`, `evidence_weight` |
| **User skill levels** | `UserSkill.current_level` must map to valid `SkillLevel.ordinal`; recomputed from weighted evidence with decay | `level_calc_method(weighted_recent_evidence)`, `staleness_days`, `min_evidence_count` |

## Suggested User Skill Levels

| node_type | relationships | properties |
|---|---|---|
| **SkillLevel** | `0..5 progression` applied through `UserSkill AT SkillLevel` | `0-Unaware`, `1-Awareness`, `2-Basic`, `3-Working`, `4-Proficient`, `5-Expert` |

