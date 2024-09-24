import React from 'react';
import styles from './GenomeResultsTable.module.scss';

interface GenomeResultsTableProps {
    results: any[];
    onSortClick: (sortField: string) => void;
}

const GenomeResultsTable: React.FC<GenomeResultsTableProps> = ({ results, onSortClick }) => {
    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
                <tr className="vf-table__row">
                    <th className="vf-table__heading" scope="col">
                        <button
                            className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                            onClick={() => onSortClick('species')}
                        >
                            Species
                        </button>
                    </th>
                    <th className="vf-table__heading" scope="col">
                        <button
                            className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                            onClick={() => onSortClick('isolate_name')}
                        >
                            Strain
                        </button>
                    </th>
                    <th className="vf-table__heading" scope="col">Assembly</th>
                    <th className="vf-table__heading" scope="col">Annotations</th>
                    <th className="vf-table__heading" scope="col">Actions</th>
                </tr>
            </thead>
            <tbody className="vf-table__body">
                {results.map((result, index) => (
                    <tr key={index} className="vf-table__row">
                        <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.species || 'Unknown Species'}</td>
                        <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.isolate_name || 'Unknown Isolate'}</td>
                        <td className={`vf-table__cell ${styles.vfTableCell}`}>
                            <a href={result.fasta_file || '#'}>{result.assembly_name || 'Unknown Assembly'}</a>
                        </td>
                        <td className={`vf-table__cell ${styles.vfTableCell}`}><a href={result.gff_file || '#'}>GFF</a></td>
                        <td className={`vf-table__cell ${styles.vfTableCell}`}><a href={`/jbrowse/${result.id}/`}>Browse</a></td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

export default GenomeResultsTable;
