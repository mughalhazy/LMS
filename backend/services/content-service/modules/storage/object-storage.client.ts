import { StorageProvider, SignedUrl, StoredObject } from "./types";

/**
 * In-memory implementation that demonstrates object storage integration points.
 * Replace this with a cloud provider SDK adapter (S3/GCS/Azure Blob) in production.
 */
export class InMemoryObjectStorageClient implements StorageProvider {
  private objects = new Map<string, StoredObject>();

  async createSignedPutUrl(params: {
    bucket: string;
    key: string;
    contentType: string;
    contentLength: number;
    expiresInSeconds: number;
    checksumSha256?: string;
  }): Promise<SignedUrl> {
    const expiresAtIso = new Date(Date.now() + params.expiresInSeconds * 1000).toISOString();

    const objectRef = `${params.bucket}/${params.key}`;
    this.objects.set(objectRef, {
      bucket: params.bucket,
      key: params.key,
      sizeBytes: params.contentLength,
      checksumSha256: params.checksumSha256,
      etag: `etag-${params.key}`,
      uploadedAtIso: new Date().toISOString(),
    });

    return {
      url: `https://object-storage.local/${params.bucket}/${params.key}?signed=put`,
      expiresAtIso,
      headers: {
        "content-type": params.contentType,
      },
    };
  }

  async createSignedGetUrl(params: {
    bucket: string;
    key: string;
    expiresInSeconds: number;
    responseContentDisposition?: string;
  }): Promise<SignedUrl> {
    const expiresAtIso = new Date(Date.now() + params.expiresInSeconds * 1000).toISOString();

    const disposition = params.responseContentDisposition
      ? `&response-content-disposition=${encodeURIComponent(params.responseContentDisposition)}`
      : "";

    return {
      url: `https://object-storage.local/${params.bucket}/${params.key}?signed=get${disposition}`,
      expiresAtIso,
    };
  }

  async headObject(params: { bucket: string; key: string }): Promise<StoredObject> {
    const objectRef = `${params.bucket}/${params.key}`;
    const found = this.objects.get(objectRef);

    if (!found) {
      throw new Error(`Object not found: ${objectRef}`);
    }

    return found;
  }
}
