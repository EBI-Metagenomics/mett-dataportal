import React from 'react';
import styles from './Breadcrumb.module.scss';

export type BreadcrumbPage = 'home' | 'api-docs' | 'genome-view';

interface BreadcrumbProps {
    currentPage: BreadcrumbPage;
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ currentPage }) => {
    return (
        <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
            <ul className={`vf-breadcrumbs__list vf-list vf-list--inline ${styles.breadcrumbList}`}>
                <li className={styles.breadcrumbItem}>
                    {currentPage === 'home' ? (
                        <b>Home</b>
                    ) : (
                        <a href="/" className="vf-breadcrumbs__link">Home</a>
                    )}
                </li>
                <span className={styles.separator}> | </span>
                <li className={styles.breadcrumbItem}>
                    {currentPage === 'api-docs' ? (
                        <b>API Docs</b>
                    ) : (
                        <a href="/api/docs" className="vf-breadcrumbs__link">API Docs</a>
                    )}
                </li>
                
                <li className={styles.breadcrumbItem}>
                    {currentPage === 'genome-view' ? (
                        <b><span className={styles.separator}> | </span> Genome View</b>
                    ) : (
                        <span></span>
                    )}
                </li>
            </ul>
        </nav>
    );
};

export default Breadcrumb;

