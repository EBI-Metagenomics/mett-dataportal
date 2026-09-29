/** JBrowse app-core ViewHeader / ViewMenu test ids. */
export const HIDDEN_JBROWSE_VIEW_CONTROL_TEST_IDS = [
  'view_menu_icon',
  'close_view',
  'minimize_view',
  'track_menu_icon',
] as const;

/**
 * Selectors for JBrowse drawers / feature-detail chrome we suppress in embed mode.
 * Keep these scoped to JBrowse UI — never use document-wide selectors like
 * `[role="presentation"]` or bare `.MuiBackdrop-root` (they break Radix dialogs).
 */
export const JBROWSE_DRAWER_SELECTORS = [
  '.MuiDrawer-root',
  '.MuiDrawer-modal',
  '.MuiDrawer-paper',
  '.MuiDrawer-docked',
  '[class*="MuiDrawer"]',
  'aside[class*="MuiDrawer"]',
  // v4 drawer shell is Paper elevation 16 (see app-core Drawer.js)
  '.MuiPaper-elevation16',
  '[class*="BaseFeatureDetail"]',
  '[class*="FeatureDetails"]',
  '[class*="featureDetails"]',
  '[class*="DrawerWidget"]',
  '[class*="FeatureWidget"]',
  '[class*="BaseFeatureWidget"]',
  '[aria-label*="drawer"]',
  '[aria-label*="Drawer"]',
] as const;

function markHidden(element: Element): void {
  element.classList.add('jbrowse-embed-hidden');
  element.setAttribute('aria-hidden', 'true');
}

export function hideJBrowseViewChrome(container: HTMLElement | null): void {
  if (!container) return;
  for (const testId of HIDDEN_JBROWSE_VIEW_CONTROL_TEST_IDS) {
    container.querySelectorAll(`[data-testid="${testId}"]`).forEach(markHidden);
  }
}

/**
 * Hide the JBrowse FILE/ADD/TOOLS/HELP AppBar.
 * v4 DropDownMenu no longer uses data-testid="dropDownMenuButton", so match AppBar directly.
 */
export function hideJBrowseMenuBar(container: HTMLElement | null): void {
  if (!container) return;
  container.querySelectorAll('.MuiAppBar-root').forEach(markHidden);
  container.querySelectorAll('.MuiFab-root').forEach(markHidden);
}

export function hideJBrowseDrawers(container: HTMLElement | null): void {
  if (!container) return;
  JBROWSE_DRAWER_SELECTORS.forEach(selector => {
    try {
      container.querySelectorAll(selector).forEach(markHidden);
    } catch {
      // Invalid selector — skip
    }
  });
}

export function hideEmbeddedJBrowseChrome(container: HTMLElement | null): void {
  hideJBrowseViewChrome(container);
  hideJBrowseMenuBar(container);
  hideJBrowseDrawers(container);
}
