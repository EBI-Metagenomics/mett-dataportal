import React, {useState} from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-app';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {GeneMeta} from '../../../../interfaces/Gene';
import {ZOOM_LEVELS} from '../../../../utils/appConstants';
import {GENE_TABLE_COLUMNS} from "@components/organisms/Gene/GeneResultsHandler/GeneTableColumns";
import Pagination from '@components/molecules/Pagination';

type ViewModel = ReturnType<typeof createViewState>;

interface GeneResultsTableProps {
    results: GeneMeta[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    linkData: LinkData;
    viewState?: ViewModel;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    isTypeStrainAvailable: boolean;
    page: number;
    pageSize: number;
    totalHits: number;
    onPageChange: (page: number) => void;
}

const GeneResultsTable: React.FC<GeneResultsTableProps> = ({
    results,
    onSortClick,
    linkData,
    viewState,
    setLoading,
    isTypeStrainAvailable,
    page,
    pageSize,
    totalHits,
    onPageChange,
}) => {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const availableColumns = GENE_TABLE_COLUMNS.filter(col =>
        isTypeStrainAvailable || !col.onlyForTypeStrain
    ).filter(col => col.defaultVisible !== false);

    const handleSort = (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        onSortClick(field, newSortOrder);
    };

    const totalPages = Math.ceil(totalHits / pageSize);
    const hasPrevious = page > 1;
    const hasNext = page < totalPages;

    return (
        <section>
            <table className="vf-table vf-table--sortable">
                <thead className="vf-table__header">
                <tr className="vf-table__row">
                    {availableColumns.map(col => (
                        <th
                            key={col.key}
                            onClick={() => col.sortable && handleSort(col.key)}
                            className={`vf-table__heading ${styles.vfTableHeading} ${col.sortable ? styles.clickableHeader : ''}`}
                        >
                            {col.label}
                            {sortField === col.key ? (
                                <span
                                    className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                                    style={{paddingLeft: '5px'}}/>
                            ) : col.sortable ? (
                                <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}/>
                            ) : null}
                        </th>
                    ))}
                    <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
                </tr>
                </thead>
                <tbody className="vf-table__body">
                {results.map((geneMeta, index) => (
                    <tr key={index} className={`vf-table__row ${styles.vfTableRow}`}>
                        {availableColumns.map(col => (
                            <td key={col.key} className={`vf-table__cell ${styles.vfTableCell}`}>
                                {col.render(geneMeta)}
                            </td>
                        ))}
                        <td className={`vf-table__cell ${styles.vfTableCell}`}>
                            {viewState ? (
                                <a
                                    href="#"
                                    className="vf-link"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const view = viewState.session.views[0];
                                        const locationString = `${geneMeta.seq_id}:${geneMeta.start_position || 0}..${geneMeta.end_position || 1000}`;
                                        view.navToLocString(locationString);
                                        setTimeout(() => {
                                            view.zoomTo(ZOOM_LEVELS.NAV);
                                            setLoading(false);
                                        }, 200);
                                    }}
                                >
                                    {linkData.alias}
                                </a>
                            ) : (
                                <a href={linkData.template.replace('${strain_name}', geneMeta.isolate_name)} target="_blank" rel="noreferrer">
                                    {linkData.alias}
                                    <span className={`icon icon-common icon-external-link-alt ${styles.externalIcon}`}
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            )}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
            {totalHits > 0 && (
                <div className={styles.paginationContainer}>
                    <Pagination
                        currentPage={page}
                        totalPages={totalPages}
                        hasPrevious={hasPrevious}
                        hasNext={hasNext}
                        onPageClick={onPageChange}
                    />
                </div>
            )}
        </section>
    );
};

export default GeneResultsTable;
