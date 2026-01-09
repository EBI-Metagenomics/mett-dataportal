import cytoscape from 'cytoscape';

/**
 * Zoom levels for rendering optimization
 */
export enum ZoomLevel {
  /** Very zoomed out - show only nodes (no labels, minimal edges) */
  MINIMAL = 'minimal',
  /** Medium zoom - show some labels and edges */
  MEDIUM = 'medium',
  /** High zoom - show all labels and edges */
  FULL = 'full',
}

/**
 * Determine zoom level based on Cytoscape zoom value
 * Uses hysteresis to prevent flickering at boundaries
 */
export function getZoomLevel(zoom: number, previousLevel?: ZoomLevel): ZoomLevel {
  // Use hysteresis: different thresholds for going up vs going down
  // This prevents rapid toggling when zoom is near a boundary
  if (previousLevel === ZoomLevel.MINIMAL) {
    // When coming from minimal, need to go higher to switch
    if (zoom < 0.4) return ZoomLevel.MINIMAL;
    if (zoom < 0.8) return ZoomLevel.MEDIUM;
    return ZoomLevel.FULL;
  } else if (previousLevel === ZoomLevel.MEDIUM) {
    // When in medium, use narrower thresholds
    if (zoom < 0.35) return ZoomLevel.MINIMAL;
    if (zoom < 0.75) return ZoomLevel.MEDIUM;
    return ZoomLevel.FULL;
  } else {
    // When coming from full or initial, use standard thresholds
    if (zoom < 0.3) return ZoomLevel.MINIMAL;
    if (zoom < 0.7) return ZoomLevel.MEDIUM;
    return ZoomLevel.FULL;
  }
}

/**
 * Apply zoom-based rendering optimizations to Cytoscape instance
 * This improves performance by reducing rendering complexity at low zoom levels
 * Uses smooth transitions to avoid visual jumps
 */
export function applyZoomOptimization(
  cy: cytoscape.Core,
  zoomLevel: ZoomLevel,
  showOrthologs: boolean
): void {
  cy.batch(() => {
    cy.nodes().forEach(node => {
      const nodeData = node.data();
      const isPPI = nodeData.nodeType === 'ppi';
      const isOrtholog = nodeData.nodeType === 'ortholog';
      
      // Don't change node sizes dynamically - it causes jumps
      // Only change text opacity and use CSS transitions for smooth changes
      switch (zoomLevel) {
        case ZoomLevel.MINIMAL:
          // Hide all labels
          node.style('text-opacity', 0);
          break;
          
        case ZoomLevel.MEDIUM:
          // Show labels for PPI nodes if orthologs are enabled, hide ortholog labels
          if (showOrthologs && isPPI) {
            node.style('text-opacity', 1);
          } else if (isOrtholog) {
            node.style('text-opacity', 0);
          } else {
            node.style('text-opacity', 0.6); // Semi-transparent
          }
          break;
          
        case ZoomLevel.FULL:
          // Show all labels
          if (showOrthologs && isPPI) {
            node.style('text-opacity', 1);
          } else if (isOrtholog) {
            node.style('text-opacity', 0);
          } else {
            node.style('text-opacity', 1);
          }
          break;
      }
    });
    
    cy.edges().forEach(edge => {
      switch (zoomLevel) {
        case ZoomLevel.MINIMAL:
          // Lower opacity for edges at minimal zoom
          edge.style('opacity', 0.3);
          break;
          
        case ZoomLevel.MEDIUM:
          // Medium opacity
          edge.style('opacity', 0.6);
          break;
          
        case ZoomLevel.FULL:
          // Full opacity
          edge.style('opacity', 1);
          break;
      }
    });
  });
}

/**
 * Create a debounced zoom handler that only applies optimization when zoom level changes
 */
export function createDebouncedZoomHandler(
  cy: cytoscape.Core,
  showOrthologs: boolean,
  debounceMs: number = 150
): { handler: () => void; cleanup: () => void } {
  let lastZoomLevel: ZoomLevel | undefined = undefined;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  
  const handler = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    timeoutId = setTimeout(() => {
      const currentZoom = cy.zoom();
      const newZoomLevel = getZoomLevel(currentZoom, lastZoomLevel);
      
      // Only apply optimization if zoom level actually changed
      if (newZoomLevel !== lastZoomLevel) {
        applyZoomOptimization(cy, newZoomLevel, showOrthologs);
        lastZoomLevel = newZoomLevel;
      }
      
      timeoutId = null;
    }, debounceMs);
  };
  
  const cleanup = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };
  
  return { handler, cleanup };
}
