class InMemoryMembershipRepository {
  constructor({ cohorts = [], users = [], memberships = [] } = {}) {
    this.cohorts = new Map(cohorts.map((c) => [c.cohortId, c]));
    this.users = new Map(users.map((u) => [u.userId, u]));
    this.memberships = new Map(memberships.map((m) => [m.cohortMembershipId, m]));
  }

  getCohortById(cohortId) {
    return this.cohorts.get(cohortId) || null;
  }

  getUserById(userId) {
    return this.users.get(userId) || null;
  }

  findMembership(cohortId, learnerId) {
    for (const membership of this.memberships.values()) {
      if (membership.cohortId === cohortId && membership.learnerId === learnerId) {
        return membership;
      }
    }
    return null;
  }

  insertMembership(membership) {
    this.memberships.set(membership.cohortMembershipId, membership);
    return membership;
  }

  updateMembership(membershipId, patch) {
    const existing = this.memberships.get(membershipId);
    if (!existing) return null;
    const merged = { ...existing, ...patch, updatedAt: new Date().toISOString() };
    this.memberships.set(membershipId, merged);
    return merged;
  }

  listMemberships({ cohortId, state, page = 1, pageSize = 50 } = {}) {
    const offset = (page - 1) * pageSize;
    const filtered = Array.from(this.memberships.values()).filter((m) => {
      if (cohortId && m.cohortId !== cohortId) return false;
      if (state && m.state !== state) return false;
      return true;
    });

    return {
      total: filtered.length,
      page,
      pageSize,
      records: filtered.slice(offset, offset + pageSize),
    };
  }
}

module.exports = {
  InMemoryMembershipRepository,
};
