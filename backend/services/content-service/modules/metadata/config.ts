export interface MetadataModuleConfig {
  enforceTagLowercase: boolean;
  maxTagsPerContent: number;
  maxTagLength: number;
}

export const defaultMetadataModuleConfig: MetadataModuleConfig = {
  enforceTagLowercase: true,
  maxTagsPerContent: 25,
  maxTagLength: 40,
};
