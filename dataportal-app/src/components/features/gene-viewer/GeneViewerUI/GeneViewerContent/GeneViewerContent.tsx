import React, { useRef } from 'react';
import { JBrowseApp } from '@jbrowse/react-app2';
import styles from './GeneViewerContent.module.scss';
import { useDisableJBrowseContextMenus } from './useDisableJBrowseContextMenus';
import { useHideJBrowseChrome } from './useHideJBrowseChrome';
import { useJBrowseFeatureSelection } from './useJBrowseFeatureSelection';

interface GeneViewerContentProps {
  viewState: any;
  onRefreshTracks?: () => void;
  onFeatureSelect?: (feature: any) => void;
}

const GeneViewerContent: React.FC<GeneViewerContentProps> = ({
  viewState,
  onRefreshTracks,
  onFeatureSelect,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useHideJBrowseChrome(containerRef, viewState);
  useDisableJBrowseContextMenus(containerRef, viewState);
  useJBrowseFeatureSelection(viewState, onFeatureSelect);

  React.useEffect(() => {
    if (viewState && onRefreshTracks) {
      onRefreshTracks();
    }
  }, [viewState, onRefreshTracks]);

  if (!viewState) {
    return <p>Loading Genome Viewer...</p>;
  }

  return (
    <div className={styles.jbrowseViewer}>
      <div ref={containerRef} className={styles.jbrowseContainer}>
        <JBrowseApp viewState={viewState} />
      </div>
    </div>
  );
};

export default GeneViewerContent;
