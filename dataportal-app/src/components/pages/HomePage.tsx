import React, {useEffect, useState} from 'react';
import TabNavigation from '../molecules/TabNavigation';
import GeneSearchForm from '../organisms/GeneSearch/GeneSearchForm';
import GenomeSearchForm from '../organisms/GenomeSearch/GenomeSearchForm';
import SelectedGenomes from '../organisms/SelectedGenomes';
import {fetchGenomesBySearch, fetchTypeStrains} from '../../services/genomeService';
import {fetchSpeciesList} from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomeIntroSection from "@components/organisms/HomeIntroSection";

const HomePage: React.FC = () => {
    const [speciesList, setSpeciesList] = useState<{ id: number; scientific_name: string }[]>([]); // Updated state type for species
    const [selectedSpecies, setSelectedSpecies] = useState<number[]>([]); // State to manage selected species
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [selectedGenomes, setSelectedGenomes] = useState<{ id: number; name: string }[]>([]);
    const [typeStrains, setTypeStrains] = useState<{ id: number; isolate_name: string }[]>([]); // State for type strains
    const [selectedTypeStrains, setSelectedTypeStrains] = useState<number[]>([]); // State to store selected type strains

    // State for Genome Search
    const [genomeSearchQuery, setGenomeSearchQuery] = useState('');
    const [genomeResults, setGenomeResults] = useState<any[]>([]);

    // State for Gene Search
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);

    useEffect(() => {
        const fetchSpecies = async () => {
            const species = await fetchSpeciesList();
            setSpeciesList(species || []);
        };

        const fetchTypeStrainsData = async () => {
            const strains = await fetchTypeStrains(); // Fetch type strains
            setTypeStrains(strains || []);
        };

        fetchSpecies();
        fetchTypeStrainsData(); // Fetch type strains on component mount
    }, []);

    // Handle species selection
    const handleSpeciesSelect = (speciesId: number) => {
        if (selectedSpecies.includes(speciesId)) {
            setSelectedSpecies(selectedSpecies.filter(id => id !== speciesId));
        } else {
            setSelectedSpecies([...selectedSpecies, speciesId]);
        }
    };

    const handleTypeStrainSelect = (strainId: number) => {
        if (selectedTypeStrains.includes(strainId)) {
            setSelectedTypeStrains(selectedTypeStrains.filter(id => id !== strainId));
        } else {
            setSelectedTypeStrains([...selectedTypeStrains, strainId]);
        }
    };

    const handleGenomeSearch = async () => {
        const results = await fetchGenomesBySearch(selectedSpecies, genomeSearchQuery);
        setGenomeResults(results || []); // No 'results' property, so we use the array directly
    };

    const handleGeneSearch = async () => {
        const results = await fetchGenomesBySearch(selectedSpecies, geneSearchQuery);
        setGeneResults(results || []); // No 'results' property, so we use the array directly
    };

    const handleGenomeSelect = (genome: { id: number; name: string }) => {
        if (!selectedGenomes.some(g => g.id === genome.id)) {
            setSelectedGenomes([...selectedGenomes, genome]);
        }
    };

    const handleRemoveGenome = (genomeId: number) => {
        setSelectedGenomes(selectedGenomes.filter(g => g.id !== genomeId));
    };

    const handleToggleGenomeSelect = (genome: { id: number; name: string }) => {
        if (selectedGenomes.some(g => g.id === genome.id)) {
            handleRemoveGenome(genome.id);
        } else {
            handleGenomeSelect(genome);
        }
    };

    const linkData = {
        template: '/gene-viewer/gene/${id}/?genomeId=${strain_id}',
        alias: 'Browse'
    };

    const tabs = [
        {id: 'vf-tabs__section--1', label: 'Search Gene'},
        {id: 'vf-tabs__section--2', label: 'Search Genome'}
    ];

    return (
        <div>
            <div>
                <HomeIntroSection/>
            </div>

            <div className="layout-container">
                {/* Left Panel */}
                <div className={styles.leftPane}>
                    {/* Add Species Section */}
                    <div className={styles.speciesSection}>
                        <h3>Species</h3>
                        <ul>
                            {speciesList.map(species => (
                                <li key={species.id}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={selectedSpecies.includes(species.id)}
                                            onChange={() => handleSpeciesSelect(species.id)}
                                        />
                                        {species.scientific_name}
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Add Type Strains Section */}
                    <div className={styles.typeStrains}>
                        <h3>Type Strains</h3>
                        <ul>
                            {typeStrains.map(strain => (
                                <li key={strain.id}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={selectedTypeStrains.includes(strain.id)}
                                            onChange={() => handleTypeStrainSelect(strain.id)}
                                        />
                                        {strain.isolate_name}
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Selected Genomes */}
                    <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>
                </div>

                {/* Right Panel - Search Form */}
                <div className={styles.rightPane}>
                    <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={setActiveTab}/>
                    {activeTab === 'vf-tabs__section--1' && (
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedSpecies={selectedSpecies}
                            selectedGenomes={selectedGenomes}
                            results={geneResults}
                            onSortClick={(sortField) => console.log('Sort by:', sortField)}
                            currentPage={1} // Assuming you want page 1 (if needed for pagination)
                            totalPages={1}  // Assuming no pagination here (set 1)
                            handlePageClick={(page) => console.log('Page:', page)}
                            linkData={linkData}
                        />
                    )}

                    {activeTab === 'vf-tabs__section--2' && (
                        <GenomeSearchForm
                            searchQuery={genomeSearchQuery}
                            onSearchQueryChange={e => setGenomeSearchQuery(e.target.value)}
                            onSearchSubmit={handleGenomeSearch}
                            onGenomeSelect={handleGenomeSelect}
                            selectedSpecies={selectedSpecies}
                            results={genomeResults}
                            onSortClick={(sortField) => console.log('Sort by:', sortField)}
                            selectedGenomes={selectedGenomes}
                            onToggleGenomeSelect={handleToggleGenomeSelect}
                            currentPage={1} // Assuming page 1
                            totalPages={1}  // Assuming no pagination
                            handlePageClick={(page) => console.log('Page:', page)}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
