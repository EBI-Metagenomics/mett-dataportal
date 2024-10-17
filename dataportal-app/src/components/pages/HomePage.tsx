import React, {useEffect, useState} from 'react';
import TabNavigation from '../molecules/TabNavigation';
import GeneSearchForm from '../organisms/GeneSearch/GeneSearchForm';
import GenomeSearchForm from '../organisms/GenomeSearch/GenomeSearchForm';
import SelectedGenomes from '../organisms/SelectedGenomes';
import {fetchGenomesBySearch} from '../../services/genomeService';
import {fetchSpeciesList} from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomeIntroSection from "@components/organisms/HomeIntroSection";
import Dropdown from '../atoms/Dropdown';

const HomePage: React.FC = () => {
    const [speciesList, setSpeciesList] = useState<any[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState('');
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [selectedGenomes, setSelectedGenomes] = useState<{ id: number; name: string }[]>([]);
    const [totalPages, setTotalPages] = useState(1);
    // State for Genome Search
    const [genomeSearchQuery, setGenomeSearchQuery] = useState('');
    const [genomeResults, setGenomeResults] = useState<any[]>([]);
    const [genomeCurrentPage, setGenomeCurrentPage] = useState(1);
    const [geneCurrentPage, setGeneCurrentPage] = useState(1);

    // State for Gene Search
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);

    useEffect(() => {
        const fetchSpecies = async () => {
            const species = await fetchSpeciesList();
            setSpeciesList(species || []);
        };

        fetchSpecies();
    }, []);

    const handleGenomeSearch = async () => {
        const response = await fetchGenomesBySearch(genomeSearchQuery, selectedSpecies);
        setGenomeResults(response.results || []);
        setTotalPages(response.num_pages || 1);
    };

    const handleGeneSearch = async () => {
        const response = await fetchGenomesBySearch(geneSearchQuery, selectedSpecies);
        setGeneResults(response.results || []);
        setTotalPages(response.num_pages || 1);
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


    const tabs = [
        {id: 'vf-tabs__section--1', label: 'Search Gene'},
        {id: 'vf-tabs__section--2', label: 'Search Genome'}
    ];

    return (
        <div>
            <div>
                <HomeIntroSection/>
            </div>
            <div className="vf-grid__col--span-3">
                <h2 className="vf-section-header__subheading">Select Species</h2>
                <p/>
                <Dropdown
                    options={speciesList.map(species => ({
                        value: species.id,
                        label: species.scientific_name
                    }))}
                    selectedValue={selectedSpecies}
                    onChange={(value) => setSelectedSpecies(value === "" ? "" : value)}
                    className={styles.customDropdown}
                />
                <p/>
            </div>

            <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={setActiveTab}/>
            <div>
                <p/>
            </div>

            <div className="layout-container">
                {/* Left Panel - Search Form */}
                <div className={styles.leftPane}>
                    {activeTab === 'vf-tabs__section--1' && (
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedSpecies={selectedSpecies}
                            selectedGenomes={selectedGenomes}
                            results={geneResults}
                            onSortClick={(sortField) => console.log('Sort by:', sortField)}
                            currentPage={geneCurrentPage}
                            totalPages={totalPages}
                            handlePageClick={(page) => setGeneCurrentPage(page)}
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
                            currentPage={genomeCurrentPage}
                            totalPages={totalPages}
                            handlePageClick={(page) => setGenomeCurrentPage(page)}
                        />
                    )}
                </div>
                {/* Right Panel - Selected Genomes */}
                <div className={styles.rightPane}>
                    <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>
                </div>
            </div>
        </div>
    );
};

export default HomePage;
