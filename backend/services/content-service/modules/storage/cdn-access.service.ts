import { CdnSigner, SignedUrl } from "./types";

/**
 * Basic CDN signer abstraction.
 * Replace signature logic with provider specific implementation (CloudFront/Akamai/Fastly).
 */
export class SimpleCdnSigner implements CdnSigner {
  constructor(private readonly baseUrl: string) {}

  async createSignedDeliveryUrl(params: {
    path: string;
    expiresInSeconds: number;
    tokenClaims: Record<string, string>;
  }): Promise<SignedUrl> {
    const expiresAt = Date.now() + params.expiresInSeconds * 1000;
    const expiresAtIso = new Date(expiresAt).toISOString();

    const serializedClaims = Buffer.from(JSON.stringify(params.tokenClaims)).toString("base64url");
    const token = Buffer.from(`${params.path}.${expiresAt}.${serializedClaims}`).toString("base64url");

    return {
      url: `${this.baseUrl}/${params.path}?token=${token}&exp=${Math.floor(expiresAt / 1000)}`,
      expiresAtIso,
    };
  }
}
