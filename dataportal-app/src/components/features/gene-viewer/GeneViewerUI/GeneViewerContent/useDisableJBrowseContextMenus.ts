import { useEffect, type RefObject } from 'react';

/**
 * Block browser and JBrowse context menus inside the embedded viewer.
 * Track label ellipsis menus are hidden via CSS; this stops right-click menus.
 */
export function useDisableJBrowseContextMenus(
  containerRef: RefObject<HTMLDivElement | null>,
  viewState: unknown
): void {
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !viewState) return;

    const blockContextMenu = (event: Event) => {
      event.preventDefault();
      event.stopPropagation();
    };

    container.addEventListener('contextmenu', blockContextMenu, true);
    return () => {
      container.removeEventListener('contextmenu', blockContextMenu, true);
    };
  }, [containerRef, viewState]);
}
