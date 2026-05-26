# LMS Data Ownership Rules

**Type:** Architecture Reference | **Last reviewed:** 2026-05-26

> **Canonical doc for data ownership:** `docs/architecture/ARCH_04_data_ownership_matrix.md` — this file is a historical ownership reference. ARCH_04 is authoritative.

Service-to-entity ownership map. Each service owns the listed entities and their backing tables exclusively.

---

| service_name | owned_entities | database_tables |
|---|---|---|
| student-service | Student, StudentProfile, StudentContact, StudentEnrollment | students, student_profiles, student_contacts, student_enrollments |
| teacher-service | Teacher, TeacherProfile, TeacherQualification, TeacherAssignment | teachers, teacher_profiles, teacher_qualifications, teacher_assignments |
| course-service | Course, CourseSection, CourseSchedule, CourseMaterial | courses, course_sections, course_schedules, course_materials |
| attendance-service | AttendanceRecord, AttendanceSession, AttendancePolicy | attendance_records, attendance_sessions, attendance_policies |
| assessment-service | Exam, AssessmentItem, Grade, GradeScale | exams, assessment_items, grades, grade_scales |
| finance-service | FeeStructure, Invoice, Payment, Scholarship | fee_structures, invoices, payments, scholarships |
| guardian-service | Guardian, StudentGuardianLink, EmergencyContact | guardians, student_guardian_links, emergency_contacts |
| notification-service | Notification, NotificationTemplate, NotificationDelivery | notifications, notification_templates, notification_deliveries |
| auth-service | UserAccount, Role, Permission, SessionToken | user_accounts, roles, permissions, session_tokens |
