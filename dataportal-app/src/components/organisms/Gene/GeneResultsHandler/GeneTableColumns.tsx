import React from 'react';
import {GeneMeta} from '../../../../interfaces/Gene';
import {getIconForEssentiality} from '../../../../utils/appConstants';

export interface ColumnDefinition {
    key: string;
    label: string;
    sortable?: boolean;
    render: (gene: GeneMeta) => React.ReactNode;
}

export const GENE_TABLE_COLUMNS: ColumnDefinition[] = [
    {
        key: 'isolate_name',
        label: 'Strain',
        sortable: true,
        render: gene => gene.isolate_name || '---',
    },
    {
        key: 'gene_name',
        label: 'Gene',
        sortable: true,
        render: gene => gene.gene_name || '---',
    },
    {
        key: 'alias',
        label: 'Alias',
        sortable: true,
        render: gene => gene.alias?.join(', ') || '---',
    },
    {
        key: 'seq_id',
        label: 'SeqId',
        sortable: true,
        render: gene => gene.seq_id || '---',
    },
    {
        key: 'locus_tag',
        label: 'Locus Tag',
        sortable: true,
        render: gene => gene.locus_tag || 'Unknown Locus Tag',
    },
    {
        key: 'product',
        label: 'Product',
        sortable: true,
        render: gene => gene.product || '',
    },
    {
        key: 'uniprot_id',
        label: 'UniProtId',
        sortable: false,
        render: gene => gene.uniprot_id || '',
    },
    {
        key: 'essentiality',
        label: 'Essentiality',
        sortable: false,
        render: gene =>
            gene.essentiality && gene.essentiality !== 'Unknown' ? (
                <span title={gene.essentiality}>
                    {getIconForEssentiality(gene.essentiality)}
                </span>
            ) : (
                '---'
            )
    },
];
