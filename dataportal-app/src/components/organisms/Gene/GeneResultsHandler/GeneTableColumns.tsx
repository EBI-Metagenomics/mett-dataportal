import React from 'react';
import {GeneMeta} from '../../../../interfaces/Gene';
import {getBacinteractomeUniprotUrl, getIconForEssentiality} from '../../../../utils/appConstants';

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
        key: 'alias',
        label: 'Alias',
        sortable: true,
        defaultVisible: true,
        onlyForTypeStrain: true,
        render: gene => gene.alias?.join(', ') || '---',
    },
    {
        key: 'seq_id',
        label: 'SeqId',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.seq_id || '---',
    },
    {
        key: 'locus_tag',
        label: 'Locus Tag',
        sortable: true,
        defaultVisible: true,
        render: gene => gene.locus_tag || 'Unknown Locus Tag',
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
        // render: gene => gene.uniprot_id || '',
        render: gene =>
            gene.uniprot_id ? (
                <a
                    href={getBacinteractomeUniprotUrl(gene.uniprot_id)}
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
        render: gene => gene.pfam?.join(', ') || '---',
    },
    {
        key: 'interpro',
        label: 'InterPro',
        sortable: false,
        defaultVisible: false,
        render: gene => gene.interpro?.join(', ') || '---',
    },
    {
        key: 'kegg',
        label: 'KEGG',
        sortable: false,
        defaultVisible: false,
        render: gene => gene.kegg?.join(', ') || '---',
    },
    {
        key: 'cog_id',
        label: 'COG Id',
        sortable: false,
        defaultVisible: false,
        render: gene => gene.cog_id || '---',
    },
];
