export interface Species {
    id: number;
    scientific_name: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
}