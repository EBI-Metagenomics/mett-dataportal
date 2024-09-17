import React, {useCallback, useEffect, useState} from 'react';
import {fetchSpeciesList} from '../../services/speciesService';
import ResultsTable from '../organisms/ResultsTable';
import styles from "@components/pages/HomePage.module.scss";
import {fetchFuzzyIsolateSearch, fetchSearchResults} from "../../services/searchService";
import {extractIsolateName} from "../../utils/utils";

const HomePage: React.FC = () => {
    const [results, setResults] = useState<any[]>([]);
    const [speciesList, setSpeciesList] = useState<any[]>([]);
    const [isolateList, setIsolateList] = useState<any[]>([]);
    const [isolateName, setIsolateName] = useState<string>('');
    const [selectedSpecies, setSelectedSpecies] = useState('');
    const [searchQuery, setSearchQuery] = useState(''); // For isolate input
    const [isTyping, setIsTyping] = useState(false);

    // Fetch species list on component mount
    useEffect(() => {
        const fetchSpecies = async () => {
            try {
                const species = await fetchSpeciesList();
                setSpeciesList(species || []);
            } catch (error) {
                console.error('Error fetching species:', error);
            }
        };

        fetchSpecies();
    }, []);

    // Debounce hook to delay search requests
    const debounce = (func: Function, delay: number) => {
        let timeoutId: NodeJS.Timeout;
        return (...args: any[]) => {
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func(...args), delay);
        };
    };

    const performFuzzySearch = async (query: string) => {
        if (query.length < 2) return; // Don't search for very short queries
        try {
            const isolates = await fetchFuzzyIsolateSearch(query, selectedSpecies); // API for fuzzy search
            setIsolateList(isolates || []);
        } catch (error) {
            console.error('Error fetching isolates:', error);
            setIsolateList([]);
        }
    };

    // Debounced version of the search function
    const debouncedSearch = useCallback(debounce(performFuzzySearch, 500), [selectedSpecies]);

    // Handle isolate search input
    const handleIsolateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);
        setIsolateName('');
        setIsTyping(true);
        debouncedSearch(query); // Trigger the debounced fuzzy search
    };

    const handleIsolateSelect = (isolate: string) => {
        setSearchQuery(isolate);
        setIsolateName(extractIsolateName(isolate));
        setIsTyping(false); // Hide autocomplete once an isolate is selected
    };

    const handleSearch = async () => {
        try {
            const response = await fetchSearchResults(searchQuery, selectedSpecies);
            setResults(response.results || []);
        } catch (error) {
            console.error('Error fetching search results:', error);
            setResults([]);
        }
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

            <section className="vf-grid__col--span-2">
                <div className={`vf-grid__col--span-3 ${styles.searchContainer}`}>
                    <h2 className="vf-section-header__subheading">Search Genome</h2>
                    <form onSubmit={handleSearch}
                          className="vf-form vf-form--search vf-form--search--responsive">
                        {/* Flexbox container for aligning components horizontally */}
                        <div className={`vf-form__item ${styles.searchElements}`}>
                            {/* Species Dropdown */}
                            <select id="species-select" value={selectedSpecies}
                                    className={`vf-dropdown ${styles.selectDropDown}`}
                                    onChange={e => setSelectedSpecies(e.target.value)}>
                                <option value="">-- Select a Species --</option>
                                {speciesList.map(species => (
                                    <option key={species.id} value={species.id}>
                                        {species.scientific_name}
                                    </option>
                                ))}
                            </select>

                            {/* Search Isolate Input */}
                            <div className="vf-form__item">
                                <input
                                    className={`vf-form__input ${styles.vfFormInput}`}
                                    value={searchQuery}
                                    onChange={handleIsolateChange}
                                    placeholder="Search..."
                                    autoComplete="off"
                                    aria-autocomplete="list"
                                    aria-controls="suggestions"
                                    role="combobox"
                                    aria-expanded={isolateList.length > 0}
                                />
                                <input type="hidden" name="isolate-name" value={isolateName}/>

                                {isTyping && isolateList.length > 0 && (
                                    <div id="suggestions" className={`vf-dropdown__menu ${styles.vfDropdown__menu}`}
                                         role="listbox">
                                        {isolateList.map((suggestion, index) => (
                                            <div
                                                key={index}
                                                className={`${styles.suggestionItem}`}
                                                onClick={() => handleIsolateSelect(suggestion)}
                                                role="option"
                                            >
                                                {suggestion}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            {/* Search Button */}
                            <button className={`vf-button vf-button--primary ${styles.searchButton}`}>Search
                            </button>
                        </div>
                    </form>
                </div>
            </section>


            {/* Results Table */}
            <section className="vf-grid vf-grid__col-3">
                <ResultsTable results={results}/>
            </section>
        </div>
    );
};

export default HomePage;
