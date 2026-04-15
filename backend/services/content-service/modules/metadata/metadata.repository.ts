import { ContentMetadataRecord, MetadataQuery, MetadataRepository, MetadataSearchResult } from "./types";

function tokenize(value?: string): string[] {
  if (!value) {
    return [];
  }

  return value
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .filter(Boolean);
}

export class InMemoryMetadataRepository implements MetadataRepository {
  private readonly records = new Map<string, ContentMetadataRecord>();

  private key(tenantId: string, contentId: string): string {
    return `${tenantId}::${contentId}`;
  }

  async getByContentId(tenantId: string, contentId: string): Promise<ContentMetadataRecord | undefined> {
    return this.records.get(this.key(tenantId, contentId));
  }

  async upsert(record: ContentMetadataRecord): Promise<ContentMetadataRecord> {
    this.records.set(this.key(record.tenantId, record.contentId), record);
    return record;
  }

  async delete(tenantId: string, contentId: string): Promise<boolean> {
    return this.records.delete(this.key(tenantId, contentId));
  }

  async search(query: MetadataQuery): Promise<MetadataSearchResult> {
    const normalizedText = query.text?.trim().toLowerCase();
    const requestedTags = new Set((query.tagsAny ?? []).map((tag) => tag.toLowerCase()));

    const items = Array.from(this.records.values()).filter((record) => {
      if (record.tenantId !== query.tenantId) {
        return false;
      }

      if (query.language && record.language !== query.language) {
        return false;
      }

      if (requestedTags.size > 0) {
        const hasTagIntersection = record.tags.some((tag) => requestedTags.has(tag.toLowerCase()));
        if (!hasTagIntersection) {
          return false;
        }
      }

      if (normalizedText) {
        const haystackTokens = new Set([
          ...tokenize(record.title),
          ...tokenize(record.description),
          ...record.tags.map((tag) => tag.toLowerCase()),
          record.contentId.toLowerCase(),
        ]);

        const queryTokens = tokenize(normalizedText);
        const matches = queryTokens.every((token) => haystackTokens.has(token));
        if (!matches) {
          return false;
        }
      }

      return true;
    });

    return {
      items,
      total: items.length,
    };
  }
}
