scaling_component | strategy | notes
--- | --- | ---
horizontal scaling | Run multiple service instances behind load balancers across compute nodes. | Scale out independently per service tier (API, workers, gateway) to remove single-node bottlenecks.
stateless services | Keep application instances stateless; persist session/workflow state in shared external stores (DB, cache, object storage). | Enables safe instance replacement and fast horizontal expansion without sticky sessions.
autoscaling | Use metric-driven autoscaling (CPU, memory, request rate, queue depth, latency SLO) for each service group. | Configure min/max capacity, cooldown windows, and separate policies for real-time APIs vs asynchronous workers.
multi-region deployment | Deploy active-active across multiple regions with global traffic routing and replicated data services. | Improve latency and resilience; define failover rules, data consistency model, and regional isolation boundaries.
