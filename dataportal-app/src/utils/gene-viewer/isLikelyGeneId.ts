/**
 * Distinguish real gene locus tags from generic JBrowse container IDs
 * like "tracksContainer", "svgfeatures", "display-placeholderId", etc.
 */
export function isLikelyGeneId(rawId: string | null): boolean {
  if (!rawId) return false;
  const id = rawId.trim();
  if (!id) return false;

  if (/(container|tracks?|svg|placeholder|display)/i.test(id)) {
    return false;
  }

  if (!/[A-Za-z]/.test(id) || !/\d/.test(id)) {
    return false;
  }

  if (/\s/.test(id)) {
    return false;
  }

  return true;
}
