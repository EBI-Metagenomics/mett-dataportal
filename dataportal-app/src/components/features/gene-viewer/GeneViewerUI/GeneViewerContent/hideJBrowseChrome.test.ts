import { hideJBrowseMenuBar, hideJBrowseViewChrome } from './hideJBrowseChrome';

describe('hideJBrowseChrome', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('hides MuiAppBar menu bar inside the embed container', () => {
    const container = document.createElement('div');
    const appBar = document.createElement('header');
    appBar.className = 'MuiAppBar-root';
    appBar.textContent = 'FILE ADD TOOLS HELP';
    container.appendChild(appBar);
    document.body.appendChild(container);

    hideJBrowseMenuBar(container);

    expect(appBar.classList.contains('jbrowse-embed-hidden')).toBe(true);
    expect(appBar.getAttribute('aria-hidden')).toBe('true');
  });

  it('hides track context menu icons', () => {
    const container = document.createElement('div');
    const trackMenu = document.createElement('button');
    trackMenu.setAttribute('data-testid', 'track_menu_icon');
    container.appendChild(trackMenu);
    document.body.appendChild(container);

    hideJBrowseViewChrome(container);

    expect(trackMenu.classList.contains('jbrowse-embed-hidden')).toBe(true);
  });
});
