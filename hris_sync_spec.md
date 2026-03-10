sync_operation | source_fields | destination_fields
--- | --- | ---
employee sync | `employee_id`, `first_name`, `last_name`, `work_email`, `employment_status`, `job_title`, `manager_employee_id`, `department_code`, `role_code`, `hire_date`, `termination_date` | `users.external_hris_id`, `users.first_name`, `users.last_name`, `users.email`, `users.status`, `users.title`, `users.manager_user_id`, `users.department_id`, `user_roles.role_id`, `users.hire_date`, `users.deactivated_at`
department mapping | `department_code`, `department_name`, `parent_department_code`, `cost_center`, `active_flag` | `departments.external_hris_code`, `departments.name`, `departments.parent_department_id`, `departments.cost_center`, `departments.is_active`
role mapping | `role_code`, `role_name`, `role_type`, `permission_bundle`, `active_flag` | `roles.external_hris_code`, `roles.name`, `roles.category`, `roles.permission_set`, `roles.is_active`
