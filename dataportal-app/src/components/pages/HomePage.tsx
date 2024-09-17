import React, {useEffect, useState} from 'react';
import {fetchSpeciesList} from '../../services/speciesService';
import {fetchSearchResults} from '../../services/searchService';
import SearchForm from '../organisms/SearchForm';
import ResultsTable from '../organisms/ResultsTable';
import styles from "@components/pages/HomePage.module.scss";

const HomePage: React.FC = () => {
    const [results, setResults] = useState<any[]>([]);
    const [speciesList, setSpeciesList] = useState<any[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState('');
    const [selectedGenome, setSelectedGenome] = useState('');

    // Fetch species list on component mount
    useEffect(() => {
        const fetchSpecies = async () => {
            try {
                const species = await fetchSpeciesList();
                console.log('Species fetched:', species);
                setSpeciesList(species || []);
            } catch (error) {
                console.error('Error fetching species:', error);
            }
        };

        fetchSpecies();
    }, []);

    const handleSearch = async () => {
        try {
            const response = await fetchSearchResults(selectedSpecies, selectedGenome);
            setResults(response.results || []);
        } catch (error) {
            console.error('Error fetching search results:', error);
            setResults([]);
        }
    };

    const handleGenomeSelect = (id: string) => {
        setSelectedGenome(id);
    };

    const handleSpeciesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedSpecies(e.target.value);
    };

    return (
        <div>
            <section className="vf-grid vf-grid__col-3 | vf-card-container | vf-u-fullbleed">
                <div className="vf-section-header vf-grid__col--span-3">
                    <div className="vf-grid__col--span-2">
                        <div className={`vf-content ${styles.vfContent}`}> {}
                            <p>
                                The Microbial Ecosystems Transversal Theme, part of the EMBL Programme "Molecules to
                                Ecosystems", focuses on understanding the roles and interactions of microbes within
                                various ecosystems. It explores how microbial communities impact their environments and
                                aims to develop methods to modulate microbiomes for beneficial outcomes. The research
                                integrates disciplines like genomics, bioinformatics, and ecology, and includes projects
                                such as the MGnify data resource and the TREC expedition. The Flagship Project of METT
                                has focused efforts on annotating the genomes of <i>Phocaeicola Vulgatus</i> and <i>Bacteroides
                                uniformis</i>, two of the most prevalent and abundant bacterial species of the human
                                microbiome.
                            </p>
                        </div>
                        <div className={`vf-grid__col--span-3 ${styles.vfGridColSpan3}`}>
                            <article className="vf-card vf-card--brand vf-card--bordered">
                                <div className="vf-card__content | vf-stack vf-stack--400">
                                    <h3 className="vf-card__heading"><a className="vf-card__link"
                                                                        href="JavaScript:Void(0);">A Bordered Card
                                        Heading
                                        <svg aria-hidden="true"
                                             className="vf-card__heading__icon | vf-icon vf-icon-arrow--inline-end"
                                             width="1em" height="1em" xmlns="http://www.w3.org/2000/svg">
                                            <path
                                                d="M0 12c0 6.627 5.373 12 12 12s12-5.373 12-12S18.627 0 12 0C5.376.008.008 5.376 0 12zm13.707-5.209l4.5 4.5a1 1 0 010 1.414l-4.5 4.5a1 1 0 01-1.414-1.414l2.366-2.367a.25.25 0 00-.177-.424H6a1 1 0 010-2h8.482a.25.25 0 00.177-.427l-2.366-2.368a1 1 0 011.414-1.414z"
                                                fill="currentColor" fillRule="nonzero"></path>
                                            {/* Use fillRule instead of fill-rule */}
                                        </svg>
                                    </a></h3>
                                    <p className="vf-card__subheading">With sub–heading</p>
                                    <p className="vf-card__text">Lorem ipsum dolor sit amet, consectetur <a
                                        href="JavaScript:Void(0);"
                                        className="vf-card__link">adipisicing elit</a>. Sapiente harum, omnis provident
                                        saepe aut eius aliquam sequi fugit incidunt reiciendis, mollitia quos?</p>
                                </div>
                            </article>
                        </div>
                    </div>
                    <div>&nbsp;</div>
                    <hr className="vf-divider"></hr>
                </div>
            </section>
            {/* Species Dropdown */}
            <section className="vf-grid__col--span-2">
                <div>
                    <label className="vf-dropdown__label" htmlFor="species-select">Select Species: </label>
                    {/*<div className="vf-dropdown__label">Select Species:</div>*/}
                    <select id="species-select" value={selectedSpecies} onChange={handleSpeciesChange}>
                        <option value="">-- Select a Species --</option>
                        {speciesList.map(species => (
                            <option key={species.id} value={species.id}>
                                {species.scientific_name}
                            </option>
                        ))}
                    </select>
                </div>
                <div>&nbsp;</div>
            </section>

            <section className="vf-grid vf-grid__col-3">
                <SearchForm onSearch={handleSearch}/>
            </section>

            <section className="vf-grid vf-grid__col-3">
                <ResultsTable results={results} onGenomeSelect={handleGenomeSelect} selectedGenome={selectedGenome}/>
            </section>
        </div>
    );
};

export default HomePage;
