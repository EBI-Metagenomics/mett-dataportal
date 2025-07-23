import {SuccessApiResponse} from "./ApiResponse";

export interface Species {
    acronym: string;
    scientific_name: string;
    common_name: string;
    taxonomy_id: number;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
}

export type SpeciesApiResponse = SuccessApiResponse<Species>;
export type SpeciesListResponse = SuccessApiResponse<Species[]>;