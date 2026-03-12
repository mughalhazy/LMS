import { ContentType } from "./types";

export interface StorageBucketConfig {
  bucket: string;
  keyPrefix: string;
  useCdn: boolean;
}

export interface CdnConfig {
  enabled: boolean;
  baseUrl: string;
  signingKeyId?: string;
}

export interface StorageModuleConfig {
  uploadUrlTtlSeconds: number;
  accessUrlTtlSeconds: number;
  enforceTenantPrefixIsolation: boolean;
  buckets: Record<ContentType, StorageBucketConfig>;
  cdn: CdnConfig;
}

export const defaultStorageConfig: StorageModuleConfig = {
  uploadUrlTtlSeconds: 900,
  accessUrlTtlSeconds: 600,
  enforceTenantPrefixIsolation: true,
  buckets: {
    video: { bucket: "lms-content-prod", keyPrefix: "videos", useCdn: true },
    audio: { bucket: "lms-content-prod", keyPrefix: "audio", useCdn: true },
    document: { bucket: "lms-content-prod", keyPrefix: "documents", useCdn: false },
    scorm_package: { bucket: "lms-content-prod", keyPrefix: "scorm", useCdn: false },
    assessment_asset: { bucket: "lms-content-prod", keyPrefix: "assessments", useCdn: false },
    interactive_module: { bucket: "lms-content-prod", keyPrefix: "interactive", useCdn: true },
    image: { bucket: "lms-content-prod", keyPrefix: "images", useCdn: true },
  },
  cdn: {
    enabled: true,
    baseUrl: "https://cdn.lms.example.com",
    signingKeyId: "kms-key-content-delivery",
  },
};
