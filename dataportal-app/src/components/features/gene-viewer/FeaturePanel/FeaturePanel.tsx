import React, {useState, useEffect} from 'react';
import styles from './FeaturePanel.module.scss';
import {PyhmmerFeaturePanel} from '../../pyhmmer/feature-panel/PyhmmerFeaturePanel';
import {generateExternalDbLink, getIconForEssentiality, getBacinteractomeUniprotUrl} from '../../../../utils/common/geneUtils';

interface FeaturePanelProps {
    feature: any | null;
    onClose?: () => void;
}

const FeaturePanel: React.FC<FeaturePanelProps> = ({ feature, onClose }) => {
    // Must call hooks before any early returns
    const [showPyhmmer, setShowPyhmmer] = useState(false);
    
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

    // Extract feature data - handle GeneMeta API response structure
    const getFeatureData = (feature: any) => {
        // The feature comes from GeneService API which returns GeneMeta structure
        const data = feature?.data || feature;
        
        
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

            <div className={styles.content}>
                {/* Core Details Section */}
                <div className={styles.section}>
                    <h4>Core Details</h4>
                    <div className={styles.field}>
                        <label>Locus Tag:</label>
                        <span>{featureData.locusTag}</span>
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

