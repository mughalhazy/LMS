import express from "express";
import { PrerequisiteEngineService } from "./application/prerequisite-engine.js";
import { createRoutes } from "./api/routes.js";
import {
  InMemoryLearningPathRepository,
  InMemoryPrerequisiteRepository,
  InMemoryTenantPolicyRepository,
  InMemoryTranscriptRepository
} from "./infrastructure/in-memory-repositories.js";

const prerequisiteRepo = new InMemoryPrerequisiteRepository();
const transcriptRepo = new InMemoryTranscriptRepository();
const learningPathRepo = new InMemoryLearningPathRepository();
const tenantPolicyRepo = new InMemoryTenantPolicyRepository();

transcriptRepo.seed([
  {
    tenantId: "tenant-a",
    userId: "learner-1",
    courseId: "course-intro",
    completionState: "COMPLETED",
    grade: 91,
    completedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
  }
]);

const engine = new PrerequisiteEngineService(
  prerequisiteRepo,
  transcriptRepo,
  learningPathRepo,
  tenantPolicyRepo
);

const app = express();
app.use(express.json());
app.use("/api/v1/prerequisite-engine", createRoutes(engine));

app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  const message = err instanceof Error ? err.message : "Unexpected error";
  res.status(400).json({ error: message });
});

const port = Number(process.env.PORT ?? 8084);
app.listen(port, () => {
  console.log(`Prerequisite Engine Service listening on port ${port}`);
});
