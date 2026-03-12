import { Router } from "express";
import { z } from "zod";
import { PrerequisiteEngineService } from "../application/prerequisite-engine.js";

const id = z.string().min(1);

export const createRoutes = (engine: PrerequisiteEngineService): Router => {
  const router = Router();

  router.post("/tenant-policies", (req, res) => {
    const schema = z.object({
      tenantId: id,
      allowAdvisoryBypass: z.boolean(),
      acceptedCompletionStates: z.array(z.enum(["COMPLETED", "IN_PROGRESS", "NOT_STARTED"]))
    });

    const body = schema.parse(req.body);
    const policy = engine.upsertTenantPolicy(body);
    res.status(201).json(policy);
  });

  router.post("/prerequisite-rules", (req, res) => {
    const schema = z.object({
      id,
      tenantId: id,
      courseId: id,
      mode: z.enum(["ALL", "ANY"]),
      prerequisiteNodes: z.array(
        z.object({
          id,
          requiredCourseId: id,
          minimumGrade: z.number().min(0).max(100).optional(),
          validityWindowDays: z.number().positive().optional()
        })
      ),
      equivalencyCourseIds: z.record(z.array(id)).optional(),
      createdBy: id,
      createdAt: z.string().datetime()
    });

    const rule = engine.definePrerequisiteRule(schema.parse(req.body));
    res.status(201).json(rule);
  });

  router.post("/eligibility/check", (req, res) => {
    const body = z
      .object({
        tenantId: id,
        userId: id,
        courseId: id
      })
      .parse(req.body);

    const decision = engine.checkCourseEligibility(body);
    res.status(200).json(decision);
  });

  router.post("/learning-paths/validate", (req, res) => {
    const schema = z.object({
      id,
      tenantId: id,
      pathId: id,
      policyVersion: z.string().min(1),
      dependencies: z.array(
        z.object({
          id,
          fromNodeId: id,
          toNodeId: id,
          strict: z.boolean(),
          type: z.enum(["SEQUENTIAL_UNLOCK", "MILESTONE_GATE", "CO_REQUISITE", "SCORE_THRESHOLD"]),
          minimumScore: z.number().min(0).max(100).optional()
        })
      )
    });

    const validation = engine.validateLearningPathDependencies(schema.parse(req.body));
    res.status(validation.valid ? 200 : 422).json(validation);
  });

  return router;
};
