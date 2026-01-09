import { BaseService } from "../common/BaseService";
import { 
  PPIInteraction, 
  PPINetworkData, 
  PPINetworkProperties,
  PPINetworkQuery,
  PPIScoreType 
} from "../../interfaces/PPI";

export class PPIService extends BaseService {
  private static readonly BASE_ENDPOINT = "/ppi";

  /**
   * Get available score types for PPI filtering
   */
  static async getAvailableScoreTypes(): Promise<PPIScoreType> {
    try {
      return await this.getWithRetry<PPIScoreType>(
        `${this.BASE_ENDPOINT}/scores/available`
      );
    } catch (error) {
      console.error("Error fetching available score types:", error);
      throw error;
    }
  }

  /**
   * Search for PPI interactions
   */
  static async searchInteractions(params: {
    species_acronym?: string;
    isolate_name?: string;
    score_type?: string;
    score_threshold?: number;
    protein_id?: string;
    locus_tag?: string;
    has_xlms?: boolean;
    has_string?: boolean;
    has_operon?: boolean;
    has_ecocyc?: boolean;
    page?: number;
    per_page?: number;
  }): Promise<{ data: PPIInteraction[]; pagination: any }> {
    try {
      const searchParams = this.buildParams({
        species_acronym: params.species_acronym,
        isolate_name: params.isolate_name,
        score_type: params.score_type,
        score_threshold: params.score_threshold,
        protein_id: params.protein_id,
        locus_tag: params.locus_tag,
        has_xlms: params.has_xlms,
        has_string: params.has_string,
        has_operon: params.has_operon,
        has_ecocyc: params.has_ecocyc,
        page: params.page || 1,
        per_page: params.per_page || 20,
      });

      return await this.getWithRetry<{ data: PPIInteraction[]; pagination: any }>(
        `${this.BASE_ENDPOINT}/interactions`,
        searchParams
      );
    } catch (error) {
      console.error("Error searching PPI interactions:", error);
      throw error;
    }
  }

  /**
   * Get PPI network data for a specific score type and threshold
   */
  static async getNetworkData(query: PPINetworkQuery): Promise<PPINetworkData> {
    try {
      const params = this.buildParams({
        score_threshold: query.score_threshold,
        species_acronym: query.species_acronym,
        isolate_name: query.isolate_name,
        locus_tag: query.locus_tag,
        include_properties: query.include_properties || false,
      });

      // ApiService.get already extracts the data from the response
      const networkData = await this.getWithRetry<PPINetworkData>(
        `${this.BASE_ENDPOINT}/network/${query.score_type}`,
        params
      );

      return networkData;
    } catch (error) {
      console.error("Error fetching PPI network data:", error);
      throw error;
    }
  }

  /**
   * Get PPI network properties
   */
  static async getNetworkProperties(query: {
    score_type: string;
    score_threshold: number;
    species_acronym?: string;
    isolate_name?: string;
  }): Promise<PPINetworkProperties> {
    try {
      const params = this.buildParams({
        score_type: query.score_type,
        score_threshold: query.score_threshold,
        species_acronym: query.species_acronym,
        isolate_name: query.isolate_name,
      });

      // ApiService.get already extracts the data from the response
      const properties = await this.getWithRetry<PPINetworkProperties>(
        `${this.BASE_ENDPOINT}/network-properties`,
        params
      );

      return properties;
    } catch (error) {
      console.error("Error fetching PPI network properties:", error);
      throw error;
    }
  }

  /**
   * Get all neighbors for a specific protein
   */
  static async getAllNeighbors(params: {
    protein_id?: string;
    locus_tag?: string;
    species_acronym?: string;
  }): Promise<{ protein_id: string; interactions: PPIInteraction[] }> {
    try {
      const searchParams = this.buildParams({
        protein_id: params.protein_id,
        locus_tag: params.locus_tag,
        species_acronym: params.species_acronym,
      });

      return await this.getWithRetry<{ protein_id: string; interactions: PPIInteraction[] }>(
        `${this.BASE_ENDPOINT}/neighbors`,
        searchParams
      );
    } catch (error) {
      console.error("Error fetching protein neighbors:", error);
      throw error;
    }
  }

  /**
   * Get lightweight PPI network data (optimized for global cloud view)
   * Returns minimal data (IDs, locus tags, scores) with configurable limit
   */
  static async getLightweightNetworkData(query: {
    score_type: string;
    score_threshold: number;
    species_acronym?: string;
    isolate_name?: string;
    max_interactions?: number;
  }): Promise<PPINetworkData> {
    try {
      const params = this.buildParams({
        score_threshold: query.score_threshold,
        species_acronym: query.species_acronym,
        isolate_name: query.isolate_name,
        max_interactions: query.max_interactions || 50000,
      });

      // The lightweight endpoint returns the same structure but with minimal fields
      const networkData = await this.getWithRetry<PPINetworkData>(
        `${this.BASE_ENDPOINT}/network-lightweight/${query.score_type}`,
        params
      );

      return networkData;
    } catch (error) {
      console.error("Error fetching lightweight PPI network data:", error);
      throw error;
    }
  }
}

