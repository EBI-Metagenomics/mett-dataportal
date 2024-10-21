import React from 'react';
import styles from './GeneResultsTable.module.scss';

interface GenomeResultsTableProps {
    results: any[];
    onSortClick: (sortField: string) => void;
}

const GeneResultsTable: React.FC<GenomeResultsTableProps> = ({
                                                                 results,
                                                                 onSortClick
                                                             }) => {
    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Strain
                    <button
                        className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                        onClick={() => onSortClick('species')}
                    />
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Gene
                    <button
                        className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                        onClick={() => onSortClick('isolate_name')}
                    />
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Description</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Locus Tag</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((result, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.strain || 'Unknown Strain'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.gene_name || 'Unknown Gene Name'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.description || 'Unknown Description'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.locus_tag || 'Unknown Locus Tag'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={`/gene-viewer/gene/${result.id}/?speciesId=${result.species_id}&genomeId=${result.strain_id}`}>Browse</a>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GeneResultsTable;
