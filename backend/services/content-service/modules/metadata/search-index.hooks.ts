import { ContentMetadataRecord, SearchIndexEvent, SearchIndexHook } from "./types";

export class InMemorySearchIndexHook implements SearchIndexHook {
  readonly events: SearchIndexEvent[] = [];

  async onMetadataUpserted(record: ContentMetadataRecord): Promise<void> {
    this.events.push({
      type: "upsert",
      tenantId: record.tenantId,
      contentId: record.contentId,
      occurredAtIso: new Date().toISOString(),
    });
  }

  async onMetadataDeleted(params: { tenantId: string; contentId: string }): Promise<void> {
    this.events.push({
      type: "delete",
      tenantId: params.tenantId,
      contentId: params.contentId,
      occurredAtIso: new Date().toISOString(),
    });
  }
}
