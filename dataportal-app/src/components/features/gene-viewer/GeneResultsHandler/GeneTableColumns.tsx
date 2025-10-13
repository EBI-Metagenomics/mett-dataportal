import React from 'react';
import {GeneMeta} from '../../../../interfaces/Gene';
import {getBacinteractomeUniprotUrl, getIconForEssentiality, renderExternalDbLinks} from '../../../../utils/common';

export interface ColumnDefinition {
    key: string;
    label: string;
    sortable?: boolean;
    defaultVisible?: boolean;
    onlyForTypeStrain?: boolean;
    render: (gene: GeneMeta) => React.ReactNode;
}

export const GENE_TABLE_COLUMNS: ColumnDefinition[] = [
    {
        key: 'locus_tag',
        label: 'Locus Tag',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.locus_tag || 'Unknown Locus Tag',
    },
    {
        key: 'alias',
        label: 'Alias',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.alias?.join(', ') || '---',
    },
    {
        key: 'isolate_name',
        label: 'Strain',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.isolate_name || '---',
    },
    {
        key: 'gene_name',
        label: 'Gene',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.gene_name || '---',
    },
    {
        key: 'seq_id',
        label: 'SeqId',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.seq_id || '---',
    },
    {
        key: 'product',
        label: 'Product',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.product || '',
    },
    {
        key: 'uniprot_id',
        label: 'UniProtId',
        sortable: false,
        defaultVisible: true,
        onlyForTypeStrain: true,
        render: gene =>
            gene.uniprot_id ? (
                <a
                    href={getBacinteractomeUniprotUrl(gene.uniprot_id, gene.species_scientific_name)}
                    target="_blank"
                    rel="noreferrer"
                >
                    {gene.uniprot_id}
                </a>
            ) : (
                '---'
            ),
    },
    {
        key: 'essentiality',
        label: 'Essentiality',
        sortable: false,
        defaultVisible: true,
        onlyForTypeStrain: true,
        render: gene =>
            gene.essentiality && gene.essentiality !== 'Unknown' ? (
                <span title={gene.essentiality}>
                    {getIconForEssentiality(gene.essentiality)}
                </span>
            ) : (
                '---'
            )
    },
    {
        key: 'pfam',
        label: 'PFAM',
        sortable: false,
        defaultVisible: false,
        render: gene => renderExternalDbLinks('PFAM', gene.pfam || []),
    },
    {
        key: 'interpro',
        label: 'InterPro',
        sortable: false,
        defaultVisible: false,
        render: gene => renderExternalDbLinks('INTERPRO', gene.interpro || []),
    },
    {
        key: 'kegg',
        label: 'KEGG',
        sortable: false,
        defaultVisible: false,
        render: gene => renderExternalDbLinks('KEGG', gene.kegg || []),
    },
    {
        key: 'cog_funcats',
        label: 'COG Catergories',
        sortable: false,
        defaultVisible: false,
        render: gene => gene.cog_funcats || '---',
    },
    {
        key: 'cog_id',
        label: 'COG Id',
        sortable: false,
        defaultVisible: false,
        render: gene => renderExternalDbLinks('COG', gene.cog_id || []),
    },
    {
        key: 'amr',
        label: 'AMR class/subclass',
        sortable: false,
        defaultVisible: false,
        render: gene =>
            gene.amr && gene.amr.length > 0
                ? gene.amr.map((amr, idx) =>
                    <div key={idx}>
                        {amr.drug_class ? `${amr.drug_class}` : ''} {amr.drug_subclass ? `(${amr.drug_subclass})` : ''}
                    </div>
                )
                : '---',
    },
];
