import React, {useState, useEffect, useMemo} from 'react';
import styles from './FeaturePanel.module.scss';
import {PyhmmerFeaturePanel} from '../../pyhmmer/feature-panel/PyhmmerFeaturePanel';
import {generateExternalDbLink, getIconForEssentiality, getBacinteractomeUniprotUrl} from '../../../../utils/common/geneUtils';
import {useViewportSyncStore} from '../../../../stores/viewportSyncStore';
import {createViewState} from '@jbrowse/react-app2';
import {ZOOM_LEVELS} from '../../../../utils/common/constants';
import {VIEWPORT_SYNC_CONSTANTS} from '../../../../utils/gene-viewer';

type ViewModel = ReturnType<typeof createViewState>;

interface FeaturePanelProps {
    feature: any | null;
    onClose?: () => void;
    viewState?: ViewModel;
    setLoading?: React.Dispatch<React.SetStateAction<boolean>>;
    activeTab?: 'search' | 'sync';
}

const FeaturePanel: React.FC<FeaturePanelProps> = ({ feature, onClose, viewState, setLoading, activeTab }) => {
    // Must call hooks before any early returns
    const [showPyhmmer, setShowPyhmmer] = useState(false);
    const { selectedLocusTag, seqId: viewportSeqId, start: viewportStart, end: viewportEnd } = useViewportSyncStore();
    
    // Extract feature data - handle GeneMeta API response structure (must be before early return)
    const getFeatureData = (featureData: any) => {
        if (!featureData) {
            return {
                locusTag: 'N/A',
                gene: '',
                product: 'N/A',
                alias: [],
                start: 0,
                end: 0,
                strand: 0,
                seqId: 'N/A',
                essentiality: '',
                uniprotId: '',
                pfam: [],
                interpro: [],
                kegg: [],
                cog: [],
                cogCategories: [],
                dbxref: null,
                inference: '',
                productSource: '',
                eggnog: '',
                ontologyTerms: [],
                ecNumber: '',
                ufKeyword: [],
                ufOntologyTerms: [],
                ufGeneName: '',
                ufProtRecFullname: '',
                proteinSequence: '',
                isolateName: '',
                speciesName: '',
            };
        }
        
        // The feature comes from GeneService API which returns GeneMeta structure
        const data = featureData?.data || featureData;
        
        
        return {
            // Basic info - GeneMeta uses gene_name, not gene
            locusTag: data?.locus_tag || 'N/A',
            gene: data?.gene_name || data?.gene || '',
            product: data?.product || 'N/A',
            alias: Array.isArray(data?.alias) ? data.alias : (data?.alias ? [data.alias] : []),
            
            // Location info - GeneMeta uses start_position/end_position
            start: data?.start_position || data?.start || 0,
            end: data?.end_position || data?.end || 0,
            strand: data?.strand || 0,
            seqId: data?.seq_id || 'N/A',
            
            // Annotation info
            essentiality: data?.essentiality || '',
            uniprotId: data?.uniprot_id || '',
            
            // Arrays - keep as arrays for link generation
            pfam: Array.isArray(data?.pfam) ? data.pfam : (data?.pfam ? [data.pfam] : []),
            interpro: Array.isArray(data?.interpro) ? data.interpro : (data?.interpro ? [data.interpro] : []),
            kegg: Array.isArray(data?.kegg) ? data.kegg : (data?.kegg ? [data.kegg] : []),
            cog: Array.isArray(data?.cog_id) ? data.cog_id : (data?.cog_id ? [data.cog_id] : []),
            cogCategories: Array.isArray(data?.cog_funcats) ? data.cog_funcats : (data?.cog_funcats ? [data.cog_funcats] : []),
            
            // AMR info
            amr: data?.amr || null,
            hasAmr: data?.has_amr_info || false,
            
            // Additional metadata fields
            dbxref: data?.dbxref || null,
            inference: data?.inference || '',
            productSource: data?.product_source || '',
            eggnog: data?.eggnog || '',
            
            // Ontology terms - handle nested structure from Elasticsearch
            ontologyTerms: Array.isArray(data?.ontology_terms) 
                ? data.ontology_terms 
                : [],
            
            ecNumber: data?.ec_number || '',
            
            // Unifire fields (uf_*) - from UniFire annotation system
            ufKeyword: Array.isArray(data?.uf_keyword) ? data.uf_keyword : [],
            ufOntologyTerms: Array.isArray(data?.uf_ontology_terms) ? data.uf_ontology_terms : [],
            ufGeneName: data?.uf_gene_name || '',
            ufProtRecFullname: data?.uf_prot_rec_fullname || '',
            
            // Other fields
            proteinSequence: data?.protein_sequence || '',
            isolateName: data?.isolate_name || '',
            speciesName: data?.species_scientific_name || '',
        };
    };

    const featureData = getFeatureData(feature);

    // Check if the selected gene is currently visible in the viewport (must be before early return)
    // Gene is "out of view" if it does NOT overlap with the current viewport range
    const isGeneInViewport = useMemo(() => {
        if (!feature || !viewportSeqId || viewportStart === null || viewportEnd === null) {
            return false;
        }
        
        // Check if the gene's sequence ID matches the viewport sequence ID
        if (featureData.seqId !== viewportSeqId) {
            // Different contig/sequence - gene is out of view
            return false;
        }
        
        // Get gene coordinates
        const geneStart = featureData.start;
        const geneEnd = featureData.end;
        
        // Ensure we have valid coordinates
        if (geneStart === null || geneEnd === null || geneStart === undefined || geneEnd === undefined) {
            return false;
        }
        
        // Calculate if gene overlaps with viewport
        // Gene overlaps viewport if:
        // - Gene starts before or at viewport end, AND
        // - Gene ends after or at viewport start
        // Viewport range: [viewportStart, viewportEnd]
        // Gene range: [geneStart, geneEnd]
        const geneOverlapsViewport = geneStart <= viewportEnd && geneEnd >= viewportStart;
        
        return geneOverlapsViewport;
    }, [feature, viewportSeqId, viewportStart, viewportEnd, featureData.seqId, featureData.start, featureData.end]);
    
    // Reset PyHMMER section when feature changes
    useEffect(() => {
        setShowPyhmmer(false);
    }, [feature?.locus_tag, feature?.id]);
    
    if (!feature) {
        return (
            <div className={styles.featurePanel}>
                <div className={styles.emptyState}>
                    <p>Click on a gene feature in the viewer to see details</p>
                </div>
            </div>
        );
    }

    // Function to navigate back to the selected gene
    const handleScrollToGene = () => {
        if (!viewState || !featureData.seqId) return;
        
        const view = viewState?.session?.views?.[0];
        if (view && typeof view.navToLocString === 'function') {
            if (setLoading) setLoading(true);
            
            try {
                const navigationTime = Date.now();
                const start = Math.max(0, featureData.start - 500); // Add some padding
                const end = featureData.end + 500;
                
                // Set change source and navigation time to prevent viewport sync from interfering
                useViewportSyncStore.getState().setChangeSource('search-table');
                useViewportSyncStore.getState().setLastTableNavigationTime(navigationTime);
                useViewportSyncStore.getState().setSelectedLocusTag(featureData.locusTag || null);
                
                if (featureData.locusTag) {
                    window.selectedGeneId = featureData.locusTag;
                }
                
                view.navToLocString(`${featureData.seqId}:${start}..${end}`);
                
                setTimeout(() => {
                    view.zoomTo(ZOOM_LEVELS.NAV);
                    
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
                    
                    // Wait a bit longer for JBrowse to finish navigation, then read actual viewport
                    // This ensures the button disappears and sync view refreshes if active
                    // We need to wait long enough for RECENT_BLOCK_WINDOW_MS (1000ms) to pass
                    // after we set changeSource to 'search-table', so the sync view can refresh
                    setTimeout(() => {
                        // Read actual viewport coordinates from JBrowse (similar to useJBrowseViewportSync)
                        try {
                            const displayedRegions = view.displayedRegions
                            if (displayedRegions && displayedRegions.length > 0) {
                                const region = displayedRegions[0]
                                const refName = region.refName
                                const regionStart = region.start
                                const regionEnd = region.end
                                
                                // Get viewport dimensions from JBrowse (same logic as useJBrowseViewportSync)
                                const bpPerPx = view.bpPerPx || view.volatile?.bpPerPx || 1
                                
                                let width = VIEWPORT_SYNC_CONSTANTS.DEFAULT_VIEWPORT_WIDTH_PX
                                if (view.width !== undefined) {
                                    width = view.width
                                } else if (view.volatile?.width !== undefined) {
                                    width = view.volatile.width
                                } else if (view.pxToBp && view.bpToPx) {
                                    try {
                                        const testBp = VIEWPORT_SYNC_CONSTANTS.TEST_BP_FOR_WIDTH_ESTIMATION
                                        const testPx = view.bpToPx(testBp)
                                        if (testPx > 0) {
                                            const regionLength = regionEnd - regionStart
                                            width = Math.floor((regionLength / testBp) * testPx)
                                        }
                                    } catch {
                                        // Use default width
                                    }
                                }
                                
                                let offsetPx = 0
                                if (view.offsetPx !== undefined) {
                                    offsetPx = view.offsetPx
                                } else if (view.volatile?.offsetPx !== undefined) {
                                    offsetPx = view.volatile.offsetPx
                                } else if (typeof view.getOffsetPx === 'function') {
                                    try {
                                        offsetPx = view.getOffsetPx() || 0
                                    } catch {
                                        // Use default
                                    }
                                }
                                
                                // Calculate actual visible viewport using pxToBp/bpToPx if available (more accurate)
                                let viewportStart = regionStart
                                let viewportEnd = regionEnd
                                
                                if (typeof view.bpToPx === 'function' && typeof view.pxToBp === 'function') {
                                    try {
                                        const startBp = view.pxToBp(0)
                                        const endBp = view.pxToBp(width)
                                        
                                        if (startBp !== undefined && endBp !== undefined && startBp < endBp) {
                                            viewportStart = Math.max(regionStart, Math.floor(startBp))
                                            viewportEnd = Math.min(regionEnd, Math.floor(endBp))
                                        } else if (bpPerPx && bpPerPx > 0 && width > 0) {
                                            const offsetBp = offsetPx * bpPerPx
                                            const widthBp = width * bpPerPx
                                            viewportStart = Math.max(regionStart, Math.floor(regionStart + offsetBp))
                                            viewportEnd = Math.min(regionEnd, Math.floor(viewportStart + widthBp))
                                        }
                                    } catch {
                                        if (bpPerPx && bpPerPx > 0 && width > 0) {
                                            const offsetBp = offsetPx * bpPerPx
                                            const widthBp = width * bpPerPx
                                            viewportStart = Math.max(regionStart, Math.floor(regionStart + offsetBp))
                                            viewportEnd = Math.min(regionEnd, Math.floor(viewportStart + widthBp))
                                        }
                                    }
                                } else if (bpPerPx && bpPerPx > 0 && width > 0) {
                                    const offsetBp = offsetPx * bpPerPx
                                    const widthBp = width * bpPerPx
                                    viewportStart = Math.max(regionStart, Math.floor(regionStart + offsetBp))
                                    viewportEnd = Math.min(regionEnd, Math.floor(viewportStart + widthBp))
                                }
                                
                                if (viewportStart > viewportEnd) {
                                    [viewportStart, viewportEnd] = [viewportEnd, viewportStart]
                                }
                                
                                // Ensure minimum viewport size
                                if (viewportEnd - viewportStart < VIEWPORT_SYNC_CONSTANTS.MIN_VIEWPORT_SIZE_BP) {
                                    const center = Math.floor((viewportStart + viewportEnd) / 2)
                                    const halfSize = VIEWPORT_SYNC_CONSTANTS.MIN_VIEWPORT_SIZE_BP / 2
                                    viewportStart = Math.max(regionStart, center - halfSize)
                                    viewportEnd = Math.min(regionEnd, center + halfSize)
                                }
                                
                                // Reset change source and navigation time to allow sync view to refresh
                                useViewportSyncStore.getState().setChangeSource(null);
                                useViewportSyncStore.getState().setLastTableNavigationTime(null);
                                
                                // Update viewport in store with actual JBrowse coordinates - this will:
                                // 1. Trigger sync view refresh if active (changeSource will be 'jbrowse')
                                // 2. Cause isGeneInViewport to re-evaluate (button will disappear when gene is in view)
                                useViewportSyncStore.getState().setViewport(
                                    refName,
                                    viewportStart,
                                    viewportEnd,
                                    'jbrowse'
                                );
                                
                                if (setLoading) setLoading(false);
                            } else {
                                // Fallback: use gene coordinates with padding if we can't read viewport
                                useViewportSyncStore.getState().setChangeSource(null);
                                useViewportSyncStore.getState().setLastTableNavigationTime(null);
                                useViewportSyncStore.getState().setViewport(
                                    featureData.seqId,
                                    start,
                                    end,
                                    'jbrowse'
                                );
                                if (setLoading) setLoading(false);
                            }
                        } catch {
                            // Fallback: use gene coordinates with padding if reading viewport fails
                            useViewportSyncStore.getState().setChangeSource(null);
                            useViewportSyncStore.getState().setLastTableNavigationTime(null);
                            useViewportSyncStore.getState().setViewport(
                                featureData.seqId,
                                start,
                                end,
                                'jbrowse'
                            );
                            if (setLoading) setLoading(false);
                        }
                    }, 1200); // Wait 1200ms to ensure RECENT_BLOCK_WINDOW_MS (1000ms) has passed and JBrowse has finished navigation
                }, 200);
            } catch (error) {
                console.error('Error navigating to gene:', error);
                if (setLoading) setLoading(false);
            }
        }
    };

    // Helper to generate external link
    const renderExternalLink = (database: 'PFAM' | 'INTERPRO' | 'KEGG' | 'COG' | 'COG_CATEGORY' | 'GO' | 'UNIPROT', id: string, label?: string) => {
        // Use special URL generator for UniProt that links to Bacinteractome
        const url = database === 'UNIPROT' 
            ? getBacinteractomeUniprotUrl(id, featureData.speciesName)
            : generateExternalDbLink(database, id);
        return (
            <a href={url} target="_blank" rel="noopener noreferrer" className={styles.externalLink}>
                {label || id}
            </a>
        );
    };

    // Helper to render array of IDs with links
    const renderExternalLinks = (database: 'PFAM' | 'INTERPRO' | 'KEGG' | 'COG' | 'COG_CATEGORY' | 'GO' | 'UNIPROT', ids: string[]) => {
        if (!ids || ids.length === 0) return null;
        
        return (
            <div className={styles.linkList}>
                {ids.map((id, idx) => (
                    <span key={idx}>
                        {renderExternalLink(database, id)}
                        {idx < ids.length - 1 && ', '}
                    </span>
                ))}
            </div>
        );
    };

    return (
        <div className={styles.featurePanel}>
            <div className={styles.header}>
                <h3>Feature Details</h3>
                {onClose && (
                    <button className={styles.closeButton} onClick={onClose}>
                        ×
                    </button>
                )}
            </div>

            {/* Show navigation button if gene is not in viewport */}
            {!isGeneInViewport && viewState && (
                <div className={styles.navigationBanner}>
                    <button 
                        className={styles.scrollToGeneButton}
                        onClick={handleScrollToGene}
                        title="Scroll JBrowse viewer to show this gene"
                    >
                        <span className={styles.scrollToGeneIcon}>📍</span>
                        <span>Scroll back to selected gene</span>
                    </button>
                </div>
            )}

            <div className={styles.content}>
                {/* Core Details Section */}
                <div className={styles.section}>
                    <h4>Core Details</h4>
                    <div className={styles.field}>
                        <label>Locus Tag:</label>
                        <span 
                            className={selectedLocusTag === featureData.locusTag ? styles.highlightedLocusTag : ''}
                        >
                            {featureData.locusTag}
                        </span>
                    </div>
                    {featureData.gene && (
                        <div className={styles.field}>
                            <label>Name:</label>
                            <span>{featureData.gene}</span>
                        </div>
                    )}
                    {featureData.alias && featureData.alias.length > 0 && (
                        <div className={styles.field}>
                            <label>Alias:</label>
                            <span>{featureData.alias.join(', ')}</span>
                        </div>
                    )}
                    {featureData.uniprotId && (
                        <div className={styles.field}>
                            <label>UniProt ID:</label>
                            {renderExternalLink('UNIPROT', featureData.uniprotId)}
                        </div>
                    )}
                    <div className={styles.field}>
                        <label>Product:</label>
                        <span>{featureData.product}</span>
                    </div>
                    {featureData.productSource && (
                        <div className={styles.field}>
                            <label>Product Source:</label>
                            <span>{featureData.productSource}</span>
                        </div>
                    )}
                    {featureData.inference && (
                        <div className={styles.field}>
                            <label>Inference:</label>
                            <span>{featureData.inference}</span>
                        </div>
                    )}
                </div>

                <div className={styles.section}>
                    <h4>Location</h4>
                    <div className={styles.field}>
                        <label>Sequence ID:</label>
                        <span>{featureData.seqId}</span>
                    </div>
                    <div className={styles.field}>
                        <label>Position:</label>
                        <span>{featureData.start.toLocaleString()} - {featureData.end.toLocaleString()}</span>
                    </div>
                    <div className={styles.field}>
                        <label>Strand:</label>
                        <span>{featureData.strand > 0 ? 'Forward (+)' : 'Reverse (-)'}</span>
                    </div>
                </div>

                {/* Annotations Section */}
                {(featureData.essentiality || featureData.pfam.length > 0 || featureData.interpro.length > 0 || 
                  featureData.kegg.length > 0 || featureData.cog.length > 0 || featureData.cogCategories.length > 0 ||
                  featureData.eggnog) && (
                    <div className={styles.section}>
                        <h4>Annotations</h4>
                        {featureData.essentiality && (
                            <div className={styles.field}>
                                <label>Essentiality Status:</label>
                                <span className={styles.essentiality}>
                                    {getIconForEssentiality(featureData.essentiality)} {featureData.essentiality}
                                </span>
                            </div>
                        )}
                        {featureData.pfam.length > 0 && (
                            <div className={styles.field}>
                                <label>PFAM:</label>
                                {renderExternalLinks('PFAM', featureData.pfam)}
                            </div>
                        )}
                        {featureData.interpro.length > 0 && (
                            <div className={styles.field}>
                                <label>InterPro:</label>
                                {renderExternalLinks('INTERPRO', featureData.interpro)}
                            </div>
                        )}
                        {featureData.kegg.length > 0 && (
                            <div className={styles.field}>
                                <label>KEGG:</label>
                                {renderExternalLinks('KEGG', featureData.kegg.map((k: string) => k.replace('ko:', '')))}
                            </div>
                        )}
                        {featureData.cog.length > 0 && (
                            <div className={styles.field}>
                                <label>COG ID:</label>
                                {renderExternalLinks('COG', featureData.cog)}
                            </div>
                        )}
                        {featureData.cogCategories.length > 0 && (
                            <div className={styles.field}>
                                <label>COG Categories:</label>
                                {renderExternalLinks('COG_CATEGORY', featureData.cogCategories)}
                            </div>
                        )}
                        {featureData.eggnog && (
                            <div className={styles.field}>
                                <label>eggNOG:</label>
                                <span>{featureData.eggnog}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Ontology Terms Section */}
                {featureData.ontologyTerms && featureData.ontologyTerms.length > 0 && (
                    <div className={styles.section}>
                        <h4>Ontology Terms</h4>
                        <div className={styles.field}>
                            <label>GO Terms:</label>
                            <div className={styles.linkList}>
                                {featureData.ontologyTerms.slice(0, 10).map((term: any, idx: number) => {
                                    const ontologyId = term.ontology_id || '';
                                    // const goMatch = ontologyId.match(/GO:(\d+)/);
                                    return (
                                        <span key={idx}>
                                            {/*{goMatch ? (*/}
                                            {/*    renderExternalLink('GO', goMatch[1], ontologyId)*/}
                                            {/*) : (*/}
                                                <span title={term.ontology_description}>{ontologyId}</span>
                                            {/*)}*/}
                                            {idx < Math.min(featureData.ontologyTerms.length - 1, 9) && ', '}
                                        </span>
                                    );
                                })}
                                {featureData.ontologyTerms.length > 10 && (
                                    <span>... and {featureData.ontologyTerms.length - 10} more</span>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* UniFire Annotations Section */}
                {(featureData.ufProtRecFullname || featureData.ufOntologyTerms.length > 0) && (
                    <div className={styles.section}>
                        <h4>UniFire Annotations</h4>
                        {featureData.ufProtRecFullname && (
                            <div className={styles.field}>
                                <label>Protein Name:</label>
                                <span>{featureData.ufProtRecFullname}</span>
                            </div>
                        )}
                        {featureData.ufOntologyTerms.length > 0 && (
                            <div className={styles.field}>
                                <label>Ontology:</label>
                                <span>{featureData.ufOntologyTerms.join(', ')}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Database Cross-References Section */}
                {featureData.dbxref && Array.isArray(featureData.dbxref) && featureData.dbxref.length > 0 && (
                    <div className={styles.section}>
                        <h4>Database Cross-References</h4>
                        <div className={styles.field}>
                            {featureData.dbxref.map((ref: any, idx: number) => (
                                <div key={idx} className={styles.dbxrefItem}>
                                    <strong>{ref.db}:</strong> {ref.ref}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Protein Sequence Section */}
                {featureData.proteinSequence && (
                    <div className={styles.section}>
                        <h4>Protein Sequence</h4>
                        <div className={styles.sequenceContainer}>
                            <pre className={styles.sequence}>
                                {featureData.proteinSequence}
                            </pre>
                        </div>
                        
                        {/* PyHMMER Search Integration */}
                        <div className={styles.pyhmmerSection}>
                            {!showPyhmmer ? (
                                <button
                                    className={styles.pyhmmerButton}
                                    onClick={() => setShowPyhmmer(true)}
                                >
                                    🔍 Search Similar Proteins
                                </button>
                            ) : (
                                <div className={styles.pyhmmerContainer}>
                                    <PyhmmerFeaturePanel 
                                        proteinSequence={featureData.proteinSequence}
                                        isolateName={featureData.locusTag}
                                        product={featureData.product}
                                        onClearResults={() => setShowPyhmmer(false)}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FeaturePanel;

