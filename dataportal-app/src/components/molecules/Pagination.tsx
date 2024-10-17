import React from 'react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    hasPrevious: boolean;
    hasNext: boolean;
    onPageClick: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalPages, hasPrevious, hasNext, onPageClick }) => {
    return (
        <nav className="vf-pagination" aria-label="Pagination">
            <ul className="vf-pagination__list">
                {hasPrevious && (
                    <>
                        <li className="vf-pagination__item">
                            <button className="vf-pagination__link" onClick={() => onPageClick(1)}>First</button>
                        </li>
                        <li className="vf-pagination__item">
                            <button className="vf-pagination__link" onClick={() => onPageClick(currentPage - 1)}>Previous</button>
                        </li>
                    </>
                )}
                <li className="vf-pagination__item">
                    <span className="vf-pagination__link">Page {currentPage} of {totalPages}</span>
                </li>
                {hasNext && (
                    <>
                        <li className="vf-pagination__item">
                            <button className="vf-pagination__link" onClick={() => onPageClick(currentPage + 1)}>Next</button>
                        </li>
                        <li className="vf-pagination__item">
                            <button className="vf-pagination__link" onClick={() => onPageClick(totalPages)}>Last</button>
                        </li>
                    </>
                )}
            </ul>
        </nav>
    );
};

export default Pagination;
