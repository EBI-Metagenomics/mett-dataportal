import type cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';
import { getFcoseLayoutOptions } from './getFcoseLayoutOptions';

const L = NETWORK_VIEW_CONSTANTS.FCOSE_LAYOUT;
const POSITION_CLAMP = 8000;
const FCOSE_NODE_LIMIT = 120;

export type LayoutMode = 'full' | 'inPlace' | 'reset';

export interface LayoutControl {
  instance: cytoscape.Layouts | null;
  running: boolean;
}

export const stopLayout = (control: { current: LayoutControl }): void => {
  try {
    control.current.instance?.stop();
  } catch {
    // ignore
  }
  control.current.instance = null;
  control.current.running = false;
};

export const sanitizeNodePositions = (cy: cytoscape.Core): void => {
  cy.nodes().forEach((node) => {
    const p = node.position();
    const invalid =
      !Number.isFinite(p.x) ||
      !Number.isFinite(p.y) ||
      Math.abs(p.x) > POSITION_CLAMP ||
      Math.abs(p.y) > POSITION_CLAMP;
    if (invalid) {
      node.position({
        x: (Math.random() - 0.5) * 200,
        y: (Math.random() - 0.5) * 200,
      });
    }
    try {
      node.unlock();
    } catch {
      // ignore
    }
  });
};

const runCoseFallback = (cy: cytoscape.Core, padding: number): void => {
  const layout = cy.layout({
    name: 'cose',
    animate: false,
    fit: true,
    padding,
    nodeOverlap: 20,
    gravity: 0.25,
    numIter: 800,
    randomize: true,
  } as cytoscape.LayoutOptions);
  layout.run();
};

/**
 * Run fCoSE without overlapping instances. Falls back to cose/fit on failure.
 * Concurrent or mid-mutation fCoSE runs can throw RangeError in calcGrid.
 */
export const runSafeLayout = (
  cy: cytoscape.Core,
  control: { current: LayoutControl },
  options: {
    mode: LayoutMode;
    focalNodeId?: string | null;
  }
): void => {
  if (!cy || cy.destroyed() || cy.nodes().empty()) {
    return;
  }

  stopLayout(control);
  sanitizeNodePositions(cy);

  const padding = options.mode === 'inPlace' ? L.FIT_PADDING_IN_PLACE : L.FIT_PADDING;
  const nodeCount = cy.nodes().length;
  const useFcose = nodeCount <= FCOSE_NODE_LIMIT;

  const onStop = (layout: cytoscape.Layouts) => {
    layout.one('layoutstop', () => {
      if (control.current.instance === layout) {
        control.current.instance = null;
        control.current.running = false;
      }
      try {
        if (!cy.destroyed()) cy.fit(undefined, padding);
      } catch {
        // ignore
      }
    });
  };

  try {
    if (!useFcose) {
      control.current.running = true;
      runCoseFallback(cy, padding);
      control.current.running = false;
      return;
    }

    const layout = cy.layout(
      getFcoseLayoutOptions({
        focalNodeId: options.mode === 'reset' ? null : options.focalNodeId,
        inPlace: options.mode === 'inPlace',
        randomize: options.mode === 'reset' ? true : undefined,
        animate: options.mode !== 'inPlace',
        nodeCount,
      }) as unknown as cytoscape.LayoutOptions
    );
    control.current.instance = layout;
    control.current.running = true;
    onStop(layout);
    layout.run();
  } catch {
    control.current.instance = null;
    control.current.running = false;
    try {
      if (!cy.destroyed()) {
        runCoseFallback(cy, padding);
      }
    } catch {
      try {
        if (!cy.destroyed()) cy.fit(undefined, padding);
      } catch {
        // ignore
      }
    }
  }
};
