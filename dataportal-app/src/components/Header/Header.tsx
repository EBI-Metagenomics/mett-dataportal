import React from 'react';

const Header: React.FC = () => {
    return (
        <div>
            <header>
                <meta charSet="UTF-8"/>
                <meta name="description" content="ME TT Data Portal"/>
                <meta name="keywords"
                      content="METT, Transversal Themes, DataPortal, Phocaeicola vulgatus, Bacteroides uniformis"/>
                <title>DataPortal Data Portal</title>
                <link rel="preconnect" href="https://fonts.googleapis.com"/>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/>
                <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans&display=swap" rel="stylesheet"/>
                <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&display=swap" rel="stylesheet"/>
                <link rel="stylesheet" href="https://assets.emblstatic.net/vf/v2.5.7/css/styles.css"/>
            </header>

            <section
                className="vf-hero vf-hero--800 vf-hero--search vf-u-fullbleed"
                style={{
                    '--vf-hero--bg-image': "url('https://acxngcvroo.cloudimg.io/v7/https://www.embl.org/files/wp-content/uploads/microbial-ecosystems-l.jpg')",
                } as React.CSSProperties} // Cast to React.CSSProperties to avoid TypeScript errors
            >

                <div className="vf-hero__content | vf-box | vf-stack vf-stack--400"><p className="vf-hero__kicker">
                </p>
                    <h2 className="vf-hero__heading">Microbial Ecosystems TT - Data Portal</h2>
                    <p className="vf-hero__subheading">Microbial Ecosystems transversal theme - a part of the EMBL
                        Programme
                        "Molecules
                        to Ecosystems”.</p>
                    <div className="vf-card__heading"><a className="vf-card__link" href="JavaScript:Void(0);">Optional
                        call
                        to
                        action
                        link
                        <svg aria-hidden="true" className="vf-card__heading__icon | vf-icon vf-icon-arrow--inline-end"
                             width="1em" height="1em" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                                fill="currentColor" fill-rule="nonzero"></path>
                        </svg>
                    </a></div>
                </div>
            </section>
        </div>
    );
};

export default Header;
