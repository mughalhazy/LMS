component
technology
purpose

Compute - API & business services
Kubernetes (Amazon EKS) with autoscaling node groups
Runs LMS microservices (catalog, enrollment, assessments, progress, notifications) with horizontal scaling, rolling deployments, and fault isolation.

Compute - Edge/API ingress
Amazon API Gateway + AWS Application Load Balancer
Provides secure API entry points, request routing, throttling, and TLS termination for web/mobile/partner integrations.

Compute - Background jobs
AWS Lambda + Kubernetes CronJobs
Executes asynchronous and scheduled tasks such as reminders, certificate generation, nightly syncs, and compliance checks.

Databases - transactional learning data
Amazon Aurora PostgreSQL (Multi-AZ)
Stores strongly consistent relational data for users, enrollments, assessments, certifications, and audit-linked transactions.

Databases - high-throughput session/progress cache
Amazon DynamoDB
Handles large-scale key-value access patterns for learner session state, activity checkpoints, and low-latency progress lookups.

Databases - search index
Amazon OpenSearch Service
Supports full-text search and faceted filtering across course catalog, tags, skills, and content metadata.

Storage - learning content assets
Amazon S3 (versioned buckets)
Stores videos, SCORM/xAPI packages, documents, and certificate artifacts with lifecycle management and durability.

Storage - shared file system
Amazon EFS
Provides POSIX shared storage for services needing common runtime files, import/export staging, and temporary processing artifacts.

CDN
Amazon CloudFront
Caches static web assets and learning media globally, reducing latency and offloading origin traffic while enforcing signed URL access for protected content.

Queue system - event bus
Amazon EventBridge
Distributes domain events (EnrollmentCreated, TrainingCompleted, CertificationIssued) between decoupled LMS and EMS services.

Queue system - reliable async processing
Amazon SQS (standard + dead-letter queues)
Buffers background work (email, report generation, webhook delivery) with retry and failure isolation.

Queue system - stream processing
Amazon MSK (Apache Kafka)
Processes high-volume learning telemetry/event streams for near-real-time analytics and compliance monitoring pipelines.
