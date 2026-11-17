export const GENE_SET_MIN = 2;
export const GENE_SET_MAX = 5;

export function canFindPaths(count: number): boolean {
  return count >= GENE_SET_MIN && count <= GENE_SET_MAX;
}

/** Add a locus tag when the set is below the cap and the tag is new. */
export function nextGeneSet(current: readonly string[], locusTag: string): readonly string[] {
  const tag = locusTag.trim();
  if (!tag || current.includes(tag) || current.length >= GENE_SET_MAX) {
    return current;
  }
  return [...current, tag];
}
