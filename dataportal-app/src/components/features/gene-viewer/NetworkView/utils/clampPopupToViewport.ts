const DEFAULT_MARGIN = 12;

/**
 * Returns pixel deltas to shift an element so its getBoundingClientRect() stays inside the viewport.
 */
export function computeViewportClampDelta(rect: DOMRect, margin = DEFAULT_MARGIN): { dx: number; dy: number } {
  const vw = typeof window !== 'undefined' ? window.innerWidth : 0;
  const vh = typeof window !== 'undefined' ? window.innerHeight : 0;
  if (!vw || !vh) return { dx: 0, dy: 0 };

  let dx = 0;
  let dy = 0;

  if (rect.width <= vw - 2 * margin) {
    if (rect.left < margin) dx += margin - rect.left;
    if (rect.right + dx > vw - margin) dx += vw - margin - (rect.right + dx);
  } else {
    dx = margin - rect.left;
  }

  if (rect.height <= vh - 2 * margin) {
    if (rect.top < margin) dy += margin - rect.top;
    if (rect.bottom + dy > vh - margin) dy += vh - margin - (rect.bottom + dy);
  } else {
    dy = margin - rect.top;
  }

  return { dx, dy };
}
