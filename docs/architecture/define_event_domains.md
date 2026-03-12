event_name
producer_service
consumer_services
event_purpose

EmployeeCreated
employee-service
identity-service, payroll-service, org-structure-service, notification-service, audit-service
Propagates a new employee profile so downstream services can create linked records and enforce traceability.

EmployeeUpdated
employee-service
identity-service, payroll-service, org-structure-service, compliance-service, audit-service
Synchronizes authoritative employee attribute changes (role, department, manager, location) across dependent domains.

EmployeeTerminated
employee-service
identity-service, payroll-service, access-control-service, asset-service, notification-service, audit-service
Triggers offboarding workflows to revoke access, stop compensation, collect assets, and maintain compliance evidence.

DepartmentCreated
org-structure-service
employee-service, budgeting-service, reporting-service, access-control-service
Broadcasts a new organizational unit for staffing, budget allocation, and authorization scoping.

DepartmentManagerChanged
org-structure-service
employee-service, approval-service, reporting-service, notification-service
Updates managerial hierarchies used for approvals, escalation chains, and org analytics.

UserProvisioned
identity-service
access-control-service, notification-service, audit-service
Signals successful account creation so permissions, onboarding notices, and identity audit logs can be completed.

AccessRoleAssigned
access-control-service
identity-service, audit-service, compliance-service
Distributes role-assignment decisions to keep identity claims, audits, and policy attestations consistent.

LeaveRequested
leave-service
approval-service, workforce-planning-service, notification-service, audit-service
Starts leave approval and staffing impact workflows when an employee submits time-off.

LeaveApproved
approval-service
leave-service, payroll-service, workforce-planning-service, notification-service
Confirms approved leave so balances, payroll calculations, and staffing plans are updated.

LeaveRejected
approval-service
leave-service, notification-service, audit-service
Closes leave workflows with a rejection outcome and preserves decision traceability.

WorklogSubmitted
time-tracking-service
approval-service, payroll-service, project-accounting-service, audit-service
Publishes submitted timesheets for manager review, labor costing, and payroll preparation.

WorklogApproved
approval-service
time-tracking-service, payroll-service, project-accounting-service
Finalizes approved time entries for compensation and cost recognition.

PayrollCalculated
payroll-service
finance-service, reporting-service, notification-service, audit-service
Shares calculated payroll run results for accounting, employee communications, and control verification.

PayrollDisbursed
payroll-service
finance-service, reporting-service, notification-service, audit-service
Indicates successful payout execution and enables reconciliation and statutory reporting.

ExpenseSubmitted
expense-service
approval-service, finance-service, notification-service, audit-service
Initiates reimbursement workflow and accounting pre-validation for employee expenses.

ExpenseApproved
approval-service
expense-service, finance-service, payroll-service, notification-service
Authorizes reimbursements and routes payable amounts to finance or payroll settlement paths.

ExpenseReimbursed
finance-service
expense-service, notification-service, reporting-service, audit-service
Confirms reimbursement completion for employee visibility and financial close processes.

TrainingAssigned
learning-service
employee-service, notification-service, compliance-service
Announces mandatory or optional learning assignments tied to employee development and policy obligations.

TrainingCompleted
learning-service
employee-service, compliance-service, reporting-service, notification-service
Records completed training to update skills profiles and satisfy compliance requirements.

PerformanceReviewCompleted
performance-service
employee-service, compensation-service, reporting-service, notification-service
Publishes finalized review outcomes for career development, merit planning, and workforce analytics.
