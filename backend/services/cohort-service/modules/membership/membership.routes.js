function registerMembershipRoutes({ app, membershipService }) {
  app.post('/cohorts/:cohortId/memberships', (req, res) => {
    const result = membershipService.addLearnerToCohort({
      tenantId: req.body.tenantId,
      cohortId: req.params.cohortId,
      learnerId: req.body.learnerId,
      assignedBy: req.body.assignedBy,
      effectiveDate: req.body.effectiveDate,
      overrideFlags: req.body.overrideFlags,
      metadata: req.body.metadata,
    });

    res.status(result.status === 'assigned' ? 201 : 200).json(result);
  });

  app.delete('/cohorts/:cohortId/memberships/:learnerId', (req, res) => {
    const result = membershipService.removeLearnerFromCohort({
      cohortId: req.params.cohortId,
      learnerId: req.params.learnerId,
      removedBy: req.body.removedBy,
      reason: req.body.reason,
    });

    res.status(result.status === 'removed' ? 200 : 404).json(result);
  });

  app.post('/cohorts/:cohortId/memberships:bulkEnroll', (req, res) => {
    const result = membershipService.bulkEnroll({
      tenantId: req.body.tenantId,
      cohortId: req.params.cohortId,
      learnerIds: req.body.learnerIds || [],
      assignedBy: req.body.assignedBy,
      effectiveDate: req.body.effectiveDate,
      overrideFlags: req.body.overrideFlags,
      metadata: req.body.metadata,
    });

    res.status(200).json(result);
  });

  app.get('/cohorts/:cohortId/memberships', (req, res) => {
    const result = membershipService.listCohortMemberships({
      cohortId: req.params.cohortId,
      state: req.query.state,
      page: Number(req.query.page || 1),
      pageSize: Number(req.query.pageSize || 50),
    });

    res.status(200).json(result);
  });
}

module.exports = {
  registerMembershipRoutes,
};
