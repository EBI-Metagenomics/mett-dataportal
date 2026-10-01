import { autorun, type IReactionDisposer } from 'mobx';

type SessionWithWidgets = {
  activeWidgets?: { size: number };
  hideAllWidgets?: () => void;
};

/**
 * Keep JBrowse drawer widgets closed in embed mode.
 *
 * Assigning `session.showWidget = () => undefined` does not reliably override
 * MST actions. Instead, immediately clear activeWidgets whenever one appears.
 * That also collapses the v4 Paper-based drawer (not MuiDrawer).
 */
export function suppressJBrowseWidgets(
  session: SessionWithWidgets | null | undefined
): IReactionDisposer | undefined {
  if (!session || typeof session.hideAllWidgets !== 'function') {
    return undefined;
  }

  return autorun(() => {
    if ((session.activeWidgets?.size ?? 0) > 0) {
      session.hideAllWidgets?.();
    }
  });
}
