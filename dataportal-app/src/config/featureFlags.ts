/**
 * Feature flags driven by environment variables.
 * Set via Kubernetes ConfigMap/Secret for deployment control.
 */

const parseBool = (value: string | undefined): boolean => {
  if (value == null || value === '') return false;
  const v = value.toLowerCase().trim();
  return v === 'true' || v === '1';
};

/**
 * Network View tab in Gene Viewer.
 * When false (default), the tab is hidden and never rendered.
 * Set VITE_NETWORK_VIEW_ENABLED=true in Kubernetes to enable.
 */
export const NETWORK_VIEW_ENABLED = parseBool(
  import.meta.env.VITE_NETWORK_VIEW_ENABLED
);

/** Helper for checking if Network View tab is enabled. */
export const isNetworkViewEnabled = (): boolean => NETWORK_VIEW_ENABLED;
