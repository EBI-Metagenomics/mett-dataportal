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

  /**
   * Global cloud view configuration
   */
  GLOBAL_CLOUD: {
    CENTER_X: 800, // Center X coordinate for cloud layout
    CENTER_Y: 600, // Center Y coordinate for cloud layout
    BASE_RADIUS: 500, // Base radius for outermost tier (increased for better distribution)
    TIER_RADIUS_INCREMENT: 100, // Radius increment per tier (increased spacing)
    NUM_TIERS: 8, // Number of centrality tiers (more tiers for better granularity)
    ANGLE_SPREAD: Math.PI * 2, // Full circle (2π radians)
    MIN_NODE_DISTANCE: 35, // Minimum distance between nodes in same tier (increased)
  },

  /**
   * Zoom optimization thresholds
   */
  ZOOM: {
    MINIMAL_THRESHOLD: 0.3, // Below this zoom, show minimal rendering
    MEDIUM_THRESHOLD: 0.7, // Below this zoom, show medium rendering
    // Above MEDIUM_THRESHOLD, show full rendering
  },
} as const;

