export interface PyhmmerDatabase {
    id: string;
    name: string;
    description?: string;
    order?: number;
}

export interface PyhmmerSearchRequest {
    database: string; // Literal from backend
    threshold: 'evalue' | 'bitscore';
    threshold_value: number;
    input: string;
}


export interface PyhmmerSearchResponse {
    id: string;
}


export interface PyhmmerTaskResult {
    status: string;
    date_created?: string;
    date_done?: string;
    result?: Record<string, unknown>[];
}


export interface PyhmmerJobDetailsResponse {
    id: string;
    status: string;
    input: string;
    threshold: string;
    threshold_value: number;
    task?: PyhmmerTaskResult;
    database?: PyhmmerDatabase;
}


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
