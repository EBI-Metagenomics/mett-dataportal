import React from 'react';
import { GeneMeta } from '../../../../interfaces/Gene';
import styles from './GeneSearchResults.module.scss';

interface GeneSearchResultsProps {
    results: GeneMeta[];
    isLoading: boolean;
    totalHits: number;
    page: number;
    pageSize: number;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
    onSortChange: (field: string, order: 'asc' | 'desc') => void;
}

const GeneSearchResults: React.FC<GeneSearchResultsProps> = ({
    results,
    isLoading,
    totalHits,
    page,
    pageSize,
    sortField,
    sortOrder,
    onPageChange,
    onPageSizeChange,
    onSortChange,
}) => {
    const handleSort = (field: string) => {
        const newOrder = field === sortField && sortOrder === 'asc' ? 'desc' : 'asc';
        onSortChange(field, newOrder);
    };

    if (isLoading) {
        return <div className={styles.loading}>Loading...</div>;
    }

    return (
        <div className={styles.resultsContainer}>
            <div className={styles.resultsHeader}>
                <h3>Search Results ({totalHits} total)</h3>
            </div>
            
            <table className={styles.resultsTable}>
                <thead>
                    <tr>
                        <th onClick={() => handleSort('locus_tag')}>
                            Locus Tag {sortField === 'locus_tag' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => handleSort('gene_name')}>
                            Gene Name {sortField === 'gene_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => handleSort('product')}>
                            Product {sortField === 'product' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th onClick={() => handleSort('isolate_name')}>
                            Isolate {sortField === 'isolate_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {results.map((gene) => (
                        <tr key={gene.locus_tag}>
                            <td>
                                <a href={`/gene?locus_tag=${gene.locus_tag}`}>
                                    {gene.locus_tag}
                                </a>
                            </td>
                            <td>{gene.gene_name || '-'}</td>
                            <td>{gene.product || '-'}</td>
                            <td>{gene.isolate_name}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default GeneSearchResults; 