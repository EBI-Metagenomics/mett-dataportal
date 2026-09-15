import React from 'react';
import {GenomeMeta} from '../../../../../interfaces/Genome';
import GeneViewerLegends from '@components/molecules/GeneViewerLegends';
import Breadcrumb from '@components/molecules/Breadcrumb';
import ReleaseHistoryLink from '@components/molecules/ReleaseHistoryLink';
import {RELEASE_SELECTOR_ENABLED} from '../../../../../config/featureFlags';
import styles from './GeneViewerHeader.module.scss';

interface GeneViewerHeaderProps {
    genomeMeta: GenomeMeta | null;
}

const pipelineLabel = (genomeMeta: GenomeMeta): string | null => {
    const annotation = genomeMeta.annotation;
    if (!annotation) {
        return null;
    }
    const parts = [annotation.pipeline, annotation.pipeline_version].filter(Boolean);
    return parts.length ? parts.join(' ') : null;
};

const GeneViewerHeader: React.FC<GeneViewerHeaderProps> = ({genomeMeta}) => {
    const pipeline = genomeMeta ? pipelineLabel(genomeMeta) : null;
    const processingUrl = genomeMeta?.annotation?.processing_document_url;
    const processingRef = genomeMeta?.annotation?.processing_reference;

    return (
        <div className={styles.geneViewerHeader}>
            <Breadcrumb currentPage="genome-view" />

            <section className={styles.infoSection}>
                <div className={styles.infoGrid}>
                    <div className={styles.leftPane}>
                        {genomeMeta ? (
                            <div className="genome-meta-info">
                                <h2><i>{genomeMeta.species_scientific_name}</i>: {genomeMeta.isolate_name}</h2>
                                <p><strong>Assembly Name:&nbsp;</strong>
                                    <a href={genomeMeta.fasta_url} target="_blank" rel="noopener noreferrer">
                                        {genomeMeta.assembly_name}
                                        <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                                              style={{paddingLeft: '5px'}}></span>
                                    </a>
                                </p>
                                <p><strong>Annotations:&nbsp;</strong>
                                    <a href={genomeMeta.gff_url} target="_blank" rel="noopener noreferrer">
                                        {genomeMeta.gff_file}
                                        <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                                              style={{paddingLeft: '5px'}}></span>
                                    </a>
                                </p>
                                {pipeline && (
                                    <p><strong>Annotation pipeline:&nbsp;</strong>{pipeline}</p>
                                )}
                                {processingUrl && (
                                    <p><strong>Processing document:&nbsp;</strong>
                                        <a href={processingUrl} target="_blank" rel="noopener noreferrer">
                                            {processingRef || processingUrl}
                                        </a>
                                    </p>
                                )}
                                {RELEASE_SELECTOR_ENABLED && (
                                    <p>
                                        <ReleaseHistoryLink kind="genome" id={genomeMeta.isolate_name} />
                                    </p>
                                )}
                            </div>
                        ) : (
                            <p>Loading genome meta information...</p>
                        )}
                    </div>

                    <div className={styles.rightPane}>
                        {genomeMeta && (
                            <GeneViewerLegends showEssentiality={genomeMeta.type_strain === true}/>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
};

export default GeneViewerHeader;
