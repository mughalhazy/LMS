import { StorageModuleConfig } from "./config";
import { SecureAccessService } from "./secure-access.service";
import {
  AccessGrant,
  AccessRequest,
  CompleteUploadRequest,
  CompleteUploadResult,
  ContentMetadata,
  StorageProvider,
  UploadIntent,
  UploadIntentRequest,
  CdnSigner,
} from "./types";

export class UploadPipelineService {
  private readonly metadataStore = new Map<string, ContentMetadata>();

  constructor(
    private readonly config: StorageModuleConfig,
    private readonly objectStorage: StorageProvider,
    private readonly accessControl: SecureAccessService,
    private readonly cdnSigner?: CdnSigner,
  ) {}

  async createUploadIntent(request: UploadIntentRequest): Promise<UploadIntent> {
    this.validateUploadRequest(request);

    const bucketConfig = this.config.buckets[request.contentType];
    const assetId = this.generateAssetId(request.tenantId, request.contentType);
    const objectKey = this.buildObjectKey({
      tenantId: request.tenantId,
      contentTypePrefix: bucketConfig.keyPrefix,
      assetId,
      fileName: request.fileName,
    });

    const signedPut = await this.objectStorage.createSignedPutUrl({
      bucket: bucketConfig.bucket,
      key: objectKey,
      contentType: request.contentTypeHeader,
      contentLength: request.contentLength,
      expiresInSeconds: this.config.uploadUrlTtlSeconds,
      checksumSha256: request.metadata?.checksumSha256,
    });

    return {
      assetId,
      objectKey,
      storageUri: `s3://${bucketConfig.bucket}/${objectKey}`,
      uploadUrl: signedPut.url,
      uploadHeaders: signedPut.headers ?? {},
      expiresAtIso: signedPut.expiresAtIso,
    };
  }

  async completeUpload(request: CompleteUploadRequest): Promise<CompleteUploadResult> {
    const bucketConfig = this.config.buckets[request.contentType];
    const object = await this.objectStorage.headObject({
      bucket: bucketConfig.bucket,
      key: request.objectKey,
    });

    const metadata: ContentMetadata = {
      assetId: request.assetId,
      tenantId: request.tenantId,
      title: request.metadata?.title,
      description: request.metadata?.description,
      language: request.metadata?.language,
      tags: request.metadata?.tags,
      uploadedBy: request.uploadedBy,
      uploadedAt: object.uploadedAtIso,
      publishedAt: request.metadata?.publishedAt,
      version: request.metadata?.version ?? 1,
      checksumSha256: object.checksumSha256,
      retentionPolicy: request.metadata?.retentionPolicy,
      accessTier: request.metadata?.accessTier ?? "private",
      customFields: request.metadata?.customFields,
    };

    this.metadataStore.set(request.assetId, metadata);

    return {
      assetId: request.assetId,
      objectKey: request.objectKey,
      storageUri: `s3://${bucketConfig.bucket}/${request.objectKey}`,
      metadata,
      virusScanStatus: "pending",
    };
  }

  async getSecureContentAccess(request: AccessRequest): Promise<AccessGrant> {
    this.accessControl.authorize(request);

    const bucketConfig = this.config.buckets[request.contentType];
    const expiresInSeconds = this.config.accessUrlTtlSeconds;

    if (this.config.cdn.enabled && bucketConfig.useCdn && this.cdnSigner) {
      const signedCdn = await this.cdnSigner.createSignedDeliveryUrl({
        path: request.objectKey,
        expiresInSeconds,
        tokenClaims: {
          tenantId: request.tenantId,
          requesterId: request.requesterId,
          assetId: request.assetId,
        },
      });

      return {
        deliveryUrl: signedCdn.url,
        expiresAtIso: signedCdn.expiresAtIso,
        tokenType: "cdn_signed_url",
      };
    }

    const signedGet = await this.objectStorage.createSignedGetUrl({
      bucket: bucketConfig.bucket,
      key: request.objectKey,
      expiresInSeconds,
      responseContentDisposition: request.requiresDownload ? "attachment" : undefined,
    });

    return {
      deliveryUrl: signedGet.url,
      expiresAtIso: signedGet.expiresAtIso,
      tokenType: "object_signed_get",
    };
  }

  getMetadata(assetId: string): ContentMetadata | undefined {
    return this.metadataStore.get(assetId);
  }

  private validateUploadRequest(request: UploadIntentRequest): void {
    if (!request.fileName.trim()) {
      throw new Error("fileName is required");
    }

    if (request.contentLength <= 0) {
      throw new Error("contentLength must be greater than 0");
    }

    if (!request.contentTypeHeader.includes("/")) {
      throw new Error("contentTypeHeader must be a valid MIME type");
    }
  }

  private buildObjectKey(params: {
    tenantId: string;
    contentTypePrefix: string;
    assetId: string;
    fileName: string;
  }): string {
    const sanitizedFileName = params.fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
    return `tenants/${params.tenantId}/${params.contentTypePrefix}/raw/${params.assetId}/${sanitizedFileName}`;
  }

  private generateAssetId(tenantId: string, contentType: string): string {
    const stamp = Date.now().toString(36);
    return `${tenantId}-${contentType}-${stamp}`;
  }
}
