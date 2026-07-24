import cytoscape from 'cytoscape';
// cytoscape-fcose has no bundled TypeScript types
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error -- no type declarations for cytoscape-fcose
import fcose from 'cytoscape-fcose';

let registered = false;

/**
 * Register Cytoscape layout extensions once (idempotent).
 */
export function registerCytoscapeExtensions(): void {
  if (registered) return;
  cytoscape.use(fcose);
  registered = true;
}
