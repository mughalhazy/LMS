import { EnrollmentController } from './controller';
import { InMemoryEnrollmentRepository } from './repository';
import { EnrollmentService } from './service';

export * from './types';
export * from './repository';
export * from './service';
export * from './controller';

export const createEnrollmentModule = (): EnrollmentController => {
  const repository = new InMemoryEnrollmentRepository();
  const service = new EnrollmentService(repository);
  return new EnrollmentController(service);
};
