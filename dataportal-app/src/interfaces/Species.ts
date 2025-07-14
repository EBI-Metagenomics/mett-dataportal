import { PaginatedApiResponse, SuccessApiResponse } from "./ApiResponse";

export interface Species {
    acronym: string;
    scientific_name: string;
    common_name: string;
    taxonomy_id: number;
}

// Legacy pagination interface (for backward compatibility)
export interface PaginatedResponse<T> {
    data: T[];
    total: number;
}

// New standardized response types
export type SpeciesApiResponse = SuccessApiResponse<Species>;
export type SpeciesListResponse = SuccessApiResponse<Species[]>;