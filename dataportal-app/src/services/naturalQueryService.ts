import { BaseService } from "./BaseService";

const API_BASE_SEARCH = "/query/interpret";

type ParamsType = {
  query: string;
};

type QueryResponse = Record<string, any>;

export class NaturalQueryService extends BaseService {
  static async query(request: ParamsType): Promise<QueryResponse> {
    try {
      // Send query as URL parameter, not in request body
      const encodedQuery = encodeURIComponent(request.query);
      const urlWithQuery = `${API_BASE_SEARCH}?query=${encodedQuery}`;
      return await this.postWithRetry<QueryResponse>(urlWithQuery, {});
    } catch (error) {
      console.error("Error processing natural query:", error);
      throw error;
    }
  }
}