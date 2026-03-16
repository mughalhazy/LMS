# Migration notes

1. Deploy program-service schema to a **dedicated** program-service database/schema.
2. Do not add FKs to `course-service` tables; `course_id` remains an external reference validated via API/read-model.
3. Backfill is optional because programs are net-new entities; no course data rewrite is required.
4. Configure event-bus topics for program lifecycle events before enabling writes.
5. Validate tenant isolation by enforcing `tenant_id` in API context (`X-Tenant-Id`) and persisted records.
