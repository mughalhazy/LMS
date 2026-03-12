import { defaultMetadataModuleConfig, MetadataModuleConfig } from "./config";
import { MetadataRepository } from "./types";
import { InMemoryMetadataRepository } from "./metadata.repository";
import { MetadataService } from "./metadata.service";
import { InMemorySearchIndexHook } from "./search-index.hooks";

export * from "./types";
export * from "./config";
export { TaggingService } from "./tagging.service";
export { MetadataService } from "./metadata.service";
export { InMemoryMetadataRepository } from "./metadata.repository";
export { InMemorySearchIndexHook } from "./search-index.hooks";

export interface MetadataModule {
  service: MetadataService;
  repository: MetadataRepository;
  searchHook: InMemorySearchIndexHook;
}

export function createMetadataModule(config: MetadataModuleConfig = defaultMetadataModuleConfig): MetadataModule {
  const repository = new InMemoryMetadataRepository();
  const searchHook = new InMemorySearchIndexHook();
  const service = new MetadataService(repository, searchHook, config);

  return {
    service,
    repository,
    searchHook,
  };
}
