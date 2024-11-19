export interface GeneMeta {
    id: number;
    seq_id: string;
    gene_name: string;
    description: string;
    strain_id: number;
    strain: string;
    assembly: string;
    locus_tag: string;
    cog: string | null;
    kegg: string | null;
    pfam: string | null;
    interpro: string | null;
    dbxref: string | null;
    ec_number: string | null;
    product: string | null;
    start_position: number | null;
    end_position: number | null;
    annotations: Record<string, any> | null;
}

export interface GeneSuggestion {
    gene_id: number;
    gene_name: string | '';
    strain_name: string;
    product: string | null;
    locus_tag: string;
    kegg: string | null;
    pfam: string | null;
    interpro: string | null;
    dbxref: string | null;
}