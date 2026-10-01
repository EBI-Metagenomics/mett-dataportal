import { suppressJBrowseWidgets } from './suppressJBrowseWidgets';

describe('suppressJBrowseWidgets', () => {
  it('clears active widgets when they are already present', () => {
    const hideAllWidgets = jest.fn();
    const session = {
      activeWidgets: { size: 2 },
      hideAllWidgets,
    };

    const dispose = suppressJBrowseWidgets(session);
    expect(hideAllWidgets).toHaveBeenCalledTimes(1);
    dispose?.();
  });

  it('returns undefined when session has no hideAllWidgets', () => {
    expect(suppressJBrowseWidgets(null)).toBeUndefined();
    expect(suppressJBrowseWidgets({})).toBeUndefined();
  });
});
