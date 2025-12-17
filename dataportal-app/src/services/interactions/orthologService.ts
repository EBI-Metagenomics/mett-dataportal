import { BaseService } from "../common/BaseService";
import { GeneOrthologs, OrthologRelationship } from "../../interfaces/Ortholog";

export class OrthologService extends BaseService {
  private static readonly BASE_ENDPOINT = "/orthologs";
  private static readonly GENE_BASE_ENDPOINT = "/genes";

  /**
   * Get all orthologs for a specific gene
   */
  static async getGeneOrthologs(
    locusTag: string,
    params?: {
      species_acronym?: string;
      orthology_type?: string;
      one_to_one_only?: boolean;
      cross_species_only?: boolean;
      max_results?: number;
    }
  ): Promise<GeneOrthologs> {
    try {
      const searchParams = this.buildParams({
        species_acronym: params?.species_acronym,
        orthology_type: params?.orthology_type,
        one_to_one_only: params?.one_to_one_only || false,
        cross_species_only: params?.cross_species_only || false,
        max_results: params?.max_results || 10000,
      });

      // ApiService.get already extracts the data from the response
      const orthologs = await this.getWithRetry<GeneOrthologs>(
        `${this.GENE_BASE_ENDPOINT}/${locusTag}/orthologs`,
        searchParams
      );

      return orthologs;
    } catch (error) {
      console.error("Error fetching gene orthologs:", error);
      throw error;
    }
  }

  /**
   * Get ortholog relationship between two genes
   */
  static async getOrthologPair(
    locusTagA: string,
    locusTagB: string
  ): Promise<OrthologRelationship | null> {
    try {
      const params = this.buildParams({
        locus_tag_a: locusTagA,
        locus_tag_b: locusTagB,
      });

      // ApiService.get already extracts the data from the response
      const orthologPair = await this.getWithRetry<OrthologRelationship>(
        `${this.BASE_ENDPOINT}/pair`,
        params
      );

      return orthologPair;
    } catch (error) {
      console.error("Error fetching ortholog pair:", error);
      // If not found, return null instead of throwing
      if ((error as any)?.statusCode === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get orthologs for multiple genes in batch
   * This is useful for enriching network nodes with ortholog information
   */
  static async getBatchOrthologs(
    locusTags: string[],
    speciesAcronym?: string
  ): Promise<Map<string, OrthologRelationship[]>> {
    try {
      // Fetch orthologs for each gene
      // Note: This could be optimized on the backend with a batch endpoint
      const orthologMap = new Map<string, OrthologRelationship[]>();
      
      const promises = locusTags.map(async (locusTag) => {
        try {
          const orthologs = await this.getGeneOrthologs(locusTag, {
            species_acronym: speciesAcronym,
            max_results: 100,
          });
          orthologMap.set(locusTag, orthologs.orthologs);
        } catch (error) {
          console.warn(`Failed to fetch orthologs for ${locusTag}:`, error);
          orthologMap.set(locusTag, []);
        }
      });

      await Promise.all(promises);
      return orthologMap;
    } catch (error) {
      console.error("Error fetching batch orthologs:", error);
      throw error;
    }
  }
}

