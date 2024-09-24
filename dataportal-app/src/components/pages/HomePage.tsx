import React, { useEffect, useState } from 'react';
import TabNavigation from '../molecules/TabNavigation';
import GeneSearchForm from '../organisms/GeneSearch/GeneSearchForm';
import GenomeSearchForm from '../organisms/GenomeSearch/GenomeSearchForm';
import SelectedGenomes from '../organisms/SelectedGenomes';
import { fetchSearchGenomes } from '../../services/searchService';
import { fetchSpeciesList } from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomeIntroSection from "@components/organisms/HomeIntroSection";
import Dropdown from '../atoms/Dropdown';

const HomePage: React.FC = () => {
    const [speciesList, setSpeciesList] = useState<any[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState(''); // Initialize with an empty string
    const [searchQuery, setSearchQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [selectedGenomes, setSelectedGenomes] = useState<string[]>([]);

    // Fetch species list on component mount
    useEffect(() => {
        const fetchSpecies = async () => {
            const species = await fetchSpeciesList();
            setSpeciesList(species || []);
        };

        fetchSpecies();
    }, []);

    const handleSearch = async () => {
        const response = await fetchSearchGenomes(searchQuery, selectedSpecies);
        setResults(response.results || []);
    };

    const handleGenomeSelect = (genome: string) => {
        if (!selectedGenomes.includes(genome)) {
            setSelectedGenomes([...selectedGenomes, genome]);
        }
    };

    const handleRemoveGenome = (genome: string) => {
        setSelectedGenomes(selectedGenomes.filter(g => g !== genome));
    };

    const tabs = [
        { id: 'vf-tabs__section--1', label: 'Search Gene' },
        { id: 'vf-tabs__section--2', label: 'Search Genome' }
    ];

    return (
        <div>
            <div>
                <HomeIntroSection />
            </div>
            <div className="vf-grid__col--span-3">
                <h2 className="vf-section-header__subheading">Select Species</h2>
                <p />
                <Dropdown
                    options={speciesList.map(species => ({
                        value: species.id,
                        label: species.scientific_name
                    }))}
                    selectedValue={selectedSpecies}
                    onChange={(value) => setSelectedSpecies(value === "" ? "" : value)} // Handle setting to empty string
                    className={styles.customDropdown}
                    style={{ width: '300px', height: '40px' }}
                />
                <p />
            </div>

            <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={setActiveTab} />

            <div className="layout-container">
                {/* Left Panel - Selected Genomes */}
                <div className="left-pane">
                    <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome} />
                </div>

                {/* Right Panel - Search Form */}
                <div className="right-pane">
                    {activeTab === 'vf-tabs__section--1' && (
                        <GeneSearchForm
                            searchQuery={searchQuery}
                            onSearchQueryChange={e => setSearchQuery(e.target.value)}
                            onSearchSubmit={handleSearch}
                        />
                    )}

                    {activeTab === 'vf-tabs__section--2' && (
                        <GenomeSearchForm
                            searchQuery={searchQuery}
                            onSearchQueryChange={e => setSearchQuery(e.target.value)}
                            onSearchSubmit={handleSearch}
                            onGenomeSelect={handleGenomeSelect}
                            selectedSpecies={selectedSpecies}
                        />
                    )}
                </div>
            </div>

            {/* Results Table - shared across both tabs */}
            <section className="vf-grid vf-grid__col-3">
                {/* Render search results */}
            </section>
        </div>
    );
};

export default HomePage;
