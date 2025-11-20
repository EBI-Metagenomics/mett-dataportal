"""
HTML templates for Swagger UI page customization.
These templates are injected by SwaggerHeaderFooterMiddleware to add
Data Portal header, footer, and breadcrumb navigation.
"""

# Header HTML (EBI global header + Data Portal hero)
HEADER_HTML = """    <!-- EBI Global Header -->
    <header id="masthead-black-bar" class="clearfix masthead-black-bar | ebi-header-footer vf-content vf-u-fullbleed"></header>
    <link rel="import" href="https://www.embl.org/api/v1/pattern.html?filter-content-type=article&filter-id=6682&pattern=node-body&source=contenthub" data-target="self" data-embl-js-content-hub-loader>
    
    <!-- Data Portal Header -->
    <header>
        <section class="vf-hero vf-hero--800 vf-hero--search vf-u-fullbleed" style="--vf-hero--bg-image: url('https://acxngcvroo.cloudimg.io/v7/https://www.embl.org/files/wp-content/uploads/microbial-ecosystems-l.jpg');">
            <div class="vf-hero__container" style="display: flex; justify-content: flex-start; padding: 0 1rem; max-width: 80em; margin: 0 auto;">
                <div class="vf-hero__content | vf-box | vf-stack vf-stack--400" style="max-width: 55em; width: 100%; z-index: 1;">
                    <h2 class="vf-hero__heading" style="max-width: 50ch;">Microbial Ecosystems Transversal Themes</h2>
                    <p class="vf-hero__subheading">
                        Transversal Themes Data Portal - a part of the EMBL Programme "Molecules to Ecosystems".
                    </p>
                    <div class="vf-card__heading">
                        <a class="vf-card__link" href="https://www.embl.org/about/programme/research-plans/microbial-ecosystems/" target="_blank" rel="noopener noreferrer">
                            Microbial Ecosystems Transversal Themes
                            <svg aria-hidden="true" class="vf-card__heading__icon | vf-icon vf-icon-arrow--inline-end" width="1em" height="1em" xmlns="http://www.w3.org/2000/svg">
                                <path d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z" fill="currentColor" fill-rule="nonzero"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
        </section>
    </header>
"""

