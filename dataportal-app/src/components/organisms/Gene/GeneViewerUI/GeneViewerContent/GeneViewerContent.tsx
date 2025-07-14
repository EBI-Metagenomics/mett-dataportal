import React from 'react';
import { JBrowseApp } from "@jbrowse/react-app2";
import styles from './GeneViewerContent.module.scss';

interface GeneViewerContentProps {
  viewState: any;
  height: number;
  onRefreshTracks?: () => void;
}

const GeneViewerContent: React.FC<GeneViewerContentProps> = ({
  viewState,
  height,
  onRefreshTracks,
}) => {
  // Refresh tracks when viewState changes
  React.useEffect(() => {
    if (viewState && onRefreshTracks) {
      onRefreshTracks();
    }
  }, [viewState, onRefreshTracks]);

  if (!viewState) {
    return <p>Loading Genome Viewer...</p>;
  }

  return (
    <div
      style={{
        maxHeight: `${height}px`,
        overflowY: 'auto',
        overflowX: 'auto',
      }}
    >
      <div className={styles.jbrowseViewer}>
        <div className={styles.jbrowseContainer}>
          <JBrowseApp viewState={viewState}/>
        </div>
      </div>
    </div>
  );
};

export default GeneViewerContent; 