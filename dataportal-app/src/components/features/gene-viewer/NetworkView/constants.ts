/**
 * Constants for Network View configuration.
 * Graph colors here should match _networkViewTheme.scss for consistency.
 */

export const NETWORK_VIEW_CONSTANTS = {
  /**
   * Maximum depth for node expansion
   * Controls how many levels deep users can expand interactions
   */
  MAX_EXPANSION_DEPTH: 5,

  /**
   * Edge width configuration (weight-based thickness, reference-style visibility)
   */
  EDGE_WIDTH: {
    MIN: 1, // Minimum edge width in pixels (weak interactions)
    MAX: 14, // Maximum edge width in pixels (strong interactions)
    BASE_SCALE: 1, // Use full range for clear weight differences
  },

  /**
   * Graph theme (Cytoscape styles). Align with _networkViewTheme.scss for legend/UI.
   */
  GRAPH_THEME: {
    EDGE: {
      LINE_COLOR: '#5B8DEE',
      OPACITY: 0.65,
      /** Local ES edges (default PPI) */
      LOCAL_EDGE_COLOR: '#5B8DEE',
      /** STRING DB edges – distinct color so "both" view shows two edge types clearly */
      STRINGDB_EDGE_COLOR: '#E65100',
      ORTHOLOG_LINE_COLOR: '#FF9800',
      ORTHOLOG_OPACITY: 0.6,
      ORTHOLOG_WIDTH: 2,
      CONTROL_POINT_STEP_SIZE: 18,
    },
    NODE: {
      PPI_COLOR: '#4A90E2',
      PPI_WITH_ORTHOLOGS_COLOR: '#50C878',
      ORTHOLOG_COLOR: '#FF9800',
      BORDER_COLOR: '#333',
      BORDER_WIDTH: 1,
      WIDTH: 26,
      HEIGHT: 26,
      FONT_SIZE: '9px',
      TEXT_MARGIN_Y: -5,
      TEXT_MAX_WIDTH: '120px',
    },
    FADED: {
      OPACITY: 0.2,
      TEXT_OPACITY: 0.1,
    },
    PATH: {
      NODE_OPACITY: 1,
      EDGE_OPACITY: 0.7,
    },
    PREVIOUS_EXPANSION: {
      BORDER_COLOR: '#ccc',
      NODE_OPACITY: 0.7,
    },
    EXPANSION_EDGE: {
      LINE_WIDTH: 2,
      OPACITY: 0.7,
    },
    SELECTED_EDGE: {
      LINE_WIDTH: 4,
      OPACITY: 1,
      LINE_COLOR: '#FF6B6B',
      Z_INDEX: 999,
    },
  },

  /**
   * Cose (force-directed) layout options. Used in NetworkGraph and useCytoscapeLayout.
   */
  COSE_LAYOUT: {
    PADDING: 80,
    PADDING_IN_PLACE: 50,
    ANIMATION_DURATION: 500,
    ANIMATION_DURATION_IN_PLACE: 700,
    FIT_PADDING: 80,
    FIT_PADDING_IN_PLACE: 50,
    IDEAL_EDGE_LENGTH: 100,
    NODE_REPULSION: 80000,
    NODE_OVERLAP: 20,
    GRAVITY: 0.2,
    NUM_ITER: 1000,
    RANDOMIZE: false,
    AVOID_OVERLAP: true,
    NODE_OVERLAP_IN_PLACE: 10,
    GRAVITY_IN_PLACE: 0.15,
    NUM_ITER_IN_PLACE: 1200,
    NODE_REPULSION_IN_PLACE: 6000,
  },

  /**
   * Slider configuration for NetworkControls (top N / min score).
   */
  SLIDER: {
    TOP_N_MIN: 1,
    TOP_N_MAX: 50,
    TOP_N_TICK_VALUES: [1, 10, 20, 30, 40, 50] as const,
    THRESHOLD_TICK_VALUES: [0, 0.25, 0.5, 0.75, 1] as const,
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

