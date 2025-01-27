export interface Species {
    id: number;
    scientific_name: string;
    common_name: string;
    acronym: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
}