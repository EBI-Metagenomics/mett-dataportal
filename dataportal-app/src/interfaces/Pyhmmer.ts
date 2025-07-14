export interface PyhmmerDatabase {
    id: string;
    name: string;
    type: string;
    version: string;
    release_date?: string;
    order: number;
}

export interface PyhmmerMXChoice {
    value: string;
    label: string;
}

export interface PyhmmerResult {
    query: string;
    target: string;
    evalue: string;
    score: string;
    num_hits: number;
    num_significant: number;
    bias?: number;
    description?: string;

    [key: string]: unknown;
}


export interface PyhmmerSearchRequest {
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: number;
    input: string;
    mx?: string;
    
    // E-value parameters
    E?: number | null;
    domE?: number | null;
    incE?: number | null;
    incdomE?: number | null;
    
    // Bit score parameters
    T?: number | null;
    domT?: number | null;
    incT?: number | null;
    incdomT?: number | null;
    
    // Gap penalties
    popen?: number;
    pextend?: number;
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
