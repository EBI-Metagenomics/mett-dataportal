import React from 'react';
import styles from './HomepageFilterRail.module.scss';

interface HomepageFilterRailProps {
    title: string;
    children: React.ReactNode;
}

const HomepageFilterRail: React.FC<HomepageFilterRailProps> = ({title, children}) => (
    <aside className={styles.rail} aria-label={title}>
        <div className={styles.header}>
            <h3 className={styles.title}>{title}</h3>
        </div>
        {children}
    </aside>
);

export default HomepageFilterRail;
