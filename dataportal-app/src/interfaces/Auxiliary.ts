export interface LinkData {
    template: string;
    alias: string;
}


export interface FacetItem {
    value: string;
    count: number;
    selected?: boolean;
}

export interface FacetOperator {
    [key: string]: 'AND' | 'OR';
}