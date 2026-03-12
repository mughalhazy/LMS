import { EnrollmentService } from './service';

export interface HttpRequest {
  params: Record<string, string | undefined>;
  query: Record<string, string | undefined>;
  body: Record<string, unknown>;
  headers: Record<string, string | undefined>;
}

export interface HttpResponse {
  status(code: number): HttpResponse;
  json(payload: unknown): void;
}

/**
 * HTTP handler layer for enrollment APIs.
 * Assumes tenant context is provided via `x-tenant-id` header.
 */
export class EnrollmentController {
  constructor(private readonly enrollmentService: EnrollmentService) {}

  enrollUser = (req: HttpRequest, res: HttpResponse): void => {
    const tenantId = this.requireTenant(req);
    const enrollment = this.enrollmentService.enrollUser({
      tenantId,
      userId: String(req.body.userId),
      courseId: String(req.body.courseId),
      status: req.body.status as never,
    });

    res.status(201).json(enrollment);
  };

  unenrollUser = (req: HttpRequest, res: HttpResponse): void => {
    const tenantId = this.requireTenant(req);
    const enrollmentId = String(req.params.enrollmentId);
    const enrollment = this.enrollmentService.unenrollUser({ tenantId, enrollmentId });

    res.status(200).json(enrollment);
  };

  getEnrollment = (req: HttpRequest, res: HttpResponse): void => {
    const tenantId = this.requireTenant(req);
    const enrollmentId = String(req.params.enrollmentId);
    const enrollment = this.enrollmentService.getEnrollment(tenantId, enrollmentId);

    res.status(200).json(enrollment);
  };

  listEnrollments = (req: HttpRequest, res: HttpResponse): void => {
    const tenantId = this.requireTenant(req);
    const enrollments = this.enrollmentService.listEnrollments({
      tenantId,
      userId: req.query.userId,
      courseId: req.query.courseId,
      status: req.query.status as never,
    });

    res.status(200).json({ data: enrollments, count: enrollments.length });
  };

  updateEnrollmentStatus = (req: HttpRequest, res: HttpResponse): void => {
    const tenantId = this.requireTenant(req);
    const enrollmentId = String(req.params.enrollmentId);

    const enrollment = this.enrollmentService.updateEnrollmentStatus({
      tenantId,
      enrollmentId,
      status: String(req.body.status) as never,
    });

    res.status(200).json(enrollment);
  };

  private requireTenant(req: HttpRequest): string {
    const tenantId = req.headers['x-tenant-id'];
    if (!tenantId) {
      throw new Error('Missing x-tenant-id header');
    }

    return tenantId;
  }
}
