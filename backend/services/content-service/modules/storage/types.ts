export type ContentType =
  | "video"
  | "audio"
  | "document"
  | "scorm_package"
  | "assessment_asset"
  | "interactive_module"
  | "image";

export type AccessTier = "private" | "internal" | "public";

export interface ContentMetadata {
  assetId: string;
  tenantId: string;
  title?: string;
  description?: string;
  language?: string;
  tags?: string[];
  uploadedBy: string;
  uploadedAt: string;
  publishedAt?: string;
  version: number;
  checksumSha256?: string;
  retentionPolicy?: string;
  accessTier: AccessTier;
  customFields?: Record<string, string | number | boolean | null>;
}

export interface UploadIntentRequest {
  tenantId: string;
  contentType: ContentType;
  fileName: string;
  contentLength: number;
  contentTypeHeader: string;
  uploadedBy: string;
  metadata?: Partial<ContentMetadata>;
}

export interface UploadIntent {
  assetId: string;
  objectKey: string;
  storageUri: string;
  uploadUrl: string;
  uploadHeaders: Record<string, string>;
  expiresAtIso: string;
}

export interface CompleteUploadRequest {
  tenantId: string;
  contentType: ContentType;
  assetId: string;
  objectKey: string;
  uploadedBy: string;
  metadata?: Partial<ContentMetadata>;
}

export interface CompleteUploadResult {
  assetId: string;
  objectKey: string;
  storageUri: string;
  metadata: ContentMetadata;
  virusScanStatus: "pending" | "clean" | "infected";
}

export interface AccessRequest {
  tenantId: string;
  requesterId: string;
  roles: string[];
  contentType: ContentType;
  assetId: string;
  objectKey: string;
  requiresDownload?: boolean;
}

export interface AccessGrant {
  deliveryUrl: string;
  expiresAtIso: string;
  tokenType: "cdn_signed_url" | "object_signed_get" | "proxy_token";
}

export interface StoredObject {
  bucket: string;
  key: string;
  sizeBytes: number;
  checksumSha256?: string;
  etag?: string;
  uploadedAtIso: string;
}

export interface SignedUrl {
  url: string;
  expiresAtIso: string;
  headers?: Record<string, string>;
}

export interface StorageProvider {
  createSignedPutUrl(params: {
    bucket: string;
    key: string;
    contentType: string;
    contentLength: number;
    expiresInSeconds: number;
    checksumSha256?: string;
  }): Promise<SignedUrl>;
  createSignedGetUrl(params: {
    bucket: string;
    key: string;
    expiresInSeconds: number;
    responseContentDisposition?: string;
  }): Promise<SignedUrl>;
  headObject(params: { bucket: string; key: string }): Promise<StoredObject>;
}

export interface CdnSigner {
  createSignedDeliveryUrl(params: {
    path: string;
    expiresInSeconds: number;
    tokenClaims: Record<string, string>;
  }): Promise<SignedUrl>;
}
