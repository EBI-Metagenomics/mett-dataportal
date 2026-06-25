import {GeneMeta} from '../../../../interfaces/Gene';
import {normalizeFilterValues} from '../../../../utils/common/filterUtils';

export interface FeaturePanelGeneData {
    locusTag: string;
    gene: string;
    product: string;
    alias: string[];
    start: number;
    end: number;
    strand: number;
    seqId: string;
    essentiality: string;
    uniprotId: string;
    pfam: string[];
    interpro: string[];
    kegg: string[];
    cog: string[];
    cogCategories: string[];
    dbxref: { db: string; ref: string }[] | null;
    inference: string;
    productSource: string;
    eggnog: string;
    ontologyTerms: { ontology_type?: string; ontology_id?: string; ontology_description?: string }[];
    ecNumber: string;
    ufProtRecEcnumber: string;
    ufProtRecShortname: string;
    ufProtAltFullname: string;
    ufProtAltShortname: string;
    ufProtAltEcnumber: string;
    ufChebi: string[];
    ufPirsrCofactor: string;
    ufGeneNameSynonym: string;
    dbcanProtType: string;
    dbcanProtFamily: string[];
    substrateDbcanPul: string;
    substrateDbcanSub: string;
    geccoBgcType: string;
    nearestMibig: string;
    nearestMibigClass: string;
    antismashBgcFunction: string;
    mgeId: string;
    mgeTypes: string[];
    defenseFinderType: string;
    defenseFinderSubtype: string;
    extraCopyNumber: number | null;
    note: string;
    ufKeyword: string[];
    ufOntologyTerms: string[];
    ufGeneName: string;
    ufProtRecFullname: string;
    amr: GeneMeta['amr'];
    hasAmr: boolean;
    proteinSequence: string;
    isolateName: string;
    speciesName: string;
}

const EMPTY_FEATURE_DATA: FeaturePanelGeneData = {
    locusTag: 'N/A',
    gene: '',
    product: 'N/A',
    alias: [],
    start: 0,
    end: 0,
    strand: 0,
    seqId: 'N/A',
    essentiality: '',
    uniprotId: '',
    pfam: [],
    interpro: [],
    kegg: [],
    cog: [],
    cogCategories: [],
    dbxref: null,
    inference: '',
    productSource: '',
    eggnog: '',
    ontologyTerms: [],
    ecNumber: '',
    ufProtRecEcnumber: '',
    ufProtRecShortname: '',
    ufProtAltFullname: '',
    ufProtAltShortname: '',
    ufProtAltEcnumber: '',
    ufChebi: [],
    ufPirsrCofactor: '',
    ufGeneNameSynonym: '',
    dbcanProtType: '',
    dbcanProtFamily: [],
    substrateDbcanPul: '',
    substrateDbcanSub: '',
    geccoBgcType: '',
    nearestMibig: '',
    nearestMibigClass: '',
    antismashBgcFunction: '',
    mgeId: '',
    mgeTypes: [],
    defenseFinderType: '',
    defenseFinderSubtype: '',
    extraCopyNumber: null,
    note: '',
    ufKeyword: [],
    ufOntologyTerms: [],
    ufGeneName: '',
    ufProtRecFullname: '',
    amr: null,
    hasAmr: false,
    proteinSequence: '',
    isolateName: '',
    speciesName: '',
};

function asStringArray(value: unknown): string[] {
    if (Array.isArray(value)) {
        return normalizeFilterValues(value) as string[];
    }
    if (value) {
        return normalizeFilterValues([value]) as string[];
    }
    return [];
}

export function mapGeneMetaToFeatureData(featureData: unknown): FeaturePanelGeneData {
    if (!featureData) {
        return EMPTY_FEATURE_DATA;
    }

    const data = (featureData as { data?: GeneMeta })?.data || (featureData as GeneMeta);
    const unifire = data.unifire ?? {};
    const dbcan = data.dbcan ?? {};
    const bgc = data.bgc ?? {};
    const mobilome = data.mobilome ?? {};
    const defense = data.defense ?? {};
    const metadata = data.metadata ?? {};

    return {
        locusTag: data.locus_tag || 'N/A',
        gene: data.gene_name || '',
        product: data.product || 'N/A',
        alias: Array.isArray(data.alias) ? data.alias : (data.alias ? [data.alias] : []),
        start: data.start_position || 0,
        end: data.end_position || 0,
        strand: (data as { strand?: number }).strand || 0,
        seqId: data.seq_id || 'N/A',
        essentiality: data.essentiality || '',
        uniprotId: data.uniprot_id || '',
        pfam: asStringArray(data.pfam),
        interpro: asStringArray(data.interpro),
        kegg: asStringArray(data.kegg),
        cog: asStringArray(data.cog_id),
        cogCategories: asStringArray(data.cog_funcats),
        amr: data.amr ?? [],
        hasAmr: data.has_amr_info || (Array.isArray(data.amr) && data.amr.length > 0),
        dbxref: data.dbxref ?? [],
        inference: data.inference || '',
        productSource: data.product_source || '',
        eggnog: data.eggnog || '',
        ontologyTerms: Array.isArray(data.ontology_terms) ? data.ontology_terms : [],
        ecNumber: data.ec_number || '',
        ufProtRecEcnumber: unifire.protein_ec_number || '',
        ufProtRecShortname: unifire.protein_shortname || '',
        ufProtAltFullname: unifire.alt_protein_fullname || '',
        ufProtAltShortname: unifire.alt_protein_shortname || '',
        ufProtAltEcnumber: unifire.alt_ec_number || '',
        ufChebi: Array.isArray(unifire.chebi) ? unifire.chebi : [],
        ufPirsrCofactor: unifire.pirsr_cofactor || '',
        ufGeneNameSynonym: unifire.gene_name_synonym || '',
        dbcanProtType: dbcan.prot_type || '',
        dbcanProtFamily: Array.isArray(dbcan.prot_family) ? dbcan.prot_family : [],
        substrateDbcanPul: dbcan.substrate_pul || '',
        substrateDbcanSub: dbcan.substrate_sub || '',
        geccoBgcType: bgc.gecco_bgc_type || '',
        nearestMibig: bgc.nearest_mibig || '',
        nearestMibigClass: bgc.nearest_mibig_class || '',
        antismashBgcFunction: bgc.antismash_bgc_function || '',
        mgeId: mobilome.mge_id || '',
        mgeTypes: Array.isArray(mobilome.mge_types) ? mobilome.mge_types : [],
        defenseFinderType: defense.finder_type || '',
        defenseFinderSubtype: defense.finder_subtype || '',
        extraCopyNumber: metadata.extra_copy_number ?? null,
        note: metadata.note || '',
        ufKeyword: asStringArray(data.uf_keyword ?? unifire.keywords),
        ufOntologyTerms: asStringArray(data.uf_ontology_terms ?? unifire.ontology_terms),
        ufGeneName: data.uf_gene_name || unifire.gene_name || '',
        ufProtRecFullname: data.uf_prot_rec_fullname || unifire.protein_fullname || '',
        proteinSequence: (data as { protein_sequence?: string }).protein_sequence || '',
        isolateName: data.isolate_name || '',
        speciesName: data.species_scientific_name || '',
    };
}
