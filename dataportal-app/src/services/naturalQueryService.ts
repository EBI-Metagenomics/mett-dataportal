import { ApiService } from "./api";

const API_BASE_SEARCH = "/query/interpret";

type ParamsType = {
  query: string;
};

type QueryResponse = Record<string, any>;

export class NaturalQueryService {
  static async query(request: ParamsType): Promise<QueryResponse> {
    return await ApiService.post(API_BASE_SEARCH, request);
  }
}