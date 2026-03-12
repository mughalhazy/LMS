import { AssignLearningPathRequest } from "./entities";
import { LearningPathAssignmentService } from "./service";

interface HttpRequest<TBody = unknown, TParams = Record<string, string>> {
  tenantId: string;
  params: TParams;
  body: TBody;
  actorId: string;
}

interface HttpResponse {
  status: number;
  body: unknown;
}

export class LearningPathAssignmentApi {
  constructor(private readonly service: LearningPathAssignmentService) {}

  async assign(
    request: HttpRequest<AssignLearningPathRequest>,
  ): Promise<HttpResponse> {
    const assignment = await this.service.assign({
      ...request.body,
      tenantId: request.tenantId,
      createdBy: request.actorId,
    });

    return {
      status: 201,
      body: assignment,
    };
  }

  async revoke(
    request: HttpRequest<undefined, { assignmentId: string }>,
  ): Promise<HttpResponse> {
    const assignment = await this.service.revoke(
      request.tenantId,
      request.params.assignmentId,
      request.actorId,
    );

    return {
      status: 200,
      body: assignment,
    };
  }

  async listAudience(
    request: HttpRequest<undefined, { pathId: string }>,
  ): Promise<HttpResponse> {
    const audience = await this.service.getAudienceSummary(
      request.tenantId,
      request.params.pathId,
    );

    return {
      status: 200,
      body: audience,
    };
  }
}

export const assignmentRoutes = {
  assignLearningPath: {
    method: "POST",
    path: "/tenants/{tenantId}/learning-paths/{pathId}/assignments",
    handler: "LearningPathAssignmentApi.assign",
  },
  revokeLearningPathAssignment: {
    method: "POST",
    path: "/tenants/{tenantId}/learning-paths/assignments/{assignmentId}/revoke",
    handler: "LearningPathAssignmentApi.revoke",
  },
  getLearningPathAudience: {
    method: "GET",
    path: "/tenants/{tenantId}/learning-paths/{pathId}/audience",
    handler: "LearningPathAssignmentApi.listAudience",
  },
} as const;
