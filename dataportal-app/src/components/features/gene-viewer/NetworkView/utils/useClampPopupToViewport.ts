import { useLayoutEffect, useRef, useState, type RefObject } from 'react';
import { computeViewportClampDelta } from './clampPopupToViewport';

/**
 * After layout, nudges popup position so it stays within the viewport.
 */
export function useClampPopupToViewport(
  left: number,
  top: number
): { popupRef: RefObject<HTMLDivElement | null>; shift: { dx: number; dy: number } } {
  const popupRef = useRef<HTMLDivElement>(null);
  const [shift, setShift] = useState({ dx: 0, dy: 0 });

  useLayoutEffect(() => {
    const el = popupRef.current;
    if (!el) {
      setShift({ dx: 0, dy: 0 });
      return;
    }
    const rect = el.getBoundingClientRect();
    const { dx, dy } = computeViewportClampDelta(rect);
    setShift({ dx, dy });
  }, [left, top]);

  return { popupRef, shift };
}