# Footer HTML
FOOTER_HTML = """    <!-- Data Portal Footer -->
    <footer class="vf-footer" data-vf-google-analytics-region="embl-footer">
        <div class="vf-footer__inner">
            <p class="vf-footer__notice">
                <a class="vf-footer__link" href="//www.ebi.ac.uk/about/our-impact">
                    EMBL-EBI is the home for big data in biology. We help scientists
                    exploit complex information to make discoveries that benefit
                    humankind.
                </a>
            </p>
            <div class="vf-footer__links-group | vf-grid">
                <div class="vf-links">
                    <h4 class="vf-links__heading">
                        <a class="vf-heading__link" href="//www.ebi.ac.uk/services">Services</a>
                    </h4>
                    <ul class="vf-links__list | vf-list">
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/services" class="vf-list__link">By topic</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/services/all" class="vf-list__link">By name (A-Z)</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/support" class="vf-list__link">Help &amp; Support</a></li>
                    </ul>
                </div>
                <div class="vf-links">
                    <h4 class="vf-links__heading">
                        <a class="vf-heading__link" href="//www.ebi.ac.uk/research">Research</a>
                    </h4>
                    <ul class="vf-links__list | vf-list">
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/research/publications" class="vf-list__link">Publications</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/research/groups" class="vf-list__link">Research groups</a></li>
                        <li class="vf-list__item vf-footer__notice">
                            <a href="//www.ebi.ac.uk/research/postdocs" class="vf-list__link">Postdocs</a>
                            &amp;
                            <a href="//www.ebi.ac.uk/research/eipp" class="vf-list__link">PhDs</a>
                        </li>
                    </ul>
                </div>
                <div class="vf-links">
                    <h4 class="vf-links__heading">
                        <a class="vf-heading__link" href="//www.ebi.ac.uk/training">Training</a>
                    </h4>
                    <ul class="vf-links__list | vf-list">
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/training/live-events" class="vf-list__link">Live training</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/training/on-demand" class="vf-list__link">On-demand training</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/training/trainer-support" class="vf-list__link">Support for trainers</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/training/contact-us" class="vf-list__link">Contact organisers</a></li>
                    </ul>
                </div>
                <div class="vf-links">
                    <h4 class="vf-links__heading">
                        <a class="vf-heading__link" href="//www.ebi.ac.uk/industry">Industry</a>
                    </h4>
                    <ul class="vf-links__list | vf-list">
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/industry/private" class="vf-list__link">Members Area</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/industry/workshops" class="vf-list__link">Workshops</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/industry/sme-forum" class="vf-list__link">SME Forum</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/industry/contact" class="vf-list__link">Contact Industry programme</a></li>
                    </ul>
                </div>
                <div class="vf-links">
                    <h4 class="vf-links__heading">
                        <a class="vf-heading__link" href="//www.ebi.ac.uk/about">About</a>
                    </h4>
                    <ul class="vf-links__list | vf-list">
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/about/contact" class="vf-list__link">Contact us</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/about/events" class="vf-list__link">Events</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/about/jobs" class="vf-list__link">Jobs</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/about/news" class="vf-list__link">News</a></li>
                        <li class="vf-list__item"><a href="//www.ebi.ac.uk/about/people" class="vf-list__link">People &amp; groups</a></li>
                        <li class="vf-list__item"><a href="//intranet.ebi.ac.uk" class="vf-list__link">Intranet for staff</a></li>
                    </ul>
                </div>
            </div>
            <p class="vf-footer__legal">
                <span class="vf-footer__legal-text">
                    <a class="vf-footer__link" href="https://www.google.co.uk/maps/place/Hinxton,+Saffron+Walden+CB10+1SD/@52.0815334,0.1891518,17z/data=!3m1!4b1!4m5!3m4!1s0x47d87ccbfbd2538b:0x7bbdb4cde2779ff3!8m2!3d52.0800838!4d0.186415">
                        EMBL-EBI, Wellcome Genome Campus, Hinxton, Cambridgeshire, CB10 1SD, UK.
                    </a>
                </span>
                <span class="vf-footer__legal-text">
                    <a class="vf-footer__link" href="tel:00441223494444">Tel: +44 (0)1223 49 44 44</a>
                </span>
                <span class="vf-footer__legal-text">
                    <a class="vf-footer__link" href="//www.ebi.ac.uk/about/contact">Full contact details</a>
                </span>
            </p>
            <p class="vf-footer__legal">
                <span class="vf-footer__legal-text">Copyright © EMBL 2021</span>
                <span class="vf-footer__legal-text">
                    EMBL-EBI is part of the
                    <a class="vf-footer__link" href="//www.embl.org">European Molecular Biology Laboratory</a>
                </span>
                <span class="vf-footer__legal-text">
                    <a class="vf-footer__link" href="//www.ebi.ac.uk/about/terms-of-use">Terms of use</a>
                </span>
            </p>
        </div>
    </footer>
"""

# CSS and JS for header/footer
HEADER_CSS_JS = """    <!-- Visual Framework CSS -->
    <link rel="stylesheet" href="https://assets.emblstatic.net/vf/v2.5.7/css/styles.css"/>
    <link rel="stylesheet" href="https://assets.emblstatic.net/vf/v2/assets/ebi-header-footer/ebi-header-footer.css" type="text/css" media="all"/>
    
    <!-- EBI Icons -->
    <link rel="stylesheet" href="//ebi.emblstatic.net/web_guidelines/EBI-Icon-fonts/v1.3/fonts.css" type="text/css" media="all"/>
    
    <!-- EBI Header/Footer Script -->
    <script defer="defer" src="//ebi.emblstatic.net/web_guidelines/EBI-Framework/v1.4/js/script.js"></script>
    
    <!-- Custom styles to remove white space and style breadcrumbs -->
    <style>
        body {
            margin: 0 !important;
            padding: 0 !important;
        }
        .swagger-breadcrumb {
            background-color: #ffffff;
            padding: 12px 0;
            border-bottom: 1px solid #e0e0e0;
            max-width: 1460px;
            margin: 0 auto;
        }
        .swagger-breadcrumb .vf-breadcrumbs__list {
            margin: 0 !important;
            padding: 0 24px !important;
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            list-style: none !important;
        }
        .swagger-breadcrumb .vf-breadcrumbs__list li {
            display: inline-block !important;
            margin-right: 0 !important;
        }
        .swagger-breadcrumb .vf-breadcrumbs__list span {
            color: #666;
            margin: 0 0.25rem;
            display: inline-block !important;
        }
    </style>
"""

# Breadcrumb HTML for Swagger page
BREADCRUMB_HTML = """    <!-- Breadcrumb Navigation -->
    <nav class="swagger-breadcrumb vf-breadcrumbs" aria-label="Breadcrumb">
        <ul class="vf-breadcrumbs__list vf-list vf-list--inline">
            <li><a href="/" class="vf-breadcrumbs__link">Home</a></li>
            <span> | </span>
            <li><b>API Docs</b></li>
        </ul>
    </nav>
"""
