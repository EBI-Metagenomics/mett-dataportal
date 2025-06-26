import React, {useState} from 'react';
import styles from './PyhmmerResultsTable.module.scss';
import {GeneService} from '../../../../services/geneService';
import {PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import Pagination from '@components/molecules/Pagination';
import {saveAs} from 'file-saver';

const DEFAULT_PAGE_SIZE = 10;

interface PyhmmerResultsTableProps {
    results: PyhmmerResult[];
    loading: boolean;
    error?: string;
    jobId?: string;
}

const PyhmmerResultsTable: React.FC<PyhmmerResultsTableProps> = ({results, loading, error, jobId}) => {
    const [loadingIdx, setLoadingIdx] = useState<number | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [pageSize] = useState<number>(DEFAULT_PAGE_SIZE);
    const [downloading, setDownloading] = useState<string | null>(null);

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

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
    };

    const handleDownload = async (format: 'tab' | 'fasta' | 'aligned_fasta') => {
        if (!jobId) return;
        setDownloading(format);
        try {
            const url = `/api/pyhmmer/results/${jobId}/download?format=${format}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Download failed');
            const blob = await response.blob();
            let filename = '';
            if (format === 'tab') filename = `pyhmmer_hits_${jobId}.tsv`;
            if (format === 'fasta') filename = `pyhmmer_hits_${jobId}.fasta.gz`;
            if (format === 'aligned_fasta') filename = `pyhmmer_hits_${jobId}.aligned.fasta.gz`;
            saveAs(blob, filename);
        } catch {
            alert('Failed to download file.');
        } finally {
            setDownloading(null);
        }
    };

    if (loading) {
        return <div className={styles.spinner}>Loading...</div>;
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
                <div style={{display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 8}}>
                    <button
                        className="vf-button vf-button--sm"
                        style={{minWidth: 90, padding: '5px 14px', fontSize: '0.98em'}}
                        onClick={() => handleDownload('tab')}
                        disabled={!!downloading}
                    >
                        {downloading === 'tab' ? 'Downloading...' : 'Tab Delimited'}
                    </button>
                    <button
                        className="vf-button vf-button--sm"
                        style={{minWidth: 90, padding: '5px 14px', fontSize: '0.98em'}}
                        onClick={() => handleDownload('fasta')}
                        disabled={!!downloading}
                    >
                        {downloading === 'fasta' ? 'Downloading...' : 'FASTA'}
                    </button>
                    <button
                        className="vf-button vf-button--sm"
                        style={{minWidth: 110, padding: '5px 14px', fontSize: '0.98em'}}
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
                    <th>Target</th>
                    <th>E-value</th>
                    <th>Score</th>
                    <th>Hits</th>
                    <th>Significant Hits</th>
                    <th>Description</th>
                </tr>
                </thead>
                <tbody>
                {paginatedResults.map((result, idx) => (
                    <tr key={idx}>
                        <td>
                            <a
                                href="#"
                                onClick={e => {
                                    e.preventDefault();
                                    handleTargetClick(result.target, idx);
                                }}
                                style={{
                                    pointerEvents: loadingIdx === idx ? 'none' : 'auto',
                                    opacity: loadingIdx === idx ? 0.5 : 1
                                }}
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
                ))}
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