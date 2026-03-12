import { AssignmentFilters, LearningPathAssignment } from "./entities";

export interface LearningPathAssignmentRepository {
  create(assignment: LearningPathAssignment): Promise<LearningPathAssignment>;
  findById(
    tenantId: string,
    assignmentId: string,
  ): Promise<LearningPathAssignment | null>;
  findMany(filters: AssignmentFilters): Promise<LearningPathAssignment[]>;
  update(assignment: LearningPathAssignment): Promise<LearningPathAssignment>;
}

export class InMemoryLearningPathAssignmentRepository
  implements LearningPathAssignmentRepository
{
  private readonly assignments: LearningPathAssignment[] = [];

  async create(
    assignment: LearningPathAssignment,
  ): Promise<LearningPathAssignment> {
    this.assignments.push(assignment);
    return assignment;
  }

  async findById(
    tenantId: string,
    assignmentId: string,
  ): Promise<LearningPathAssignment | null> {
    return (
      this.assignments.find(
        (item) => item.tenantId === tenantId && item.assignmentId === assignmentId,
      ) ?? null
    );
  }

  async findMany(filters: AssignmentFilters): Promise<LearningPathAssignment[]> {
    return this.assignments.filter((item) => {
      if (item.tenantId !== filters.tenantId) {
        return false;
      }
      if (filters.pathId && item.pathId !== filters.pathId) {
        return false;
      }
      if (filters.targetType && item.targetType !== filters.targetType) {
        return false;
      }
      if (filters.targetId && item.targetId !== filters.targetId) {
        return false;
      }
      if (filters.status && item.status !== filters.status) {
        return false;
      }

      return true;
    });
  }

  async update(
    assignment: LearningPathAssignment,
  ): Promise<LearningPathAssignment> {
    const index = this.assignments.findIndex(
      (item) =>
        item.tenantId === assignment.tenantId &&
        item.assignmentId === assignment.assignmentId,
    );

    if (index < 0) {
      throw new Error("assignment_not_found");
    }

    this.assignments[index] = assignment;
    return assignment;
  }
}
