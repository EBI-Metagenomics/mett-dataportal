import React from 'react';
import {Link} from 'react-router-dom';
import styles from './HomePageHeadBand.module.scss';
import {GenomeMeta} from "../../../interfaces/Genome";
import SpeciesFilter from "@components/Filters/SpeciesFilter";
import {EBI_FTP_SERVER} from "../../../utils/appConstants";
import {useFeatureFlags} from '../../../hooks/useFeatureFlags';


interface HomePageHeadBandProps {
    typeStrains: GenomeMeta[];
    linkTemplate: string;
    speciesList: { acronym: string; scientific_name: string, common_name: string, taxonomy_id: number }[];
    selectedSpecies: string[];
    handleSpeciesSelect: (species_acronym: string) => Promise<void>;

}

const HomePageHeadBand: React.FC<HomePageHeadBandProps> = ({
                                                               typeStrains,
                                                               linkTemplate,
                                                               speciesList,
                                                               selectedSpecies,
                                                               handleSpeciesSelect
                                                           }) => {
    const generateLink = (strainName: string) => linkTemplate.replace('$strain_name', strainName);
    const {isFeatureEnabled} = useFeatureFlags();

    // console.log(typeStrains)

    return (
        <section className="vf-grid vf-grid__col-3 | vf-card-container | vf-u-fullbleed">
            <div className="vf-section-header vf-grid__col--span-3">
                <div className="vf-grid__col--span-2">
                    <div className={`vf-content ${styles.vfContent}`} style={{textAlign: 'justify'}}>

                        {/* Yellow Band - Feedback Link Section */}
                        {isFeatureEnabled('feedback') && (
                            <div
                                style={{
                                    backgroundColor: '#fff3cd',
                                    border: '1px solid #ffeaa7',
                                    borderRadius: '4px',
                                    padding: '0.75rem 1rem',
                                    margin: '1rem 0',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    fontSize: '1rem',
                                    gap: '1rem',
                                }}
                            >
                                <span style={{color: '#333', fontWeight: '500'}}>
                                    We value your feedback! Help us improve by sharing your thoughts.
                                </span>
                                <a
                                    href="https://www.ebi.ac.uk/about/contact/support/mett-feedback"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="vf-link"
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        color: '#005ea5',
                                        textDecoration: 'none',
                                        transition: 'color 0.2s ease',
                                        gap: '0.5rem',
                                        lineHeight: '1',
                                        overflow: 'visible',
                                        fontSize: '0.9rem',
                                        fontWeight: '500',
                                    }}
                                >
                                    Feedback
                                    <svg
                                        aria-hidden="true"
                                        className="vf-icon vf-icon-arrow--inline-end"
                                        style={{
                                            display: 'inline-block',
                                            width: '1.2em',
                                            height: '1.2em',
                                            flexShrink: '0',
                                        }}
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle cx="12" cy="12" r="11" fill="currentColor"/>
                                        <path
                                            d="M8.5 7.5l7 4.5-7 4.5v-9z"
                                            fill="white"
                                            fillRule="nonzero"
                                        />
                                    </svg>
                                </a>
                            </div>
                        )}

                        {/* Yellow Band - Natural Search Query */}
                        {isFeatureEnabled('natural_query') && (
                            <div
                                style={{
                                    backgroundColor: '#fff3cd',
                                    border: '1px solid #ffeaa7',
                                    borderRadius: '4px',
                                    padding: '0.75rem 1rem',
                                    margin: '1rem 0',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    fontSize: '1rem',
                                    gap: '1rem',
                                }}
                            >
                                <span style={{color: '#333', fontWeight: '500'}}>
                                    Simple POC to demonstrate the Natural Search Query
                                </span>
                                <a
                                    href="/natural-query"
                                    className="vf-link"
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        color: '#005ea5',
                                        textDecoration: 'none',
                                        transition: 'color 0.2s ease',
                                        gap: '0.4rem',
                                        lineHeight: '1',
                                        overflow: 'visible',
                                    }}
                                >Natural Search Query
                                    <svg
                                        aria-hidden="true"
                                        className="vf-icon vf-icon-arrow--inline-end"
                                        style={{
                                            verticalAlign: 'middle',
                                            display: 'block',
                                            overflow: 'visible',
                                        }}
                                        width="1.3em"
                                        height="1.3em"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                                            fill="currentColor"
                                            fillRule="nonzero"
                                        ></path>
                                    </svg>
                                </a>


                            </div>
                        )}

                        <p>
                            The transversal theme aims at mechanistically understanding the complex role that
                            human-associated
                            microbiomes play in human health and disease. Our current knowledge of bacterial gene
                            functions
                            come primarily from very few model bacteria, failing to capture the genetic diversity
                            within the gut microbiome. One of the goals of METT is to systematically tackle the vast
                            genetic matter in the gut microbiome and two establish new model microbes.
                            The Flagship Project of METT has focused efforts on annotating the genomes of
                            <i>B. uniformis (ATCC8492)</i> and <i>P. vulgatus (ATCC8482)</i>, two of the most prevalent
                            and abundant bacterial species of the human microbiome.
                        </p>
                        <p>
                            The current version is a web-based <i>Data Portal</i> platform designed to
                            browse the genomes of the the type strains
                            <i>B. uniformis (ATCC8492)</i> and <i>P. vulgatus (ATCC8482)</i>.
                            The annotation data generated by the ME TT has been organised on the&nbsp;
                            <a href={EBI_FTP_SERVER} target="_blank" rel="noopener noreferrer">FTP Server</a>
                            &nbsp;hosted at EBI and contains structural annotations (such as Prokka and Mobilome
                            predictions, etc) as well as functional annotations (including biosynthetic gene clusters,
                            carbohydrate active enzymes, etc).
                        </p>


                    </div>
                </div>
                <div>&nbsp;</div>
                <hr className="vf-divider"></hr>
            </div>

            {/* Type Strains Section */}
            <div
                className="vf-section-header vf-grid__col--span-3 | vf-u-fullbleed"
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '1.1rem',
                    padding: '0.5rem 0',
                    gap: '1rem',
                }}
            >
                <h3
                    className="vf-section-header__heading"
                    style={{
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        margin: '0',
                    }}
                >
                    Browse Type Strains:
                </h3>
                <div
                    style={{
                        display: 'flex',
                        gap: '1.5rem',
                        alignItems: 'center',
                    }}
                >
                    {typeStrains.map((strain) => (
                        <a
                            key={strain.isolate_name}
                            href={generateLink(strain.isolate_name)}
                            className="vf-link"
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                color: '#005ea5',
                                textDecoration: 'none',
                                transition: 'color 0.2s ease',
                                gap: '0.4rem',
                                lineHeight: '1',
                                overflow: 'visible',
                            }}
                        >
                            {strain.isolate_name}
                            <svg
                                aria-hidden="true"
                                className="vf-icon vf-icon-arrow--inline-end"
                                style={{
                                    verticalAlign: 'middle',
                                    display: 'block',
                                    overflow: 'visible',
                                }}
                                width="1.3em"
                                height="1.3em"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                                    fill="currentColor"
                                    fillRule="nonzero"
                                ></path>
                            </svg>
                        </a>
                    ))}
                </div>


            </div>


            <div
                className="vf-section-header vf-grid__col--span-3 | vf-u-fullbleed"
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '1.1rem',
                    padding: '0.2rem 0',
                    gap: '1rem',
                }}
            >
                <h3
                    className="vf-section-header__heading"
                    style={{
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        margin: '0',
                    }}
                >
                    Species:
                </h3>
                {/* Species Filter */}
                <SpeciesFilter
                    speciesList={speciesList}
                    selectedSpecies={selectedSpecies}
                    onSpeciesSelect={handleSpeciesSelect}
                />

            </div>
        </section>
    );
};

export default HomePageHeadBand; 