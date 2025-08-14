import React, { useState } from 'react';
import { CollapsibleSectionProps } from '../../../../utils/pyhmmer';
import styles from './CollapsibleSection.module.scss';

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
    title,
    expanded = false,
    onToggle,
    children,
    className = ''
}) => {
    const [isExpanded, setIsExpanded] = useState(expanded);
    
    // Handle toggle
    const handleToggle = () => {
        const newExpandedState = !isExpanded;
        setIsExpanded(newExpandedState);
        onToggle?.(newExpandedState);
    };
    
    // Update internal state when prop changes
    React.useEffect(() => {
        setIsExpanded(expanded);
    }, [expanded]);
    
    return (
        <div className={`${styles.collapsibleSection} ${className}`}>
            {/* Header */}
            <div 
                className={styles.sectionHeader}
                onClick={handleToggle}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleToggle();
                    }
                }}
            >
                <div className={styles.headerContent}>
                    <h3 className={styles.sectionTitle}>{title}</h3>
                    <div className={styles.headerActions}>
                        {/* Toggle Icon */}
                        <div className={`${styles.toggleIcon} ${isExpanded ? styles.expanded : ''}`}>
                            <svg 
                                width="16" 
                                height="16" 
                                viewBox="0 0 16 16" 
                                fill="none" 
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path 
                                    d="M6 12L10 8L6 4" 
                                    stroke="currentColor" 
                                    strokeWidth="2" 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Content */}
            <div className={`${styles.sectionContent} ${isExpanded ? styles.expanded : ''}`}>
                <div className={styles.contentInner}>
                    {children}
                </div>
            </div>
        </div>
    );
};

export default CollapsibleSection;
