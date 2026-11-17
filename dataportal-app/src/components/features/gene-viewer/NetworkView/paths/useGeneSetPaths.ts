import { useCallback, useState } from 'react';
import {
  PPIPathService,
  PPIPathsResult,
} from '../../../../../services/interactions/ppiPathService';
import { canFindPaths, nextGeneSet } from './geneSetRules';
import { disconnectedPairLabels, PathGraph, shouldReplaceNetwork, toPathGraph } from './toPathGraph';

const NO_PATH_MESSAGE = 'No interaction path found between the selected genes.';

export interface GeneSetPaths {
  genes: string[];
  addGene: (locusTag: string) => void;
  removeGene: (locusTag: string) => void;
  findPaths: () => Promise<void>;
  backToNetwork: () => void;
  dismissNotice: () => void;
  searching: boolean;
  canSearch: boolean;
  pathGraph: PathGraph | null;
  notice: string | null;
  disconnected: string[];
  error: string | null;
}

interface UseGeneSetPathsArgs {
  speciesAcronym?: string;
  scoreType: string;
  scoreThreshold: number;
}

function applyResult(
  result: PPIPathsResult,
  setPathGraph: (graph: PathGraph | null) => void,
  setNotice: (notice: string | null) => void,
  setDisconnected: (pairs: string[]) => void,
): void {
  if (!shouldReplaceNetwork(result)) {
    setPathGraph(null);
    setDisconnected([]);
    setNotice(NO_PATH_MESSAGE);
    return;
  }
  setPathGraph(toPathGraph(result));
  setDisconnected(disconnectedPairLabels(result));
  setNotice(null);
}

/**
 * Gene-set state for path search. The anchor neighborhood stays in NetworkView;
 * this hook only publishes a replacement graph when at least one path exists.
 */
export function useGeneSetPaths({
  speciesAcronym,
  scoreType,
  scoreThreshold,
}: UseGeneSetPathsArgs): GeneSetPaths {
  const [genes, setGenes] = useState<string[]>([]);
  const [pathGraph, setPathGraph] = useState<PathGraph | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [disconnected, setDisconnected] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearPathView = useCallback(() => {
    setPathGraph(null);
    setNotice(null);
    setDisconnected([]);
    setError(null);
  }, []);

  const addGene = useCallback((locusTag: string) => {
    const next = nextGeneSet(genes, locusTag);
    if (next === genes) return;
    setGenes([...next]);
  }, [genes]);

  const removeGene = useCallback((locusTag: string) => {
    setGenes((current) => current.filter((tag) => tag !== locusTag));
  }, []);

  const findPaths = useCallback(async () => {
    if (!canFindPaths(genes.length)) return;
    setSearching(true);
    setError(null);
    setNotice(null);
    try {
      const result = await PPIPathService.findPaths({
        locus_tags: genes,
        species_acronym: speciesAcronym,
        score_type: scoreType,
        score_threshold: scoreThreshold,
      });
      applyResult(result, setPathGraph, setNotice, setDisconnected);
    } catch (err) {
      setPathGraph(null);
      setError(err instanceof Error ? err.message : 'Path search failed');
    } finally {
      setSearching(false);
    }
  }, [genes, speciesAcronym, scoreType, scoreThreshold]);

  const backToNetwork = useCallback(() => {
    clearPathView();
  }, [clearPathView]);

  const dismissNotice = useCallback(() => {
    setNotice(null);
  }, []);

  return {
    genes,
    addGene,
    removeGene,
    findPaths,
    backToNetwork,
    dismissNotice,
    searching,
    canSearch: canFindPaths(genes.length) && !searching,
    pathGraph,
    notice,
    disconnected,
    error,
  };
}
