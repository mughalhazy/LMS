const MembershipState = {
  ACTIVE: 'active',
  REMOVED: 'removed',
  WAITLISTED: 'waitlisted',
};

const AssignmentMode = {
  MANUAL: 'manual',
  RULE_BASED: 'rule_based',
  BULK_IMPORT: 'bulk_import',
};

/**
 * Cohort membership entity factory.
 */
function createMembershipRecord({
  cohortMembershipId,
  tenantId,
  cohortId,
  learnerId,
  state = MembershipState.ACTIVE,
  assignmentMode = AssignmentMode.MANUAL,
  assignedBy,
  effectiveDate,
  metadata,
}) {
  return {
    cohortMembershipId,
    tenantId,
    cohortId,
    learnerId,
    state,
    assignmentMode,
    assignedBy,
    effectiveDate,
    metadata: metadata || {},
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    removedAt: null,
  };
}

module.exports = {
  MembershipState,
  AssignmentMode,
  createMembershipRecord,
};
