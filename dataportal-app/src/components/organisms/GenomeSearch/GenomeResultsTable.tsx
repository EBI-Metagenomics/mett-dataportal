import React, {useEffect, useState} from 'react';
import styles from './GenomeResultsTable.module.scss';

interface GenomeResultsTableProps {
    results: any[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    selectedGenomes: { id: number; name: string }[];
    onToggleGenomeSelect: (genome: { id: number; name: string }) => void;
}

const GenomeResultsTable: React.FC<GenomeResultsTableProps> = ({
                                                                   results,
                                                                   onSortClick,
                                                                   selectedGenomes,
                                                                   onToggleGenomeSelect
                                                               }) => {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    useEffect(() => {
        console.log('Updated results:', results);
    }, [results]);

    const handleSort = (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        console.log("sort originated with sort order - " + sortOrder);
        onSortClick(field, newSortOrder);
    };

    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th onClick={() => handleSort('species')} className="{`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}">
                    Species
                    {sortField === 'species' ? (
                        <span
                            className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                            style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th onClick={() => handleSort('isolate_name')}
                    className="{`vf-table__heading ${styles.vfTableHeading}`} ${styles.clickableHeader}">
                    Strain
                    {sortField === 'isolate_name' ? (
                        <span
                            className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                            style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th className="{`vf-table__heading ${styles.vfTableHeading}`}">Assembly</th>
                <th className="{`vf-table__heading ${styles.vfTableHeading}`}">Annotations</th>
                <th className="{`vf-table__heading ${styles.vfTableHeading}`}">Actions</th>
                <th className="{`vf-table__heading ${styles.vfTableHeading}`}">Add to Gene Search</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((result, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}><i>{result.species || 'Unknown Species'}</i>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.isolate_name || 'Unknown Isolate'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={result.fasta_url || '#'}>{result.assembly_name || 'Unknown Assembly'}<span
                            className="icon icon-common icon-download"
                            style={{paddingLeft: '5px'}}></span></a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={result.gff_url || '#'}>GFF<span
                            className="icon icon-common icon-download"
                            style={{paddingLeft: '5px'}}></span></a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={`/gene-viewer/genome/${result.id}/`}>Browse</a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <button
                            className={styles.toggleButton}
                            onClick={() => onToggleGenomeSelect({id: result.id, name: result.isolate_name})}
                        >
                            {selectedGenomes.some(genome => genome.id === result.id) ? '−' : '+'}
                        </button>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GenomeResultsTable;
