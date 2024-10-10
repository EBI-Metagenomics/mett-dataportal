import React from 'react';

const Header: React.FC = () => {
  return (
    <header>
      <section
        className="vf-hero vf-hero--800 vf-hero--search vf-u-fullbleed"
        style={{
          '--vf-hero--bg-image': "url('https://acxngcvroo.cloudimg.io/v7/https://www.embl.org/files/wp-content/uploads/microbial-ecosystems-l.jpg')",
        } as React.CSSProperties}
      >
        <div className="vf-hero__content | vf-box | vf-stack vf-stack--400">
          <h2 className="vf-hero__heading">Microbial Ecosystems TT - Data Portal</h2>
          <p className="vf-hero__subheading">
            Microbial Ecosystems transversal theme - a part of the EMBL Programme "Molecules to Ecosystems”.
          </p>
          <div className="vf-card__heading">
            <a className="vf-card__link" href="embl.org/editorhub/wp-content/uploads/2023/11/research-plans-embl-programme-2022-2026.pdf" target="_blank">
              Microbial Ecosystems Transversal Themes
              <svg
                aria-hidden="true"
                className="vf-card__heading__icon | vf-icon vf-icon-arrow--inline-end"
                width="1em"
                height="1em"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                  fill="currentColor"
                  fillRule="nonzero"
                />
              </svg>
            </a>
          </div>
        </div>
      </section>
    </header>
  );
};

export default Header;
