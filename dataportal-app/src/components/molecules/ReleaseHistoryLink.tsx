import React, {useEffect, useState} from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {GenomeService} from '../../services/genome';
import {GeneService} from '../../services/gene';
import {ReleaseAppearance, StrainAnnotation} from '../../interfaces/Genome';
import {RELEASE_SELECTOR_ENABLED} from '../../config/featureFlags';
import styles from './ReleaseHistoryLink.module.scss';

type ReleaseHistoryKind = 'genome' | 'gene';

interface ReleaseHistoryLinkProps {
    kind: ReleaseHistoryKind;
    id: string;
    label?: string;
    iconOnly?: boolean;
}

const formatPipeline = (annotation?: StrainAnnotation | null): string | null => {
    if (!annotation) {
        return null;
    }
    const parts = [annotation.pipeline, annotation.pipeline_version].filter(Boolean);
    return parts.length ? parts.join(' ') : null;
};

const ReleaseHistoryLink: React.FC<ReleaseHistoryLinkProps> = ({
    kind,
    id,
    label = 'Releases',
    iconOnly = false,
}) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [appearances, setAppearances] = useState<ReleaseAppearance[] | null>(null);

    useEffect(() => {
        setAppearances(null);
        setError(null);
    }, [kind, id]);

    const handleOpenChange = (nextOpen: boolean) => {
        setOpen(nextOpen);
        if (!nextOpen || appearances !== null || !id) {
            return;
        }
        setLoading(true);
        setError(null);
        const request =
            kind === 'genome'
                ? GenomeService.fetchReleaseHistory(id)
                : GeneService.fetchReleaseHistory(id);
        request
            .then((history) => {
                setAppearances(history.appearances || []);
            })
            .catch(() => {
                setError('Could not load release information.');
                setAppearances([]);
            })
            .finally(() => {
                setLoading(false);
            });
    };

    if (!RELEASE_SELECTOR_ENABLED || !id) {
        return null;
    }

    const title = `Releases for ${id}`;

    return (
        <Dialog.Root open={open} onOpenChange={handleOpenChange}>
            <Dialog.Trigger asChild>
                <button
                    type="button"
                    className={`${styles.trigger} ${iconOnly ? styles.triggerIconOnly : ''}`}
                    title="View release information"
                    aria-label="View release information"
                    onClick={(event) => event.stopPropagation()}
                >
                    <span className={`icon icon-common icon-info ${styles.icon}`} aria-hidden="true" />
                    {!iconOnly && label}
                </button>
            </Dialog.Trigger>
            <Dialog.Portal>
                <Dialog.Overlay className={styles.overlay} />
                <Dialog.Content
                    className={styles.content}
                    onClick={(event) => event.stopPropagation()}
                    aria-describedby={undefined}
                >
                    <Dialog.Title className={styles.title}>{title}</Dialog.Title>
                    {loading && <p className={styles.status}>Loading…</p>}
                    {error && <p className={styles.error}>{error}</p>}
                    {!loading && !error && appearances && appearances.length === 0 && (
                        <p className={styles.status}>No readable releases contain this record.</p>
                    )}
                    {!loading && appearances && appearances.length > 0 && (
                        <ul className={styles.list}>
                            {appearances.map((row) => {
                                const pipeline = formatPipeline(row.annotation);
                                const docUrl = row.annotation?.processing_document_url;
                                const docLabel =
                                    row.annotation?.processing_reference || docUrl;
                                return (
                                    <li key={row.version} className={styles.item}>
                                        <div className={styles.version}>
                                            {row.version}
                                            {row.is_current ? ' — Current' : ` — ${row.status}`}
                                        </div>
                                        {pipeline && (
                                            <div>Pipeline: {pipeline}</div>
                                        )}
                                        {docUrl && (
                                            <div>
                                                Processing document:{' '}
                                                <a href={docUrl} target="_blank" rel="noopener noreferrer">
                                                    {docLabel}
                                                </a>
                                            </div>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                    <Dialog.Close asChild>
                        <button type="button" className={styles.close}>
                            Close
                        </button>
                    </Dialog.Close>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
};

export default ReleaseHistoryLink;
