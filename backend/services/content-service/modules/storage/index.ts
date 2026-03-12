import { defaultStorageConfig, StorageModuleConfig } from "./config";
import { SimpleCdnSigner } from "./cdn-access.service";
import { InMemoryObjectStorageClient } from "./object-storage.client";
import { SecureAccessService } from "./secure-access.service";
import { UploadPipelineService } from "./upload-pipeline.service";

export * from "./types";
export * from "./config";
export { UploadPipelineService } from "./upload-pipeline.service";
export { SecureAccessService } from "./secure-access.service";
export { InMemoryObjectStorageClient } from "./object-storage.client";
export { SimpleCdnSigner } from "./cdn-access.service";

export function createStorageModule(config: StorageModuleConfig = defaultStorageConfig): UploadPipelineService {
  const objectStorageClient = new InMemoryObjectStorageClient();
  const secureAccessService = new SecureAccessService(config);
  const cdnSigner = config.cdn.enabled ? new SimpleCdnSigner(config.cdn.baseUrl) : undefined;

  return new UploadPipelineService(config, objectStorageClient, secureAccessService, cdnSigner);
}
