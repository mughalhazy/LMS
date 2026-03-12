import { Router, Request, Response } from "express";
import { CourseVersioningService } from "./service";

export function createCourseVersioningRouter(service: CourseVersioningService): Router {
  const router = Router();

  router.post("/courses/:courseId/versions", async (req: Request, res: Response) => {
    try {
      const version = await service.createVersion({
        tenantId: req.body.tenantId,
        courseId: req.params.courseId,
        sourceVersion: req.body.sourceVersion,
        changeSummary: req.body.changeSummary,
        editorId: req.body.editorId,
        contentPayload: req.body.contentPayload,
        metadataUpdates: req.body.metadataUpdates,
      });

      res.status(201).json(version);
    } catch (error) {
      res.status(400).json({ message: (error as Error).message });
    }
  });

  router.get("/courses/:courseId/versions", async (req: Request, res: Response) => {
    try {
      const history = await service.getVersionHistory({
        tenantId: req.query.tenantId as string,
        courseId: req.params.courseId,
        limit: req.query.limit ? Number(req.query.limit) : undefined,
        offset: req.query.offset ? Number(req.query.offset) : undefined,
      });

      res.status(200).json(history);
    } catch (error) {
      res.status(400).json({ message: (error as Error).message });
    }
  });

  router.post("/courses/:courseId/versions/:versionNumber/rollback", async (req: Request, res: Response) => {
    try {
      const rollbackVersion = await service.rollbackVersion({
        tenantId: req.body.tenantId,
        courseId: req.params.courseId,
        targetVersionNumber: Number(req.params.versionNumber),
        rollbackReason: req.body.rollbackReason,
        requestedBy: req.body.requestedBy,
      });

      res.status(201).json(rollbackVersion);
    } catch (error) {
      res.status(400).json({ message: (error as Error).message });
    }
  });

  router.post("/courses/:courseId/versions/:versionNumber/publish", async (req: Request, res: Response) => {
    try {
      const published = await service.publishVersion({
        tenantId: req.body.tenantId,
        courseId: req.params.courseId,
        versionNumber: Number(req.params.versionNumber),
        publisherId: req.body.publisherId,
        releaseNotes: req.body.releaseNotes,
      });

      res.status(200).json(published);
    } catch (error) {
      res.status(400).json({ message: (error as Error).message });
    }
  });

  return router;
}
