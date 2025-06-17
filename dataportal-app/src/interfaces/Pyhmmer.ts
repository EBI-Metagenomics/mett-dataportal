// PyhmmerDatabase: based on DatabaseResponseSchema
export interface PyhmmerDatabase {
  id: string;
  name: string;
  description?: string;
  order?: number;
}

// PyhmmerSearchRequest: based on SearchRequestSchema
export interface PyhmmerSearchRequest {
  database: string; // Literal from backend
  threshold: 'evalue' | 'bitscore';
  threshold_value: number;
  input: string;
}

// PyhmmerSearchResponse: based on SearchResponseSchema
export interface PyhmmerSearchResponse {
  id: string;
}

// PyhmmerTaskResult: based on TaskResultSchema
export interface PyhmmerTaskResult {
  status: string;
  date_created?: string;
  date_done?: string;
  result?: Record<string, unknown>[];
}

// PyhmmerJobDetailsResponse: based on JobDetailsResponseSchema
export interface PyhmmerJobDetailsResponse {
  id: string;
  status: string;
  input: string;
  threshold: string;
  threshold_value: number;
  task?: PyhmmerTaskResult;
  database?: PyhmmerDatabase;
}

// Optionally, for cut-off and gap penalties if needed in future
export interface PyhmmerCutOff {
  threshold: 'evalue' | 'bitscore';
  incE?: number;
  incdomE?: number;
  E?: number;
  domE?: number;
  incT?: number;
  incdomT?: number;
  T?: number;
  domT?: number;
}

export interface PyhmmerGapPenalties {
  popen?: number;
  pextend?: number;
  mx?: string;
}
