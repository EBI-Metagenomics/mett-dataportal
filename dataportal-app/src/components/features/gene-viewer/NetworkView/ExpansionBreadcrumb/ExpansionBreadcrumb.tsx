import React from 'react';
import { ExpansionState } from '../types/expansion';
import styles from './ExpansionBreadcrumb.module.scss';

interface ExpansionBreadcrumbProps {
  expansionState: ExpansionState;
  onNavigateToLevel?: (level: number) => void;
  onClearAll?: () => void;
}

export const ExpansionBreadcrumb: React.FC<ExpansionBreadcrumbProps> = ({
  expansionState,
  onNavigateToLevel,
  onClearAll,
}) => {
  if (expansionState.path.nodes.length === 0) {
    return null;
  }

  return (
    <div className={styles.breadcrumbContainer}>
      <span className={styles.breadcrumbLabel}>Path:</span>
      <div className={styles.breadcrumbList}>
        {expansionState.path.nodes.map((pathNode, index) => (
          <React.Fragment key={pathNode.nodeId}>
            {index > 0 && <span className={styles.separator}>›</span>}
            <button
              className={styles.breadcrumbItem}
              onClick={() => {
                // Navigate back: clicking on a node shows the state up to that node
                // For level 0, we want to go back to the initial state
                const targetLevel = index === 0 ? -1 : index - 1;
                onNavigateToLevel?.(targetLevel);
              }}
              title={`Navigate to level ${pathNode.level}`}
            >
              {pathNode.locusTag || pathNode.nodeId}
            </button>
          </React.Fragment>
        ))}
      </div>
      {onClearAll && (
        <button
          className={styles.clearButton}
          onClick={onClearAll}
          title="Clear all expansions"
        >
          Clear All
        </button>
      )}
    </div>
  );
};

