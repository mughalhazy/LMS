import { defaultMetadataModuleConfig, MetadataModuleConfig } from "./config";
import { TaggingService } from "./tagging.service";
import {
  ContentMetadataRecord,
  MetadataCreateRequest,
  MetadataQuery,
  MetadataRepository,
  MetadataSearchResult,
  MetadataUpdateRequest,
  SearchIndexHook,
} from "./types";

function nowIso(): string {
  return new Date().toISOString();
}

export class MetadataService {
  private readonly taggingService: TaggingService;

  constructor(
    private readonly repository: MetadataRepository,
    private readonly searchIndexHook: SearchIndexHook,
    config: MetadataModuleConfig = defaultMetadataModuleConfig,
  ) {
    this.taggingService = new TaggingService(config);
  }

  async createMetadata(request: MetadataCreateRequest): Promise<ContentMetadataRecord> {
    const existing = await this.repository.getByContentId(request.tenantId, request.contentId);
    if (existing) {
      throw new Error(`Metadata already exists for contentId=${request.contentId}`);
    }

    const timestamp = nowIso();
    const record: ContentMetadataRecord = {
      contentId: request.contentId,
      tenantId: request.tenantId,
      contentType: request.contentType,
      title: request.title,
      description: request.description,
      language: request.language,
      durationSeconds: request.durationSeconds,
      licensing: request.licensing,
      accessibility: request.accessibility,
      tags: this.taggingService.normalizeTags(request.tags),
      createdAtIso: timestamp,
      updatedAtIso: timestamp,
      updatedBy: request.actorUserId,
      version: 1,
    };

    const stored = await this.repository.upsert(record);
    await this.searchIndexHook.onMetadataUpserted(stored);
    return stored;
  }

  async updateMetadata(request: MetadataUpdateRequest): Promise<ContentMetadataRecord> {
    const existing = await this.repository.getByContentId(request.tenantId, request.contentId);
    if (!existing) {
      throw new Error(`Metadata not found for contentId=${request.contentId}`);
    }

    const updated: ContentMetadataRecord = {
      ...existing,
      title: request.title ?? existing.title,
      description: request.description ?? existing.description,
      language: request.language ?? existing.language,
      durationSeconds: request.durationSeconds ?? existing.durationSeconds,
      licensing: request.licensing ?? existing.licensing,
      accessibility: request.accessibility ?? existing.accessibility,
      tags: request.tags ? this.taggingService.normalizeTags(request.tags) : existing.tags,
      updatedAtIso: nowIso(),
      updatedBy: request.actorUserId,
      version: existing.version + 1,
    };

    const stored = await this.repository.upsert(updated);
    await this.searchIndexHook.onMetadataUpserted(stored);
    return stored;
  }

  async addTags(params: {
    tenantId: string;
    contentId: string;
    actorUserId: string;
    tags: string[];
  }): Promise<ContentMetadataRecord> {
    const existing = await this.repository.getByContentId(params.tenantId, params.contentId);
    if (!existing) {
      throw new Error(`Metadata not found for contentId=${params.contentId}`);
    }

    const nextTags = this.taggingService.addTags(existing.tags, params.tags);
    return this.updateMetadata({
      tenantId: params.tenantId,
      contentId: params.contentId,
      actorUserId: params.actorUserId,
      tags: nextTags,
    });
  }

  async removeTags(params: {
    tenantId: string;
    contentId: string;
    actorUserId: string;
    tags: string[];
  }): Promise<ContentMetadataRecord> {
    const existing = await this.repository.getByContentId(params.tenantId, params.contentId);
    if (!existing) {
      throw new Error(`Metadata not found for contentId=${params.contentId}`);
    }

    const nextTags = this.taggingService.removeTags(existing.tags, params.tags);
    return this.updateMetadata({
      tenantId: params.tenantId,
      contentId: params.contentId,
      actorUserId: params.actorUserId,
      tags: nextTags,
    });
  }

  async search(query: MetadataQuery): Promise<MetadataSearchResult> {
    return this.repository.search(query);
  }

  async deleteMetadata(tenantId: string, contentId: string): Promise<boolean> {
    const deleted = await this.repository.delete(tenantId, contentId);
    if (deleted) {
      await this.searchIndexHook.onMetadataDeleted({ tenantId, contentId });
    }
    return deleted;
  }
}
