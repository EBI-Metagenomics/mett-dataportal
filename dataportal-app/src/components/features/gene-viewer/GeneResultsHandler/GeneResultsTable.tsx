import React, {useEffect, useState} from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-app2';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {GeneMeta} from '../../../../interfaces/Gene';
import {TABLE_MAX_COLUMNS, ZOOM_LEVELS} from '../../../../utils/common';
import {GENE_TABLE_COLUMNS} from "./GeneTableColumns";
import {GeneService} from '../../../../services/gene';
import * as Dialog from '@radix-ui/react-dialog';
import {useViewportSyncStore} from '../../../../stores/viewportSyncStore';
import {VIEWPORT_SYNC_CONSTANTS} from '../../../../utils/gene-viewer';

// Inject CSS variables for highlight colors
if (typeof document !== 'undefined') {
  const styleId = 'gene-highlight-styles';
  if (!document.getElementById(styleId)) {
    const styleElement = document.createElement('style');
    styleElement.id = styleId;
    styleElement.textContent = `
      :root {
        --gene-highlight-background: ${VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_BACKGROUND};
        --gene-highlight-border: ${VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_BORDER};
        --gene-highlight-background-hover: ${VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_BACKGROUND_HOVER};
      }
    `;
    document.head.appendChild(styleElement);
  }
}

