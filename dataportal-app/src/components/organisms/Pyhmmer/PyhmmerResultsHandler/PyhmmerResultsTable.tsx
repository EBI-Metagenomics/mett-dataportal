import React, {useState} from 'react';
import styles from './PyhmmerResultsTable.module.scss';
import {GeneService} from '../../../../services/geneService';
import {PyhmmerService} from '../../../../services/pyhmmerService';
import {PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import Pagination from '@components/molecules/Pagination';
import {saveAs} from 'file-saver';
import AlignmentView from '@components/atoms/AlignmentView/AlignmentView';

const DEFAULT_PAGE_SIZE = 10;

interface PyhmmerResultsTableProps {
    results: PyhmmerResult[];
    loading: boolean;
    loadingMessage?: string;
    error?: string;
    jobId?: string;
}

const PyhmmerResultsTable: React.FC<PyhmmerResultsTableProps> = ({results, loading, loadingMessage, error, jobId}) => {
    const [loadingIdx, setLoadingIdx] = useState<number | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [pageSize] = useState<number>(DEFAULT_PAGE_SIZE);
    const [downloading, setDownloading] = useState<string | null>(null);
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

    const totalPages = Math.ceil((results?.length || 0) / pageSize);
    const hasPrevious = currentPage > 1;
    const hasNext = currentPage < totalPages;

    const paginatedResults = results.slice((currentPage - 1) * pageSize, currentPage * pageSize);

    const handleTargetClick = async (locus_tag: string, idx: number) => {
        setLoadingIdx(idx);
        try {
            const gene = await GeneService.fetchGeneByLocusTag(locus_tag);
            if (gene && gene.isolate_name && gene.locus_tag) {
                const url = `/genome/${gene.isolate_name}?locus_tag=${gene.locus_tag}`;
                window.open(url, '_blank');
            }
        } catch {
            // Optionally handle error
        } finally {
            setLoadingIdx(null);
        }
    };

    const handleRowExpand = (rowIndex: number) => {
        const newExpandedRows = new Set(expandedRows);
        if (newExpandedRows.has(rowIndex)) {
            newExpandedRows.delete(rowIndex);
        } else {
            newExpandedRows.add(rowIndex);
        }
        setExpandedRows(newExpandedRows);
    };

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
        // Clear expanded rows when changing pages
        setExpandedRows(new Set());
    };

    const handleDownload = async (format: 'tab' | 'fasta' | 'aligned_fasta') => {
        if (!jobId) return;
        setDownloading(format);
        try {
            const blob = await PyhmmerService.downloadResults(jobId, format);
            
            let filename = '';
            if (format === 'tab') filename = `pyhmmer_hits_${jobId}.tsv`;
            if (format === 'fasta') filename = `pyhmmer_hits_${jobId}.fasta.gz`;
            if (format === 'aligned_fasta') filename = `pyhmmer_hits_${jobId}.aligned.fasta.gz`;
            
            saveAs(blob, filename);
        } catch (error) {
            console.error('Download failed:', error);
            alert('Failed to download file.');
        } finally {
            setDownloading(null);
        }
    };

    if (loading) {
        return (
            <div className={styles.spinner}>
                <div className={styles.spinnerText}>
                    {loadingMessage || 'Loading...'}
                </div>
                <div className={styles.spinnerAnimation}>
                    <div className={styles.spinnerDot}></div>
                    <div className={styles.spinnerDot}></div>
                    <div className={styles.spinnerDot}></div>
                </div>
            </div>
        );
    }
    if (error) {
        return <div className={styles.error}>{error}</div>;
    }
    if (!results || results.length === 0) {
        return <div className={styles.noResults}>No results found.</div>;
    }
    return (
        <>
            {/* Download buttons */}
            {jobId && (
                <div className={styles.downloadButtons}>
                    <button
                        className="vf-button vf-button--sm"
                        onClick={() => handleDownload('tab')}
                        disabled={!!downloading}
                    >
                        {downloading === 'tab' ? 'Downloading...' : 'Tab Delimited'}
                    </button>
                    <button
                        className="vf-button vf-button--sm"
                        onClick={() => handleDownload('fasta')}
                        disabled={!!downloading}
                    >
                        {downloading === 'fasta' ? 'Downloading...' : 'FASTA'}
                    </button>
                    <button
                        className="vf-button vf-button--sm"
                        onClick={() => handleDownload('aligned_fasta')}
                        disabled={!!downloading}
                    >
                        {downloading === 'aligned_fasta' ? 'Downloading...' : 'Aligned FASTA'}
                    </button>
                </div>
            )}
            <table className={styles.resultsTable}>
                <thead>
                <tr>
                    <th></th>
                    <th>Target</th>
                    <th>E-value</th>
                    <th>Score</th>
                    <th>Hits</th>
                    <th>Significant Hits</th>
                    <th>Description</th>
                </tr>
                </thead>
                <tbody>
                {paginatedResults.map((result, idx) => {
                    const isExpanded = expandedRows.has(idx);
                    const hasDomains = result.domains && result.domains.length > 0;
                    
                    return (
                        <React.Fragment key={idx}>
                            <tr className={`${styles.resultRow} ${isExpanded ? styles.expanded : ''}`}>
                                <td className={styles.expandCell}>
                                    {hasDomains && (
                                        <button
                                            className={`${styles.expandButton} ${isExpanded ? styles.expanded : ''}`}
                                            onClick={() => handleRowExpand(idx)}
                                            aria-label={isExpanded ? 'Collapse' : 'Expand'}
                                        >
                                            {isExpanded ? '▼' : '▶'}
                                        </button>
                                    )}
                                </td>
                                <td>
                                    <a
                                        href="#"
                                        onClick={e => {
                                            e.preventDefault();
                                            handleTargetClick(result.target, idx);
                                        }}
                                        className={`${styles.targetLink} ${loadingIdx === idx ? styles.loading : ''}`}
                                    >
                                        {loadingIdx === idx ? 'Loading...' : result.target}
                                    </a>
                                </td>
                                <td>{result.evalue}</td>
                                <td>{result.score}</td>
                                <td>{result.num_hits}</td>
                                <td>{result.num_significant}</td>
                                <td>{result.description ?? '-'}</td>
                            </tr>
                            {isExpanded && hasDomains && jobId && (
                                <tr className={styles.expandedRow}>
                                    <td colSpan={7} className={styles.expandedCell}>
                                        <AlignmentView jobId={jobId} target={result.target} />
                                    </td>
                                </tr>
                            )}
                        </React.Fragment>
                    );
                })}
                </tbody>
            </table>
            {/* Page size dropdown and pagination */}
            <div className={styles.paginationContainer}>
                <div className={styles.paginationBar}>
                    {totalPages > 1 && (
                        <Pagination
                            currentPage={currentPage}
                            totalPages={totalPages}
                            hasPrevious={hasPrevious}
                            hasNext={hasNext}
                            onPageClick={handlePageClick}
                        />
                    )}
                </div>
            </div>
        </>
    );
};

export default PyhmmerResultsTable; 