import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {GenomeService} from '../../../../../services/genome';
import {AnnotationRun, GenomeAnnotationsResponse, GenomeMeta} from '../../../../../interfaces/Genome';
import {currentGenomePath, withAnnotationRunParam} from '../../../../../utils/common/annotationContext';
import styles from './GeneViewerHeader.module.scss';
import GeneViewerLegends from '@components/molecules/GeneViewerLegends';
import Breadcrumb from '@components/molecules/Breadcrumb';

interface GeneViewerHeaderProps {
    genomeMeta: GenomeMeta | null;
    annotationRunId?: string | null;
    locusTag?: string | null;
}

const formatDate = (value?: string | null) => {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toISOString().slice(0, 10);
};

const GeneViewerHeader: React.FC<GeneViewerHeaderProps> = ({
    genomeMeta,
    annotationRunId,
    locusTag,
}) => {
    const [annotations, setAnnotations] = useState<GenomeAnnotationsResponse | null>(null);

    useEffect(() => {
        if (!genomeMeta?.isolate_name) {
            setAnnotations(null);
            return;
        }
        let cancelled = false;
        GenomeService.fetchGenomeAnnotations(genomeMeta.isolate_name)
            .then((data) => {
                if (!cancelled) setAnnotations(data);
            })
            .catch(() => {
                if (!cancelled) setAnnotations(null);
            });
        return () => {
            cancelled = true;
        };
    }, [genomeMeta?.isolate_name]);

    const selectedRun: AnnotationRun | null = annotationRunId
        ? annotations?.runs.find((run) => String(run.id) === String(annotationRunId)) || null
        : annotations?.current || null;
    const isArchived = Boolean(selectedRun && !selectedRun.is_current);
    const gffHref = selectedRun?.gff_url || genomeMeta?.gff_url;
    const gffLabel = selectedRun?.gff_file || genomeMeta?.gff_file;
    const previousRuns = annotations?.previous || [];

    return (
        <div className={styles.geneViewerHeader}>
            <Breadcrumb currentPage="genome-view" />

            {isArchived && selectedRun && genomeMeta && (
                <div className={styles.archiveBanner} role="status">
                    <strong>Archived annotation — release {selectedRun.release_label}</strong>
                    <span>This view is read-only and is not the current METT annotation.</span>
                    <Link
                        className={styles.bannerLink}
                        to={currentGenomePath(genomeMeta.isolate_name, locusTag)}
                    >
                        Return to current annotation
                    </Link>
                </div>
            )}

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
                                    <a href={gffHref || '#'} target="_blank" rel="noopener noreferrer">
                                        {gffLabel}
                                        <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                                              style={{paddingLeft: '5px'}}></span>
                                    </a>
                                </p>
                                <p>
                                    <strong>Annotation release:&nbsp;</strong>
                                    {selectedRun?.release_label
                                        || genomeMeta.current_annotation_release
                                        || '—'}
                                    {isArchived ? ' (archived)' : ''}
                                </p>
                                {(selectedRun?.mettannotator_version || genomeMeta.mettannotator_version) && (
                                    <p>
                                        <strong>METTAnnotator:&nbsp;</strong>
                                        {selectedRun?.mettannotator_version || genomeMeta.mettannotator_version}
                                    </p>
                                )}
                                {(selectedRun?.pipeline_version || genomeMeta.pipeline_version) && (
                                    <p>
                                        <strong>Pipeline:&nbsp;</strong>
                                        {selectedRun?.pipeline_version || genomeMeta.pipeline_version}
                                    </p>
                                )}
                                {formatDate(selectedRun?.processed_at) && (
                                    <p>
                                        <strong>Processed:&nbsp;</strong>
                                        {formatDate(selectedRun?.processed_at)}
                                    </p>
                                )}
                                {(selectedRun?.doc_link || genomeMeta.annotation_doc_link) && (
                                    <p>
                                        <strong>Processing details:&nbsp;</strong>
                                        <a
                                            href={selectedRun?.doc_link || genomeMeta.annotation_doc_link || '#'}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            README
                                        </a>
                                    </p>
                                )}
                                {previousRuns.length > 0 && (
                                    <p>
                                        <strong>Previous annotations:&nbsp;</strong>
                                        {previousRuns.map((run, index) => (
                                            <span key={run.id}>
                                                {index > 0 ? ', ' : ''}
                                                <Link
                                                    to={withAnnotationRunParam(
                                                        currentGenomePath(genomeMeta.isolate_name, locusTag),
                                                        run.id,
                                                    )}
                                                >
                                                    release {run.release_label}
                                                </Link>
                                            </span>
                                        ))}
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
