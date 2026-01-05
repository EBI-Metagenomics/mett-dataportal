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
   * Get orthologs for multiple genes in batch using the batch endpoint
   * This is much more efficient than making individual API calls
   */
  static async getBatchOrthologs(
    locusTags: string[],
    speciesAcronym?: string
  ): Promise<Map<string, OrthologRelationship[]>> {
    try {
      if (locusTags.length === 0) {
        return new Map<string, OrthologRelationship[]>();
      }

      // Use batch endpoint for efficiency
      const searchParams = this.buildParams({
        locus_tags: locusTags.join(','), // Comma-separated list
        species_acronym: speciesAcronym,
        max_results_per_gene: 100, // Limit per gene
      });

      // Call the batch endpoint
      const response = await this.getWithRetry<{
        results: Array<{
          locus_tag: string;
          orthologs: Array<{
            locus_tag?: string;
            species_acronym?: string;
            orthology_type?: string;
            is_one_to_one?: boolean;
            [key: string]: unknown;
          }>;
          total_count: number;
        }>;
        total_genes: number;
        total_orthologs: number;
      }>(
        `${this.BASE_ENDPOINT}/batch`,
        searchParams
      );

      // Transform response to Map<string, OrthologRelationship[]>
      const orthologMap = new Map<string, OrthologRelationship[]>();

      for (const result of response.results || []) {
        const queryLocusTag = result.locus_tag;
        const transformedOrthologs: OrthologRelationship[] = (result.orthologs || []).map((ortholog) => ({
          locus_tag_a: queryLocusTag, // The query gene (source)
          locus_tag_b: ortholog.locus_tag || '', // The ortholog gene (target)
          species_acronym_a: queryLocusTag.split('_')[0], // Extract species from locus tag
          species_acronym_b: ortholog.species_acronym,
          orthology_type: ortholog.orthology_type,
          confidence_score: ortholog.is_one_to_one ? 1.0 : 0.8, // Use 1.0 for 1:1, lower for others
        }));

        orthologMap.set(queryLocusTag, transformedOrthologs);
      }

      return orthologMap;
    } catch (error) {
      console.error("Error fetching batch orthologs:", error);
      // Return empty map on error instead of throwing, to allow partial functionality
      return new Map<string, OrthologRelationship[]>();
    }
  }
}

