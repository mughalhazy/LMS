function matchAttribute(fragment, attribute) {
  const regex = new RegExp(`${attribute}="([^"]+)"`);
  const match = fragment.match(regex);
  return match ? match[1] : null;
}

export function resolveLaunchUrl(manifestXml, scoIdentifier) {
  if (!manifestXml || !scoIdentifier) {
    throw new Error("manifestXml and scoIdentifier are required");
  }

  const itemRegex = new RegExp(`<item[^>]*identifier="${scoIdentifier}"[^>]*>`, "i");
  const itemMatch = manifestXml.match(itemRegex);
  if (!itemMatch) {
    throw new Error(`SCO identifier '${scoIdentifier}' was not found in imsmanifest.xml`);
  }

  const itemTag = itemMatch[0];
  const resourceRef = matchAttribute(itemTag, "identifierref");
  if (!resourceRef) {
    throw new Error(`SCO '${scoIdentifier}' is missing identifierref`);
  }

  const resourceRegex = new RegExp(`<resource[^>]*identifier="${resourceRef}"[^>]*>`, "i");
  const resourceMatch = manifestXml.match(resourceRegex);
  if (!resourceMatch) {
    throw new Error(`Resource '${resourceRef}' referenced by SCO '${scoIdentifier}' was not found`);
  }

  const href = matchAttribute(resourceMatch[0], "href");
  if (!href) {
    throw new Error(`Resource '${resourceRef}' does not include launch href`);
  }

  return { href, resourceIdentifier: resourceRef };
}
