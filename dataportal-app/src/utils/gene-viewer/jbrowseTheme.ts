/** JBrowse embedded theme palette (METT brand). */
export const JBROWSE_THEME = {
  palette: {
    primary: {
      main: '#0D233F',
    },
    secondary: {
      main: '#721E63',
      // Unfocused LGV view-header (MUI darken(main, 0.3)).
      dark: '#4F1545',
    },
  },
} as const;

/**
 * Shared header strip for Feature Details panel.
 * Matches the *focused* JBrowse LGV header (secondary.main) — the state
 * when users interact with tracks and populate the feature panel.
 */
export const GENE_VIEWER_HEADER_COLOR =
  JBROWSE_THEME.palette.secondary.main;

/** Slightly darker edge under the shared header strip. */
export const GENE_VIEWER_HEADER_BORDER_COLOR = '#511446';
