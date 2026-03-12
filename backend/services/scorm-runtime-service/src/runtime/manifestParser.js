function between(value, startTag, endTag) {
  const start = value.indexOf(startTag);
  if (start < 0) return null;
  const contentStart = start + startTag.length;
  const end = value.indexOf(endTag, contentStart);
  if (end < 0) return null;
  return value.slice(contentStart, end).trim();
}

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

  const resourceTag = resourceMatch[0];
  const href = matchAttribute(resourceTag, "href");
  if (!href) {
    throw new Error(`Resource '${resourceRef}' does not include launch href`);
  }

  const scormType = matchAttribute(resourceTag, "adlcp:scormType") || "sco";
  return {
    href,
    resourceIdentifier: resourceRef,
    scormType,
    title: between(manifestXml, "<title>", "</title>") ?? "SCORM package"
  };
}
