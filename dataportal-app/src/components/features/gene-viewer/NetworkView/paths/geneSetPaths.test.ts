import { canFindPaths, nextGeneSet } from './geneSetRules';
import { disconnectedPairLabels, shouldReplaceNetwork, toPathGraph } from './toPathGraph';

describe('gene set size', () => {
  it('allows Find paths only for 2 to 5 genes', () => {
    expect(canFindPaths(1)).toBe(false);
    expect(canFindPaths(2)).toBe(true);
    expect(canFindPaths(5)).toBe(true);
    expect(canFindPaths(6)).toBe(false);
  });

  it('refuses a sixth gene and duplicates', () => {
    expect(nextGeneSet(['A', 'B', 'C', 'D', 'E'], 'F')).toEqual(['A', 'B', 'C', 'D', 'E']);
    expect(nextGeneSet(['A', 'B'], 'A')).toEqual(['A', 'B']);
    expect(nextGeneSet(['A'], 'B')).toEqual(['A', 'B']);
  });
});

describe('path view replacement', () => {
  it('keeps the current network when the response has no edges', () => {
    expect(shouldReplaceNetwork({ edges: [] })).toBe(false);
  });

  it('builds seed and intermediate nodes when a path exists', () => {
    const graph = toPathGraph({
      seeds: [
        { id: 'P1', locus_tag: 'BU_A', role: 'seed' },
        { id: 'P2', locus_tag: 'BU_B', role: 'seed' },
      ],
      intermediates: [{ id: 'PX', locus_tag: 'BU_X', role: 'intermediate' }],
      edges: [{ source: 'P1', target: 'PX', weight: 0.8 }],
      paths: [],
      disconnected_pairs: [{ locus_tag_a: 'BU_A', locus_tag_b: 'BU_C' }],
    });
    expect(shouldReplaceNetwork(graph)).toBe(true);
    expect(graph.nodes.map((node) => node.pathRole)).toEqual(['seed', 'seed', 'intermediate']);
    expect(disconnectedPairLabels({
      seeds: [],
      intermediates: [],
      edges: graph.edges,
      paths: [],
      disconnected_pairs: [{ locus_tag_a: 'BU_A', locus_tag_b: 'BU_C' }],
    })).toEqual(['BU_A — BU_C']);
  });
});