// Extend Window interface for selectedGeneId
declare global {
    interface Window {
        selectedGeneId?: string;
    }
}

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
    sortField?: string;
    sortOrder?: 'asc' | 'desc';
    onFeatureSelect?: (feature: any) => void;    
    geneMeta?: GeneMeta;
    highlightedLocusTag?: string;
    tableSource?: 'sync-table' | 'search-table'; // Identify which table this is
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
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    locusTag?: string,
    onFeatureSelect?: (feature: any) => void,
    geneMeta?: GeneMeta,
    tableSource?: 'sync-table' | 'search-table'
) => {
    // For sync table: only highlight the gene, don't navigate (prevents auto-scrolling and refresh)
    if (tableSource === 'sync-table') {
        // Set changeSource to prevent viewport sync from processing any changes
        // (track reload might trigger viewport changes)
        useViewportSyncStore.getState().setChangeSource('sync-table');
        useViewportSyncStore.getState().setSelectedLocusTag(locusTag || null);
        
        if (locusTag) {
            window.selectedGeneId = locusTag;
        }
        
        // Update feature panel
        if (onFeatureSelect && locusTag && geneMeta) {
            Promise.all([
                Promise.resolve(geneMeta),
                GeneService.fetchGeneProteinSeq(locusTag).catch(() => ({ protein_sequence: '' }))
            ])
            .then(([geneData, proteinData]) => {
                const completeData = {
                    ...geneData,
                    protein_sequence: proteinData.protein_sequence || ''
                };
                onFeatureSelect(completeData);
            })
            .catch(() => {
                onFeatureSelect(geneMeta);
            });
        }
        
        // Force JBrowse to re-render tracks to apply highlighting
        if (viewState?.session?.views?.[0]?.tracks) {
            setTimeout(() => {
                viewState.session.views[0].tracks.forEach((track: any) => {
                    if (track.displays) {
                        track.displays.forEach((display: any) => {
                            try {
                                if (display.reload) {
                                    display.reload();
                                } else if (display.setError) {
                                    display.setError(undefined);
                                }
                            } catch {
                                // Ignore display errors
                            }
                        });
                    }
                });
            }, 100);
        }
        
        // Reset changeSource after enough time to prevent viewport sync from processing any changes
        // Track reload might trigger viewport changes, so we need to block sync updates for a bit
        setTimeout(() => {
            useViewportSyncStore.getState().setChangeSource(null);
        }, 2000); // 2 seconds should be enough to prevent any viewport changes from triggering refresh
        
        return;
    }
    
    // For search table: navigate and zoom to bring gene into view
    const view = viewState?.session?.views?.[0];
    if (view && typeof view.navToLocString === 'function') {
        setLoading(true);
        try {
            const navigationTime = Date.now();
            useViewportSyncStore.getState().setLastTableNavigationTime(navigationTime);
            
            const changeSource = tableSource || 'search-table';
            useViewportSyncStore.getState().setChangeSource(changeSource);
            useViewportSyncStore.getState().setSelectedLocusTag(locusTag || null);
            
            if (locusTag) {
                window.selectedGeneId = locusTag;
            }
            
            view.navToLocString(`${contig}:${start}..${end}`);
            
            setTimeout(() => {
                view.zoomTo(ZOOM_LEVELS.NAV);
                setLoading(false);
                
                setTimeout(() => {
                    const currentNavTime = useViewportSyncStore.getState().lastTableNavigationTime;
                    if (currentNavTime === navigationTime) {
                        useViewportSyncStore.getState().setChangeSource(null);
                        useViewportSyncStore.getState().setLastTableNavigationTime(null);
                    }
                }, VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS);
                
                // Force JBrowse to re-render tracks to apply highlighting
                if (viewState?.session?.views?.[0]?.tracks) {
                    viewState.session.views[0].tracks.forEach((track: any) => {
                        if (track.displays) {
                            track.displays.forEach((display: any) => {
                                try {
                                    if (display.reload) {
                                        display.reload();
                                    } else if (display.setError) {
                                        display.setError(undefined);
                                    }
                                } catch {
                                    // Ignore display errors
                                }
                            });
                        }
                    });
                }
                
                // Update feature panel with gene data
                if (onFeatureSelect && locusTag && geneMeta) {
                    Promise.all([
                        Promise.resolve(geneMeta),
                        GeneService.fetchGeneProteinSeq(locusTag).catch(() => ({ protein_sequence: '' }))
                    ])
                    .then(([geneData, proteinData]) => {
                        const completeData = {
                            ...geneData,
                            protein_sequence: proteinData.protein_sequence || ''
                        };
                        onFeatureSelect(completeData);
                    })
                    .catch(() => {
                        onFeatureSelect(geneMeta);
                    });
                }
            }, 200);

            // Close the feature panel if open (JBrowse's default drawer)
            if (viewState?.session?.widgets?.has('baseFeature')) {
                const w = viewState.session.activeWidgets.get('baseFeature')
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
                                                               sortField: propSortField,
                                                               sortOrder: propSortOrder,
                                                               onFeatureSelect,
                                                               highlightedLocusTag,
                                                               tableSource,
                                                           }) => {
    // Use props if provided, otherwise fall back to local state
    const [localSortField, setLocalSortField] = useState<string | null>(null);
    const [localSortOrder, setLocalSortOrder] = useState<'asc' | 'desc'>('asc');
    const [selectedRow, setSelectedRow] = useState<string | null>(null);
    
    // Use highlightedLocusTag from props if provided, otherwise use local selectedRow
    const effectiveHighlightedLocusTag = highlightedLocusTag || selectedRow
    
    const sortField = propSortField || localSortField;
    const sortOrder = propSortOrder || localSortOrder;

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
        
        // Only update local state if props are not provided
        if (!propSortField) {
            setLocalSortField(field);
        }
        if (!propSortOrder) {
            setLocalSortOrder(newSortOrder);
        }
        
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

            <table className={`vf-table ${tableSource !== 'sync-table' ? 'vf-table--sortable' : ''}`}>
                <thead className="vf-table__header">
                <tr className="vf-table__row">
                    {availableColumns.filter(col => visibleColumns.includes(col.key)).map(col => (
                        <th
                            key={col.key}
                            onClick={() => col.sortable && handleSort(col.key)}
                            className={`vf-table__heading ${styles.vfTableHeading} ${col.sortable && tableSource !== 'sync-table' ? styles.clickableHeader : ''}`}
                        >
                            {col.label}
                            {/* Hide sorting icons in Genomic Context view (sync-table) */}
                            {tableSource !== 'sync-table' && (
                                <>
                                    {sortField === col.key ? (
                                        <span
                                            className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                                            style={{paddingLeft: '5px'}}/>
                                    ) : col.sortable ? (
                                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}/>
                                    ) : null}
                                </>
                            )}
                        </th>
                    ))}
                    <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
                </tr>
                </thead>
                <tbody className="vf-table__body">
                {results.map((geneMeta, index) => (
                    <tr 
                        key={index} 
                        className={`vf-table__row ${styles.vfTableRow} ${effectiveHighlightedLocusTag === geneMeta.locus_tag ? styles.selectedRow : ''}`}
                        onClick={() => setSelectedRow(geneMeta.locus_tag || null)}
                        style={{ cursor: 'pointer' }}
                    >
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
                                            setLoading,
                                            geneMeta.locus_tag,
                                            onFeatureSelect,
                                            geneMeta,
                                            tableSource // Pass table source to identify which table initiated navigation
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
