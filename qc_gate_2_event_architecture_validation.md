event_name
producer_service
issue_description
severity
recommended_fix

EmployeeOnboarded
employee-service
No issue found: exactly one producer, consumers align with employee lifecycle onboarding domain, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

EmployeeProfileChanged
employee-service
No issue found: exactly one producer, consumers align with employee master-data propagation domain, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

EmployeeOffboardingInitiated
employee-service
No issue found: exactly one producer, consumers align with offboarding/security/payroll domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

OrgUnitCreated
org-structure-service
No issue found: exactly one producer, consumers align with org-structure and downstream staffing/access/reporting domain usage, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

ManagerHierarchyUpdated
org-structure-service
No issue found: exactly one producer, consumers align with approval/escalation/organizational reporting domain needs, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

UserAccountProvisioned
identity-service
No issue found: exactly one producer, consumers align with identity and access enablement domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

RoleAssignmentGranted
access-control-service
No issue found: exactly one producer, consumers align with authorization/compliance/audit domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

LeaveRequestSubmitted
leave-service
No issue found: exactly one producer, consumers align with leave approval and workforce planning domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

LeaveRequestApproved
approval-service
No issue found: exactly one producer, consumers align with approval outcome propagation to leave/payroll/workforce domains, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

LeaveRequestRejected
approval-service
No issue found: exactly one producer, consumers align with approval outcome + notification/audit domain needs, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

TimesheetSubmitted
time-tracking-service
No issue found: exactly one producer, consumers align with approval/payroll/project accounting domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

TimesheetApproved
approval-service
No issue found: exactly one producer, consumers align with approved labor posting to payroll/accounting/reporting domains, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

PayrollRunCalculated
payroll-service
No issue found: exactly one producer, consumers align with payroll-to-finance/reporting/notification/audit domain handoff, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

PayrollPaymentCompleted
payroll-service
No issue found: exactly one producer, consumers align with payment completion and reconciliation/reporting domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

ExpenseClaimSubmitted
expense-service
No issue found: exactly one producer, consumers align with expense approval/finance processing domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

ExpenseClaimApproved
approval-service
No issue found: exactly one producer, consumers align with approval outcome propagation to expense/finance/payroll domains, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

ExpenseClaimPaid
finance-service
No issue found: exactly one producer, consumers align with reimbursement completion and reporting/audit domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

TrainingEnrollmentAssigned
learning-service
No issue found: exactly one producer, consumers align with learning assignment and compliance/notification domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

TrainingCourseCompleted
learning-service
No issue found: exactly one producer, consumers align with learning completion/compliance/reporting domain workflows, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.

PerformanceReviewFinalized
performance-service
No issue found: exactly one producer, consumers align with performance-to-compensation/succession/reporting domains, naming matches PascalCase + past-tense convention, and event is unique.
none
No change required.
