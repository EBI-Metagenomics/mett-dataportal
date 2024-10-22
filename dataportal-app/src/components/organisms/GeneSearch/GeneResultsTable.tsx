import React from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-linear-genome-view';

type ViewModel = ReturnType<typeof createViewState>;

interface LinkData {
    template: string;
    alias: string;
}

interface GeneResultsTableProps {
    results: any[];
    onSortClick: (sortField: string) => void;
    linkData: LinkData;
    viewState?: ViewModel;
}

const generateLink = (template: string, result: any) => {
    return template
        .replace('${id}', result.id)
        .replace('${strain_id}', result.strain_id);
};

const handleNavigation = (
    viewState: ViewModel,
    contig: string,
    start: number,
    end: number
) => {
    const locString = `${contig}:${start}..${end}`;
    viewState.session.view.navToLocString(locString);
};

const GeneResultsTable: React.FC<GeneResultsTableProps> = ({
                                                               results,
                                                               onSortClick,
                                                               linkData,
                                                               viewState
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
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Product</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Locus Tag</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((result, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.strain || 'Unknown Strain'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.gene_name || 'Unknown Gene Name'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.description || ''}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.locus_tag || 'Unknown Locus Tag'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        {viewState ? (
                            <a
                                href="#"
                                className="vf-link"
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleNavigation(viewState, result.seq_id, result.start_position, result.end_position);
                                }}
                            >
                                {linkData.alias}
                            </a>
                        ) : (
                            <a href={generateLink(linkData.template, result)}>
                                {linkData.alias}
                            </a>
                        )}
                    </td>

                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GeneResultsTable;
