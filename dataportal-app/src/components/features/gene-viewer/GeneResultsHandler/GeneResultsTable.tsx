import React, {useEffect, useState} from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-app2';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {GeneMeta} from '../../../../interfaces/Gene';
import {TABLE_MAX_COLUMNS, ZOOM_LEVELS} from '../../../../utils/common';
import {GENE_TABLE_COLUMNS} from "./GeneTableColumns";
import * as Dialog from '@radix-ui/react-dialog';


type ViewModel = ReturnType<typeof createViewState>;

interface GeneResultsTableProps {
    results: GeneMeta[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    linkData: LinkData;
    viewState?: ViewModel;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    isTypeStrainAvailable: boolean;
    onDownloadTSV?: () => void;
    isLoading?: boolean;
}

const generateLink = (template: string, result: any) => {
    return template
        .replace('${strain_name}', result.isolate_name)
        .replace('${locus_tag}', result.locus_tag);
};

const handleNavigation = (
    viewState: ViewModel,
    contig: string,
    start: number,
    end: number,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>
) => {
    const view = viewState?.session?.views?.[0];
    if (view && typeof view.navToLocString === 'function') {
        setLoading(true);
        try {
            view.navToLocString(`${contig}:${start}..${end}`);
            setTimeout(() => {
                view.zoomTo(ZOOM_LEVELS.NAV);
                setLoading(false);
            }, 200);

            // Close the feature panel if open
            // console.log("***widgets: ", viewState.session.widgets)
            if (viewState?.session?.widgets?.has('baseFeature')) {
                const w = viewState.session.activeWidgets.get('baseFeature')
                // console.log("*****##########", w)
                viewState.session.hideWidget(w)
            }

        } catch (error) {
            console.error('Error during navigation:', error);
            setLoading(false);
        }
    } else {
        console.error('navToLocString is not available on the view object');
    }
};

const GeneResultsTable: React.FC<GeneResultsTableProps> = ({
                                                               results,
                                                               onSortClick,
                                                               linkData,
                                                               viewState,
                                                               setLoading,
                                                               isTypeStrainAvailable,
                                                               onDownloadTSV,
                                                               isLoading,
                                                           }) => {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const availableColumns = GENE_TABLE_COLUMNS.filter(col =>
        isTypeStrainAvailable || !col.onlyForTypeStrain
    );
    const [visibleColumns, setVisibleColumns] = useState<string[]>(
        availableColumns
            .filter(col => col.defaultVisible !== false)
            .map(col => col.key)
    );
    
    const [columnLimitError, setColumnLimitError] = useState(false);

    useEffect(() => {
        if (visibleColumns.length < TABLE_MAX_COLUMNS && columnLimitError) {
            setColumnLimitError(false);
        }
    }, [visibleColumns]);

    const handleSort = (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        onSortClick(field, newSortOrder);
    };

    const handleCheckboxToggle = (key: string) => {
        setVisibleColumns(prev => {
            const isCurrentlyVisible = prev.includes(key);
            const next = isCurrentlyVisible
                ? prev.filter(col => col !== key)
                : [...prev, key];

            if (next.length > TABLE_MAX_COLUMNS) {
                setColumnLimitError(true);
                return prev; // ignore update
            }

            setColumnLimitError(false);
            return next;
        });
    };


    return (
        <section>
            <div className={styles.toolbar}>
                {onDownloadTSV && (
                    <button
                        type="button"
                        title="Download TSV"
                        className={`vf-button vf-button--sm vf-button--primary ${styles.vfDownloadBtn}`}
                        onClick={onDownloadTSV}
                        disabled={isLoading}
                    >
                        <span className={`icon icon-common ${isLoading ? 'icon-spinner' : 'icon-download'}`}></span>
                        {isLoading ? ' Downloading...' : ' Download TSV'}
                    </button>
                )}
                <Dialog.Root>
                    <Dialog.Trigger asChild>
                        <button
                            type="button"
                            title="Show/Hide Columns"
                            className={`vf-button vf-button--sm vf-button--secondary ${styles.vfColumnSelectorBtn}`}
                        >
                            <span className="icon icon-common icon-columns"></span>
                        </button>
                    </Dialog.Trigger>

                    <Dialog.Portal>
                        <Dialog.Overlay className={styles.dialogOverlay}/>
                        <Dialog.Content className={styles.dialogContent}>
                            <Dialog.Title className={styles.columnSelectorTitle}>
                                Select Columns to Display
                            </Dialog.Title>
                            <Dialog.Description className={styles.visuallyHidden}></Dialog.Description>
                            <div className={styles.columnSelectorContent}>
                                {columnLimitError && (
                                    <div className={styles.errorText}>
                                        You can select up to {TABLE_MAX_COLUMNS} columns only.
                                    </div>
                                )}
                                {availableColumns.map((col) => (
                                    <label key={col.key} className={styles.checkboxLabel}>
                                        <input
                                            type="checkbox"
                                            checked={visibleColumns.includes(col.key)}
                                            onChange={() => handleCheckboxToggle(col.key)}
                                            // disabled={!visibleColumns.includes(col.key) && visibleColumns.length >= TABLE_MAX_COLUMNS}
                                        />
                                        {col.label}
                                    </label>
                                ))}
                            </div>
                            <Dialog.Close asChild>
                                <button className={styles.closeBtn}>Close</button>
                            </Dialog.Close>
                        </Dialog.Content>
                    </Dialog.Portal>
                </Dialog.Root>


            </div>

            <table className="vf-table vf-table--sortable">
                <thead className="vf-table__header">
                <tr className="vf-table__row">
                    {availableColumns.filter(col => visibleColumns.includes(col.key)).map(col => (
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
                        {GENE_TABLE_COLUMNS.filter(col => visibleColumns.includes(col.key)).map(col => (
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
                                        handleNavigation(
                                            viewState,
                                            geneMeta.seq_id,
                                            geneMeta.start_position ? geneMeta.start_position : 0,
                                            geneMeta.end_position ? geneMeta.end_position : 1000,
                                            setLoading
                                        );
                                    }}
                                >
                                    {linkData.alias}
                                </a>
                            ) : (
                                <a href={generateLink(linkData.template, geneMeta)} target="_blank" rel="noreferrer">
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
        </section>
    );
};

export default GeneResultsTable;
