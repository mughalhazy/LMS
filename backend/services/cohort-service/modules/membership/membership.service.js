const { randomUUID } = require('crypto');
const {
  MembershipState,
  AssignmentMode,
  createMembershipRecord,
} = require('./entities');

class CohortMembershipService {
  constructor({ repository }) {
    this.repository = repository;
  }

  addLearnerToCohort({
    tenantId,
    cohortId,
    learnerId,
    assignedBy,
    effectiveDate = new Date().toISOString(),
    assignmentMode = AssignmentMode.MANUAL,
    overrideFlags = {},
    metadata = {},
  }) {
    this.#validateCohortAndLearner(cohortId, learnerId);

    const cohort = this.repository.getCohortById(cohortId);
    const existingMembership = this.repository.findMembership(cohortId, learnerId);

    if (existingMembership && existingMembership.state === MembershipState.ACTIVE && !overrideFlags.allow_duplicates) {
      return {
        status: 'skipped',
        reason: 'duplicate_membership',
        membership: existingMembership,
      };
    }

    const activeCount = this.repository
      .listMemberships({ cohortId, state: MembershipState.ACTIVE, pageSize: Number.MAX_SAFE_INTEGER })
      .total;

    if (cohort.capacity && activeCount >= cohort.capacity) {
      const waitlisted = createMembershipRecord({
        cohortMembershipId: randomUUID(),
        tenantId,
        cohortId,
        learnerId,
        state: MembershipState.WAITLISTED,
        assignmentMode,
        assignedBy,
        effectiveDate,
        metadata,
      });
      this.repository.insertMembership(waitlisted);
      return {
        status: 'waitlisted',
        reason: 'cohort_capacity_reached',
        membership: waitlisted,
      };
    }

    const membership = createMembershipRecord({
      cohortMembershipId: randomUUID(),
      tenantId,
      cohortId,
      learnerId,
      state: MembershipState.ACTIVE,
      assignmentMode,
      assignedBy,
      effectiveDate,
      metadata,
    });

    this.repository.insertMembership(membership);

    return {
      status: 'assigned',
      membership,
      auditEvent: 'CohortMembersAssigned',
    };
  }

  removeLearnerFromCohort({ cohortId, learnerId, removedBy, reason = 'manual_unassign' }) {
    const existingMembership = this.repository.findMembership(cohortId, learnerId);
    if (!existingMembership || existingMembership.state === MembershipState.REMOVED) {
      return { status: 'skipped', reason: 'membership_not_found' };
    }

    const membership = this.repository.updateMembership(existingMembership.cohortMembershipId, {
      state: MembershipState.REMOVED,
      removedAt: new Date().toISOString(),
      removedBy,
      removalReason: reason,
    });

    return {
      status: 'removed',
      membership,
      auditEvent: 'CohortMembersAssigned',
    };
  }

  bulkEnroll({
    tenantId,
    cohortId,
    learnerIds,
    assignedBy,
    effectiveDate,
    overrideFlags,
    metadata,
  }) {
    const summary = {
      assigned: 0,
      skipped: 0,
      failed: 0,
    };

    const membershipRecords = [];
    const conflictReport = [];
    const waitlistEntries = [];

    for (const learnerId of learnerIds) {
      try {
        const result = this.addLearnerToCohort({
          tenantId,
          cohortId,
          learnerId,
          assignedBy,
          effectiveDate,
          assignmentMode: AssignmentMode.BULK_IMPORT,
          overrideFlags,
          metadata,
        });

        if (result.status === 'assigned') {
          summary.assigned += 1;
          membershipRecords.push(result.membership);
        } else if (result.status === 'waitlisted') {
          summary.skipped += 1;
          waitlistEntries.push(result.membership);
          conflictReport.push({ learnerId, reason: result.reason });
        } else {
          summary.skipped += 1;
          conflictReport.push({ learnerId, reason: result.reason });
        }
      } catch (error) {
        summary.failed += 1;
        conflictReport.push({ learnerId, reason: error.message });
      }
    }

    return {
      membershipRecords,
      assignmentSummary: summary,
      conflictReport,
      waitlistEntries,
      auditEvent: 'CohortMembersAssigned',
    };
  }

  listCohortMemberships({ cohortId, state, page, pageSize }) {
    return this.repository.listMemberships({ cohortId, state, page, pageSize });
  }

  #validateCohortAndLearner(cohortId, learnerId) {
    const cohort = this.repository.getCohortById(cohortId);
    if (!cohort) {
      throw new Error(`cohort_not_found:${cohortId}`);
    }

    const user = this.repository.getUserById(learnerId);
    if (!user) {
      throw new Error(`learner_not_found:${learnerId}`);
    }
  }
}

module.exports = {
  CohortMembershipService,
};
