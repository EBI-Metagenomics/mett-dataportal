import React, {useState} from 'react';
import styles from './PyhmmerResultsTable.module.scss';
import {GeneService} from '../../../../services/geneService';
import {PyhmmerResult} from "../../../../interfaces/Pyhmmer";
import Pagination from '@components/molecules/Pagination';

const DEFAULT_PAGE_SIZE = 10;

interface PyhmmerResultsTableProps {
    results: PyhmmerResult[];
    loading: boolean;
    error?: string;
}

const PyhmmerResultsTable: React.FC<PyhmmerResultsTableProps> = ({results, loading, error}) => {
    const [loadingIdx, setLoadingIdx] = useState<number | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PAGE_SIZE);

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

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setPageSize(Number(event.target.value));
        setCurrentPage(1);
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