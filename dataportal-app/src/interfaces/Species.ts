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