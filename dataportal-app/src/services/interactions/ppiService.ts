import { BaseService } from "../common/BaseService";
import { 
  PPIInteraction, 
  PPINetworkData, 
  PPINetworkProperties,
  PPINetworkQuery,
  PPIScoreType,
  PPINeighborhoodData,
  PPIDataSources,
  PPIStringNetworkRaw,
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
   * Get available PPI data sources (local ES, STRING DB, etc.).
   * This allows the UI to treat data sources generically.
   */
  static async getDataSources(): Promise<PPIDataSources> {
    try {
      return await this.getWithRetry<PPIDataSources>(
        `${this.BASE_ENDPOINT}/data-sources`
      );
    } catch (error) {
      console.error("Error fetching PPI data sources:", error);
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
   * Get protein neighborhood (top N interactors).
   * Pass locus_tag for local genes, or string_id for STRING-only nodes (resolved via feature index; empty if unmapped).
   */
  static async getProteinNeighborhood(params: {
    locus_tag?: string | null;
    string_id?: string | null;
    species_acronym?: string | null;
    n?: number;
    score_type?: string;
    score_threshold?: number;
  }): Promise<PPINeighborhoodData> {
    try {
      const searchParams = this.buildParams({
        locus_tag: params.locus_tag ?? undefined,
        string_id: params.string_id ?? undefined,
        species_acronym: params.species_acronym ?? undefined,
        n: params.n ?? 5,
        score_type: params.score_type ?? "ds_score",
        score_threshold: params.score_threshold ?? 0,
      });

      return await this.getWithRetry<PPINeighborhoodData>(
        `${this.BASE_ENDPOINT}/neighborhood`,
        searchParams
      );
    } catch (error) {
      console.error("Error fetching protein neighborhood:", error);
      throw error;
    }
  }

  /**
   * Get STRING DB network for a PPI pair or explicit STRING protein IDs.
   * This delegates to the backend, which calls the STRING DB API.
   */
  static async getStringNetwork(params: {
    pair_id?: string;
    protein_ids?: string[];
    locus_tag?: string;
    species_acronym?: string;
    required_score?: number;
    network_type?: string;
    evidence_channels?: string[];
  }): Promise<PPIStringNetworkRaw> {
    try {
      const searchParams = this.buildParams({
        pair_id: params.pair_id,
        protein_ids: params.protein_ids,
        locus_tag: params.locus_tag,
        species_acronym: params.species_acronym,
        required_score: params.required_score,
        network_type: params.network_type ?? "physical",
        evidence_channels: params.evidence_channels,
      });

      return await this.getWithRetry<PPIStringNetworkRaw>(
        `${this.BASE_ENDPOINT}/string-network`,
        searchParams
      );
    } catch (error) {
      console.error("Error fetching STRING network:", error);
      throw error;
    }
  }
}

