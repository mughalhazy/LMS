export type SupportedContentType =
  | "video"
  | "audio"
  | "document"
  | "scorm_package"
  | "assessment_asset"
  | "interactive_module"
  | "image";

export interface ContentMetadataRecord {
  contentId: string;
  tenantId: string;
  contentType: SupportedContentType;
  title?: string;
  description?: string;
  language?: string;
  durationSeconds?: number;
  licensing?: string;
  accessibility?: {
    captionsAvailable?: boolean;
    transcriptAvailable?: boolean;
    screenReaderOptimized?: boolean;
  };
  tags: string[];
  createdAtIso: string;
  updatedAtIso: string;
  updatedBy: string;
  version: number;
}

export interface MetadataCreateRequest {
  contentId: string;
  tenantId: string;
  contentType: SupportedContentType;
  actorUserId: string;
  title?: string;
  description?: string;
  language?: string;
  durationSeconds?: number;
  licensing?: string;
  accessibility?: ContentMetadataRecord["accessibility"];
  tags?: string[];
}

export interface MetadataUpdateRequest {
  contentId: string;
  tenantId: string;
  actorUserId: string;
  title?: string;
  description?: string;
  language?: string;
  durationSeconds?: number;
  licensing?: string;
  accessibility?: ContentMetadataRecord["accessibility"];
  tags?: string[];
}

export interface MetadataQuery {
  tenantId: string;
  language?: string;
  tagsAny?: string[];
  text?: string;
}

export interface MetadataSearchResult {
  items: ContentMetadataRecord[];
  total: number;
}

export interface SearchIndexHook {
  onMetadataUpserted(record: ContentMetadataRecord): Promise<void>;
  onMetadataDeleted(params: { tenantId: string; contentId: string }): Promise<void>;
}

export interface SearchIndexEvent {
  type: "upsert" | "delete";
  tenantId: string;
  contentId: string;
  occurredAtIso: string;
}

export interface MetadataRepository {
  getByContentId(tenantId: string, contentId: string): Promise<ContentMetadataRecord | undefined>;
  upsert(record: ContentMetadataRecord): Promise<ContentMetadataRecord>;
  delete(tenantId: string, contentId: string): Promise<boolean>;
  search(query: MetadataQuery): Promise<MetadataSearchResult>;
}
