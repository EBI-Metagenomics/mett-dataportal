/**
 * Constants for the Feature Panel UI.
 *
 * The Feature Panel groups gene information into collapsible categories.
 * Section ordering, identifiers and default expansion state live here so
 * they can be tweaked without touching component logic.
 */

export type SectionId =
    | 'core'
    | 'location'
    | 'annotations'
    | 'ontology'
    | 'unifire'
    | 'specialized'
    | 'dbxref'
    | 'protein';

// Canonical render order for Feature Panel sections. Also used by the
// "Expand all" / "Collapse all" header control to know which sections to
// flip together.
export const ALL_SECTION_IDS: readonly SectionId[] = [
    'core',
    'location',
    'annotations',
    'ontology',
    'unifire',
    'specialized',
    'dbxref',
    'protein',
] as const;

// Default expansion state: only Core Details is expanded on initial render
// so the panel stays scannable. Users can open any other section on demand
// or use the "Expand all" control in the header.
export const DEFAULT_EXPANDED_SECTIONS: Record<SectionId, boolean> = {
    core: true,
    location: false,
    annotations: false,
    ontology: false,
    unifire: false,
    specialized: false,
    dbxref: false,
    protein: false,
};
