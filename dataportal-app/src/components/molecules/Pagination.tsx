import React from 'react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    hasPrevious: boolean;
    hasNext: boolean;
    onPageClick: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
                                                   currentPage,
                                                   totalPages,
                                                   hasPrevious,
                                                   hasNext,
                                                   onPageClick
                                               }) => {
    const handlePageClick = (page: number) => {
        if (page < 1 || page > totalPages) return;
        onPageClick(page);
    };

    return (
        <nav className="vf-pagination" aria-label="Pagination">
            <ul className="vf-pagination__list">
                {/* "First" button */}
                <li className="vf-pagination__item">
                    <button
                        className="vf-pagination__link"
                        onClick={() => handlePageClick(1)}
                        disabled={!hasPrevious}
                    >
                        First
                    </button>
                </li>

                {/* "Previous" button */}
                <li className="vf-pagination__item">
                    <button
                        className="vf-pagination__link"
                        onClick={() => handlePageClick(currentPage - 1)}
                        disabled={!hasPrevious}
                    >
                        Previous
                    </button>
                </li>

                {/* Current Page Display */}
                <li className="vf-pagination__item">
                    <span className="vf-pagination__link">
                        Page {currentPage} of {totalPages}
                    </span>
                </li>

                {/* "Next" button */}
                <li className="vf-pagination__item">
                    <button
                        className="vf-pagination__link"
                        onClick={() => handlePageClick(currentPage + 1)}
                        disabled={!hasNext}
                    >
                        Next
                    </button>
                </li>

                {/* "Last" button */}
                <li className="vf-pagination__item">
                    <button
                        className="vf-pagination__link"
                        onClick={() => handlePageClick(totalPages)}
                        disabled={!hasNext}
                    >
                        Last
                    </button>
                </li>
            </ul>
        </nav>
    );
};

export default Pagination;
