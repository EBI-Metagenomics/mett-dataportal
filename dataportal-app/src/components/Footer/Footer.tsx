// Footer.tsx
import React from 'react';

const Footer: React.FC = () => {
    return (
        <footer className="vf-footer">
            <div className="vf-footer__inner">

                <div className="vf-flag vf-flag--middle vf-flag--400 space-below-20">
                    <div className="vf-flag__media">
                        <img src="/img/eu-flag.svg"
                             width="100px"
                             alt="EU Flag"
                             height="67px"/>
                    </div>
                    <div className="vf-flag__body">
                        <p className="vf-footer__notice">
                            This project has received funding from the European Union’s Horizon
                            2020 research and innovation programme under grant agreement No 817729
                        </p>
                    </div>
                </div>
                <div className="vf-footer__links-group | vf-grid">
                    <div className="vf-links">
                        <h4 className="vf-links__heading">The project</h4>
                        <ul className="vf-links__list | vf-list">
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="https://www.dataportal.eu">DataPortal project
                                    site</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="{% url 'admin:index' %}">Admin login</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="{{ DOCS_URL }}/publications.html">DataPortal
                                    publications</a>
                            </li>
                        </ul>
                    </div>
                    <div className="vf-links">
                        <h4 className="vf-links__heading">Help</h4>
                        <ul className="vf-links__list | vf-list">
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="{{ DOCS_URL }}">Documentation</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="mailto:dataportal-help@ebi.ac.uk">Helpdesk</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link" href="https://dataportal.cronitorstatus.com">Status
                                    page</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://github.com/ebi-metagenomics/dataportal-database">Data
                                    portal codebase</a>
                            </li>
                        </ul>
                    </div>
                    <div className="vf-links">
                        <h4 className="vf-links__heading">Data repositories</h4>
                        <ul className="vf-links__list | vf-list">
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://www.ebi.ac.uk/ena/browser/view/PRJEB43192">ENA</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://www.ebi.ac.uk/biosamples/samples?filter=attr%3Aproject%3Adataportal">Biosamples</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://www.ebi.ac.uk/metabolights/">Metabolights</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://www.ebi.ac.uk/metagenomics/super-studies/dataportal">MGnify</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://workflowhub.eu/programmes/28">WorkflowHub</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://workflowhub.eu/programmes/28">WorkflowHub</a>
                            </li>
                            <li className="vf-list__item">
                                <a className="vf-list__link"
                                   href="https://ftp.ebi.ac.uk/pub/databases/metagenomics/dataportal_data/">Data
                                    portal DB
                                    snapshots</a>
                            </li>
                        </ul>
                    </div>
                </div>
                <section className="vf-footer__legal | vf-grid vf-grid__col-1">
                    <ul className="vf-footer__list vf-footer__list--legal | vf-list vf-list--inline">
                        <li className="vf-list__item">
                            <a href="https://www.dataportal.eu/data-policy" className="vf-list__link">Privacy
                                policy</a>
                        </li>

                        <li className="vf-footer__legal-text">Data Portal technical support: <a
                            className="vf-list__link"
                            href="mailto:dataportal-help@ebi.ac.uk">dataportal-help@ebi.ac.uk</a>
                        </li>
                    </ul>
                </section>
                <div data-vf-js-banner-cookie-name="emblContentHub27360"
                     className="vf-banner vf-banner--fixed vf-banner--bottom vf-banner--notice"
                     data-vf-js-banner="true"
                     data-vf-js-banner-cookie-version="224467"
                     data-vf-js-banner-state="dismissible"
                     data-vf-js-banner-button-text="I agree">
                    <div className="vf-banner__content | vf-grid" data-vf-js-banner-text="">
                        <p className="vf-text vf-text-body--2"> This website uses cookies to function.
                            By using the site you are agreeing to this as outlined in our
                            <a className="vf-banner__link" href="https://www.embl.org/info/privacy-policy/">Privacy
                                Policy</a>.
                        </p>
                    </div>
                </div>
            </div>
            <script src="https://assets.emblstatic.net/vf/v2.5.7/scripts/scripts.js"></script>
        </footer>
    )
        ;
};

export default Footer;
