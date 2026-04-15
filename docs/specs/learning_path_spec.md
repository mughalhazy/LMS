operation
path_creation | Creates a learning path with metadata (path_id, title, description, owner, audience, version, status), supports draft/publish lifecycle, and validates referenced courses exist and are publishable.
course_sequencing | Defines ordered and branched node graph using sequence_index, prerequisite_links, optional elective groups, and milestone checkpoints; enforces acyclic graph and minimum/maximum elective constraints.
completion_rules | Configures path completion logic (all_required_complete, required_plus_n_electives, milestone_based, score_threshold), due-date policy, and recertification interval with grace windows.

path_structure
path | path_id, tenant_id, title, description, status(draft|published|archived), owner_id, version, created_at, updated_at
path_node | node_id, path_id, node_type(course|assessment|milestone), ref_id, sequence_index, is_required, min_score, estimated_duration_mins
path_edge | edge_id, path_id, from_node_id, to_node_id, relation(prerequisite|next|branch), condition(optional)
elective_group | group_id, path_id, name, min_select, max_select, node_ids[]
path_assignment_scope | scope_id, path_id, assignment_type(role|department|location|manual), target_ref, effective_from, effective_to

rules
creation_validation | Path must contain at least one required node before publish; all referenced courses/assessments must be active.
sequence_validation | Graph must be acyclic; each non-entry required node must have at least one upstream path; branch merge points must be explicit.
unlock_logic | A node unlocks when all prerequisite edges are satisfied and any conditional rule evaluates true.
completion_evaluation | Path is complete when all required nodes are completed and elective minimums are met (or configured completion mode criteria satisfied).
score_policy | If min_score is set on a node, completion requires score >= min_score; otherwise pass/fail status from source course applies.
time_policy | If due_date exists, overdue status is set when completion timestamp exceeds due_date; overdue does not auto-fail unless strict_due_date=true.
recertification | If recertification_interval_days is set, completion expires at completed_at + interval; learner re-enters in-progress state after expiry.
auditability | All path structure and rule changes must be versioned with actor, timestamp, and change_reason for compliance traceability.
