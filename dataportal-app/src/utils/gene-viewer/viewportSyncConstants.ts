/**
 * Constants for viewport synchronization between JBrowse and gene tables
 */

export const VIEWPORT_SYNC_CONSTANTS = {
  // Navigation cooldown period (milliseconds)
  TABLE_NAVIGATION_COOLDOWN_MS: 5000,
  // How long to respect a manual switch back to search view before auto-switching again
  AUTO_SWITCH_MANUAL_OVERRIDE_MS: 2000,
  
  // Safety window after blocking a fetch (milliseconds)
  RECENT_BLOCK_WINDOW_MS: 1000,
  
  // Viewport polling interval (milliseconds)
  VIEWPORT_POLLING_INTERVAL_MS: 200,
  
  // Viewport debounce delay (milliseconds)
  VIEWPORT_DEBOUNCE_MS: 1500,
  
  // Viewport buffer percentage (10% on each side)
//   VIEWPORT_BUFFER_PERCENT: 0.1,
  VIEWPORT_BUFFER_PERCENT: 0,
  
  // Large region threshold (if viewport covers more than 50% of region)
  LARGE_REGION_THRESHOLD: 0.5,
  
  // Minimum region length to apply large region logic (base pairs)
  MIN_REGION_LENGTH_FOR_CENTERED_WINDOW: 10000,
  
  // Centered window size (base pairs) when viewport is too large
  CENTERED_WINDOW_SIZE_BP: 50000,
  
  // Minimum viewport size (base pairs)
  MIN_VIEWPORT_SIZE_BP: 1000,
  
  // Default viewport width (pixels) - fallback if not available from JBrowse
  DEFAULT_VIEWPORT_WIDTH_PX: 800 as number,
  
  // Sync view page size (genes per page - no pagination in sync view)
  SYNC_VIEW_PAGE_SIZE: 1000,
  
  // Test base pairs for width estimation
  TEST_BP_FOR_WIDTH_ESTIMATION: 1000,
  
  // Gene highlighting colors (unified across table, JBrowse, and feature panel)
  GENE_HIGHLIGHT_COLOR: '#2563eb', // Primary blue color for highlighting selected genes
  GENE_HIGHLIGHT_BACKGROUND: '#dbeafe', // Light blue background for table rows
  GENE_HIGHLIGHT_BORDER: '#2563eb', // Blue border for table rows
  GENE_HIGHLIGHT_BACKGROUND_HOVER: '#bfdbfe', // Slightly darker blue for hover state
} as const;

