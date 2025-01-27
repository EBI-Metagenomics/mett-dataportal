import React, {useEffect, useState} from 'react';
import styles from './GenomeResultsTable.module.scss';
import {LinkData} from "../../../../interfaces/Auxiliary";
import {BaseGenome} from "../../../../interfaces/Genome";

interface GenomeResultsTableProps {
    results: any[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    selectedGenomes: BaseGenome[];
    onToggleGenomeSelect: (genome: BaseGenome) => void;
    linkData: LinkData;
}

const GenomeResultsTable: React.FC<GenomeResultsTableProps> = ({
                                                                   results,
                                                                   onSortClick,
                                                                   selectedGenomes,
                                                                   onToggleGenomeSelect,
                                                                   linkData
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

    const generateLink = (template: string, result: any) => {
        return template
            .replace('${strain_name}', result.isolate_name)
    };

    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th onClick={() => handleSort('species')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
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
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Strain
                    {sortField === 'isolate_name' ? (
                        <span
                            className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                            style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`}>Assembly</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`}>Annotations</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`}>Actions</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`}>Add to Gene Search</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((result, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}><i>{result.species.scientific_name || 'Unknown Species'}</i>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.isolate_name || 'Unknown Isolate'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={result.fasta_url || '#'} target="_blank"
                           rel="noreferrer">{result.assembly_name || 'Unknown Assembly'}<span
                            className="icon icon-common icon-download"
                            style={{paddingLeft: '5px'}}></span></a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={result.gff_url || '#'} target="_blank" rel="noreferrer">GFF<span
                            className="icon icon-common icon-download"
                            style={{paddingLeft: '5px'}}></span></a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <a href={generateLink(linkData.template, result)}>{linkData.alias}</a>
                    </td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        <button
                            className={styles.toggleButton}
                            onClick={() => onToggleGenomeSelect({
                                id: result.id,
                                isolate_name: result.isolate_name,
                                type_strain: result.type_strain
                            })}
                            style={{
                                cursor: "pointer",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                padding: "8px",
                                fontSize: "16px",
                                border: "none",
                                background: "transparent",
                            }}
                        >
                            <i
                                className={`icon icon-common ${
                                    selectedGenomes.some(genome => genome.id === result.id)
                                        ? "icon-minus-circle"
                                        : "icon-plus-circle"
                                }`}
                                style={{
                                    color: selectedGenomes.some(genome => genome.id === result.id)
                                        ? "#B0B0B0"
                                        : "#007BFF",
                                    fontSize: "18px",
                                }}
                                aria-hidden="true"
                            ></i>
                        </button>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GenomeResultsTable;
