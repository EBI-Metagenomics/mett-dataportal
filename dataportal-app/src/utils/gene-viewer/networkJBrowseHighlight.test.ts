import { VIEWPORT_SYNC_CONSTANTS } from './viewportSyncConstants';
import {
  anchorInteractionLocusTags,
  clearNetworkJBrowseHighlight,
  geneColorForNetworkHighlight,
  publishNetworkJBrowseHighlight,
  refreshJBrowseGeneColors,
} from './networkJBrowseHighlight';

const essentiality = '#555555';

describe('anchorInteractionLocusTags', () => {
  const nodes = [
    { id: 'anchor', locus_tag: 'BU_ANCHOR' },
    { id: 'partner', locus_tag: 'BU_PARTNER' },
    { id: 'ortholog', locus_tag: 'PV_ORTHOLOG' },
    { id: 'expanded', locus_tag: 'BU_EXPANDED' },
  ];

  it('keeps direct interaction partners and skips ortholog-only links', () => {
    const tags = anchorInteractionLocusTags(
      nodes,
      [
        { source: 'anchor', target: 'partner' },
        { source: 'anchor', target: 'ortholog', edgeType: 'ortholog' },
        { source: 'partner', target: 'expanded' },
      ],
      'anchor',
    );
    expect(tags).toEqual(['BU_PARTNER']);
  });

  it('resolves the anchor by locus tag and ignores a missing anchor', () => {
    expect(
      anchorInteractionLocusTags(nodes, [{ source: 'BU_ANCHOR', target: 'partner' }], 'BU_ANCHOR'),
    ).toEqual([]);
    expect(anchorInteractionLocusTags(nodes, [{ source: 'anchor', target: 'partner' }], 'BU_ANCHOR')).toEqual([
      'BU_PARTNER',
    ]);
    expect(anchorInteractionLocusTags(nodes, [{ source: 'anchor', target: 'partner' }], null)).toEqual([]);
  });
});

describe('geneColorForNetworkHighlight', () => {
  const partners = new Set(['BU_PARTNER']);

  it('uses hover, then the existing selected-gene blue, then interaction violet', () => {
    expect(
      geneColorForNetworkHighlight({
        locusTag: 'BU_PARTNER',
        selectedGeneId: 'BU_ANCHOR',
        hoverLocusTag: 'BU_PARTNER',
        interactionLocusTags: partners,
        essentialityColor: essentiality,
      }),
    ).toBe(VIEWPORT_SYNC_CONSTANTS.NETWORK_HOVER_HIGHLIGHT_COLOR);

    expect(
      geneColorForNetworkHighlight({
        locusTag: 'BU_ANCHOR',
        selectedGeneId: 'BU_ANCHOR',
        hoverLocusTag: null,
        interactionLocusTags: partners,
        essentialityColor: essentiality,
      }),
    ).toBe(VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_COLOR);

    expect(
      geneColorForNetworkHighlight({
        locusTag: 'BU_PARTNER',
        selectedGeneId: 'BU_ANCHOR',
        hoverLocusTag: null,
        interactionLocusTags: partners,
        essentialityColor: essentiality,
      }),
    ).toBe(VIEWPORT_SYNC_CONSTANTS.NETWORK_INTERACTION_HIGHLIGHT_COLOR);

    expect(
      geneColorForNetworkHighlight({
        locusTag: 'BU_OTHER',
        selectedGeneId: 'BU_ANCHOR',
        essentialityColor: essentiality,
      }),
    ).toBe(essentiality);
  });
});

describe('publishNetworkJBrowseHighlight', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    clearNetworkJBrowseHighlight();
  });

  afterEach(() => {
    clearNetworkJBrowseHighlight();
    jest.useRealTimers();
  });

  it('reloads JBrowse displays once when the highlight set changes', () => {
    const reload = jest.fn();
    const viewState = { session: { views: [{ tracks: [{ displays: [{ reload }] }] }] } };

    publishNetworkJBrowseHighlight(
      { interactionLocusTags: ['BU_PARTNER'], hoverLocusTag: null },
      viewState,
    );
    publishNetworkJBrowseHighlight(
      { interactionLocusTags: ['BU_PARTNER'], hoverLocusTag: null },
      viewState,
    );
    expect(reload).not.toHaveBeenCalled();

    jest.advanceTimersByTime(50);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('refreshes again when a view becomes available for the same genes', () => {
    const reload = jest.fn();
    publishNetworkJBrowseHighlight({ interactionLocusTags: ['BU_PARTNER'] }, null);
    jest.advanceTimersByTime(50);

    publishNetworkJBrowseHighlight(
      { interactionLocusTags: ['BU_PARTNER'] },
      { session: { views: [{ tracks: [{ displays: [{ reload }] }] }] } },
    );
    jest.advanceTimersByTime(50);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('reloads displays directly', () => {
    const reload = jest.fn();
    const setError = jest.fn();
    refreshJBrowseGeneColors({
      session: { views: [{ tracks: [{ displays: [{ reload }, { setError }] }] }] },
    });
    expect(reload).toHaveBeenCalledTimes(1);
    expect(setError).toHaveBeenCalledWith(undefined);
  });
});
