/** JBrowse app-core ViewHeader / ViewMenu test ids. */
export const HIDDEN_JBROWSE_VIEW_CONTROL_TEST_IDS = [
  'view_menu_icon',
  'close_view',
  'minimize_view',
  'track_menu_icon',
] as const;

/** Selectors for JBrowse drawers / feature-detail chrome we suppress in embed mode. */
export const JBROWSE_DRAWER_SELECTORS = [
  '.MuiDrawer-root',
  '.MuiDrawer-modal',
  '.MuiDrawer-paper',
  '.MuiDrawer-docked',
  '[class*="MuiDrawer"]',
  'div[class^="MuiDrawer"]',
  'aside[class*="MuiDrawer"]',
  '[class*="BaseFeatureDetail"]',
  '[class*="FeatureDetails"]',
  '[class*="featureDetails"]',
  '[class*="DrawerWidget"]',
  '[class*="FeatureWidget"]',
  '.MuiBackdrop-root',
  '[class*="MuiBackdrop"]',
  '[role="presentation"]',
  '[aria-label*="drawer"]',
  '[aria-label*="Drawer"]',
  '[class*="MuiPaper-root"]:has([class*="BaseFeature"])',
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
  const roots = container
    ? [container]
    : [document.body];

  for (const root of roots) {
    root.querySelectorAll('.MuiAppBar-root').forEach(markHidden);
    // Floating action button (drawer / help) also belongs to app shell
    root.querySelectorAll('.MuiFab-root').forEach(markHidden);
  }
}

export function hideJBrowseDrawers(): void {
  JBROWSE_DRAWER_SELECTORS.forEach(selector => {
    try {
      document.querySelectorAll(selector).forEach(markHidden);
    } catch {
      // Invalid selector — skip
    }
  });
}

export function hideEmbeddedJBrowseChrome(container: HTMLElement | null): void {
  hideJBrowseViewChrome(container);
  hideJBrowseMenuBar(container);
  hideJBrowseDrawers();
}
