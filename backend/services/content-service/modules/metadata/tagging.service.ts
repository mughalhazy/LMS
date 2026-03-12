import { MetadataModuleConfig } from "./config";

export class TaggingService {
  constructor(private readonly config: MetadataModuleConfig) {}

  normalizeTags(input: string[] | undefined): string[] {
    if (!input || input.length === 0) {
      return [];
    }

    const seen = new Set<string>();
    const normalized: string[] = [];

    for (const rawTag of input) {
      const trimmed = rawTag.trim();
      if (!trimmed) {
        continue;
      }

      const maybeLowercase = this.config.enforceTagLowercase ? trimmed.toLowerCase() : trimmed;
      const cleaned = maybeLowercase.slice(0, this.config.maxTagLength);

      if (seen.has(cleaned)) {
        continue;
      }

      seen.add(cleaned);
      normalized.push(cleaned);

      if (normalized.length >= this.config.maxTagsPerContent) {
        break;
      }
    }

    return normalized;
  }

  addTags(existing: string[], toAdd: string[]): string[] {
    return this.normalizeTags([...existing, ...toAdd]);
  }

  removeTags(existing: string[], toRemove: string[]): string[] {
    const toRemoveSet = new Set(this.normalizeTags(toRemove));
    return existing.filter((tag) => !toRemoveSet.has(tag));
  }
}
