/**
 * View mode types for NetworkView
 */
export type NetworkViewMode = 'global' | 'focused';

/**
 * Global view: Shows all proteins in a cloud-like visualization
 * - More connected proteins closer to center
 * - Less connected proteins on outer areas
 * - Used when no gene is selected or all paths are cleared
 */
export interface GlobalViewState {
  mode: 'global';
}

/**
 * Focused view: Shows only selected node and its interactions
 * - Used when a node is selected from global view
 * - Allows building expansion paths (sub-graph expansion)
 */
export interface FocusedViewState {
  mode: 'focused';
  selectedNodeId: string;
}

/**
 * Union type for view state
 */
export type ViewState = GlobalViewState | FocusedViewState;

/**
 * Helper functions for view state
 */
export const ViewStateUtils = {
  isGlobal: (state: ViewState): state is GlobalViewState => state.mode === 'global',
  isFocused: (state: ViewState): state is FocusedViewState => state.mode === 'focused',
  createGlobal: (): GlobalViewState => ({ mode: 'global' }),
  createFocused: (nodeId: string): FocusedViewState => ({ mode: 'focused', selectedNodeId: nodeId }),
};
