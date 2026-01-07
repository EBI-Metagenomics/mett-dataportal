/**
 * Constants for Network View configuration
 */

export const NETWORK_VIEW_CONSTANTS = {
  /**
   * Maximum depth for node expansion
   * Controls how many levels deep users can expand interactions
   */
  MAX_EXPANSION_DEPTH: 5,

  /**
   * Edge width configuration
   */
  EDGE_WIDTH: {
    MIN: 2, // Minimum edge width in pixels
    MAX: 10, // Maximum edge width in pixels
    BASE_SCALE: 2.0, // Base multiplier for score scaling
  },

  /**
   * Node expansion visual styling
   */
  EXPANSION: {
    EXPANDED_NODE_BORDER_WIDTH: 3, // Border width for expanded nodes
    EXPANDED_NODE_BORDER_COLOR: '#FF6B6B', // Red highlight color (current expansion)
    EXPANDED_NODE_SIZE_MULTIPLIER: 1.3, // Size increase for expanded nodes
    // Colors for different expansion levels (for edges)
    LEVEL_COLORS: [
      '#999', // Level 0 (original) - gray
      '#bf321e', // Level 1 - red
      '#50C878', // Level 2 - green
      '#FF9800', // Level 3 - orange
      '#9C27B0', // Level 4 - purple
      '#E91E63', // Level 5 - pink
    ],
    // Radial layout configuration
    RADIAL_LAYOUT: {
      BASE_RADIUS: 150, // Base radius for level 1 (in pixels)
      LEVEL_RADIUS_INCREMENT: 200, // Additional radius per expansion level
      CENTER_X: 600, // Center X coordinate (adjusted for larger viewport)
      CENTER_Y: 600, // Center Y coordinate (adjusted for larger viewport)
      ANGLE_SPREAD: Math.PI * 2, // Full circle (2π radians)
    },
  },
} as const;

