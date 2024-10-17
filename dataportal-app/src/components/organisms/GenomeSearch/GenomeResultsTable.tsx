import React from 'react';
import styles from './GenomeResultsTable.module.scss';

interface GenomeResultsTableProps {
    results: any[];
    onSortClick: (sortField: string) => void;
    selectedGenomes: { id: number; name: string }[];
    onToggleGenomeSelect: (genome: { id: number; name: string }) => void;
}

const GenomeResultsTable: React.FC<GenomeResultsTableProps> = ({
                                                                   results,
                                                                   onSortClick,
                                                                   selectedGenomes,
                                                                   onToggleGenomeSelect
                                                               }) => {
    const isGenomeSelected = (genomeId: number) => {
        return selectedGenomes.some(genome => genome.id === genomeId);
    };

    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Species
                    <button
                        className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                        onClick={() => onSortClick('species')}
                    />
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Strain
                    <button
                        className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                        onClick={() => onSortClick('isolate_name')}
                    />
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Assembly</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Annotations</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Add to Gene Search</th>
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
                    <td className={`vf-table__cell ${styles.vfTableCell}`}><a href={`/gene-viewer/genome/${result.id}/`}>Browse</a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <button
                            className={styles.toggleButton}
                            onClick={() => onToggleGenomeSelect({id: result.id, name: result.isolate_name})}
                        >
                            {isGenomeSelected(result.id) ? '−' : '+'} {/* Toggle between plus and minus */}
                        </button>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GenomeResultsTable;
