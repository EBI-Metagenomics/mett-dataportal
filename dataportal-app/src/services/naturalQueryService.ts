import { BaseService } from "./BaseService";

const API_BASE_SEARCH = "/query/interpret";

type ParamsType = {
  query: string;
};

type QueryResponse = Record<string, any>;

export class NaturalQueryService extends BaseService {
  static async query(request: ParamsType): Promise<QueryResponse> {
    try {
      return await this.postWithRetry<QueryResponse>(API_BASE_SEARCH, request);
    } catch (error) {
      console.error("Error processing natural query:", error);
      throw error;
    }
  }
}