service_name: student-service
owned_entities: Student, StudentProfile, StudentContact, StudentEnrollment
database_tables: students, student_profiles, student_contacts, student_enrollments

service_name: teacher-service
owned_entities: Teacher, TeacherProfile, TeacherQualification, TeacherAssignment
database_tables: teachers, teacher_profiles, teacher_qualifications, teacher_assignments

service_name: course-service
owned_entities: Course, CourseSection, CourseSchedule, CourseMaterial
database_tables: courses, course_sections, course_schedules, course_materials

service_name: attendance-service
owned_entities: AttendanceRecord, AttendanceSession, AttendancePolicy
database_tables: attendance_records, attendance_sessions, attendance_policies

service_name: assessment-service
owned_entities: Exam, AssessmentItem, Grade, GradeScale
database_tables: exams, assessment_items, grades, grade_scales

service_name: finance-service
owned_entities: FeeStructure, Invoice, Payment, Scholarship
database_tables: fee_structures, invoices, payments, scholarships

service_name: guardian-service
owned_entities: Guardian, StudentGuardianLink, EmergencyContact
database_tables: guardians, student_guardian_links, emergency_contacts

service_name: notification-service
owned_entities: Notification, NotificationTemplate, NotificationDelivery
database_tables: notifications, notification_templates, notification_deliveries

service_name: auth-service
owned_entities: UserAccount, Role, Permission, SessionToken
database_tables: user_accounts, roles, permissions, session_tokens
