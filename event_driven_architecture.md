event_name
producer_service
consumer_services
purpose

EmployeeOnboarded
employee-service
identity-service, access-control-service, payroll-service, org-structure-service, notification-service, audit-service
Starts the employee lifecycle by propagating a newly hired employee record so identity creation, baseline permissions, payroll enrollment, and audit tracking run asynchronously.

EmployeeProfileChanged
employee-service
identity-service, payroll-service, org-structure-service, approval-service, reporting-service, audit-service
Publishes authoritative updates to employee attributes (title, manager, location, cost center) so all downstream systems remain consistent without tight coupling.

EmployeeOffboardingInitiated
employee-service
identity-service, access-control-service, payroll-service, asset-service, compliance-service, notification-service, audit-service
Launches cross-domain offboarding workflows to revoke access, stop compensation, recover assets, and preserve regulatory evidence.

OrgUnitCreated
org-structure-service
employee-service, budgeting-service, access-control-service, reporting-service
Broadcasts creation of a department/business unit so staffing, budget ownership, and authorization scopes can be aligned.

ManagerHierarchyUpdated
org-structure-service
approval-service, employee-service, notification-service, reporting-service
Distributes supervisory-chain changes that drive approval routing, escalation logic, and managerial analytics.

UserAccountProvisioned
identity-service
access-control-service, notification-service, audit-service
Signals successful account provisioning so roles can be granted, credentials communicated, and security trails recorded.

RoleAssignmentGranted
access-control-service
identity-service, compliance-service, audit-service
Propagates role grants for claim synchronization, policy checks, and immutable authorization auditing.

LeaveRequestSubmitted
leave-service
approval-service, workforce-planning-service, notification-service, audit-service
Initiates leave approval workflow and workforce-impact calculations when time off is requested.

LeaveRequestApproved
approval-service
leave-service, payroll-service, workforce-planning-service, notification-service
Completes approval stage and triggers leave balance updates, payroll treatment adjustments, and staffing plan recalculation.

LeaveRequestRejected
approval-service
leave-service, notification-service, audit-service
Terminates leave workflow with a rejection outcome while preserving decision traceability.

TimesheetSubmitted
time-tracking-service
approval-service, payroll-service, project-accounting-service, audit-service
Starts labor validation and pay preparation by publishing submitted worklogs.

TimesheetApproved
approval-service
time-tracking-service, payroll-service, project-accounting-service, reporting-service
Confirms approved time entries to finalize payroll inputs and recognize project labor costs.

PayrollRunCalculated
payroll-service
finance-service, reporting-service, notification-service, audit-service
Distributes payroll calculation outputs for accounting accruals, employee communication, and control verification.

PayrollPaymentCompleted
payroll-service
finance-service, reporting-service, notification-service, audit-service
Signals successful payroll disbursement to trigger reconciliation, posting, and statutory reporting workflows.

ExpenseClaimSubmitted
expense-service
approval-service, finance-service, notification-service, audit-service
Begins reimbursement workflow and budget validation when an employee submits an expense claim.

ExpenseClaimApproved
approval-service
expense-service, finance-service, payroll-service, notification-service
Authorizes reimbursement and routes payment settlement through AP or payroll.

ExpenseClaimPaid
finance-service
expense-service, notification-service, reporting-service, audit-service
Confirms reimbursement completion so employee visibility, ledger posting, and close reporting can proceed.

TrainingEnrollmentAssigned
learning-service
employee-service, notification-service, compliance-service
Publishes assigned learning requirements to drive employee development and mandatory policy training completion.

TrainingCourseCompleted
learning-service
employee-service, compliance-service, reporting-service, notification-service
Records completed training to update skills profiles, compliance status, and learning analytics.

PerformanceReviewFinalized
performance-service
employee-service, compensation-service, succession-service, reporting-service, notification-service
Broadcasts finalized review outcomes to feed merit planning, talent decisions, and organizational performance insights.
