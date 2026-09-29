import { useEffect, type RefObject } from 'react';
import { hideEmbeddedJBrowseChrome } from './hideJBrowseChrome';

const HIDE_RETRY_DELAYS_MS = [100, 500, 1000] as const;

/**
 * Keep JBrowse app chrome (menu bar, drawers, view controls) hidden in embed mode.
 */
export function useHideJBrowseChrome(
  containerRef: RefObject<HTMLDivElement | null>,
  viewState: unknown
): void {
  useEffect(() => {
    const run = () => hideEmbeddedJBrowseChrome(containerRef.current);

    run();

    const observer = new MutationObserver(run);
    observer.observe(document.body, { childList: true, subtree: true });

    const timeouts = HIDE_RETRY_DELAYS_MS.map(delay => setTimeout(run, delay));

    return () => {
      observer.disconnect();
      timeouts.forEach(clearTimeout);
    };
  }, [containerRef, viewState]);
}
