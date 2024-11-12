import React from 'react';

const Footer: React.FC = () => {
    return (
        <footer className="vf-footer">
            <div className="vf-footer__inner">

                <p className="vf-footer__notice">ME TT Data Portal is a flagship project of EMBL’s microbial ecosystems
                    transversal theme.</p>
                <section className="vf-footer__legal | vf-grid vf-grid__col-1">
                    <p className="vf-footer__legal-text">Copyright © EMBL-EBI</p>
                    <p className="vf-footer__legal-text">EMBL-EBI is part of the European Molecular Biology
                        Laboratory</p>
                    <a className="vf-footer__link" href="https://www.ebi.ac.uk/about/terms-of-use">Terms of use</a>
                </section>

            </div>
            <script src="https://assets.emblstatic.net/vf/v2.5.7/scripts/scripts.js"></script>
        </footer>
    )
        ;
};

export default Footer;
