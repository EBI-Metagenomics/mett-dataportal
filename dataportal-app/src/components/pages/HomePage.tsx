import React, {useEffect, useState} from 'react';
import GeneSearchForm from '../organisms/GeneSearch/GeneSearchForm';
import GenomeSearchForm from '../organisms/GenomeSearch/GenomeSearchForm';
import SelectedGenomes from '../organisms/SelectedGenomes';
import {fetchGenomesBySearch, fetchTypeStrains} from '../../services/genomeService';
import {fetchSpeciesList} from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomeIntroSection from "@components/organisms/HomeIntroSection";

// Define the type for each tab
interface Tab {
    id: string;
    label: string;
}

// Define the props for TabNavigation component
interface TabNavigationProps {
    tabs: Tab[];
    activeTab: string;
    onTabClick: (tabId: string) => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({tabs, activeTab, onTabClick}) => (
    <div className={styles["tabs-container"]}>
        {tabs.map((tab) => (
            <button
                key={tab.id}
                onClick={() => onTabClick(tab.id)}
                className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
            >
                {tab.label}
            </button>
        ))}
    </div>
);


const HomePage: React.FC = () => {
    const [speciesList, setSpeciesList] = useState<{ id: number; scientific_name: string }[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState<number[]>([]);
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [selectedGenomes, setSelectedGenomes] = useState<{ id: number; name: string }[]>([]);
    const [typeStrains, setTypeStrains] = useState<{ id: number; isolate_name: string }[]>([]);
    const [selectedTypeStrains, setSelectedTypeStrains] = useState<number[]>([]);

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
            const strains = await fetchTypeStrains();
            setTypeStrains(strains || []);
        };

        fetchSpecies();
        fetchTypeStrainsData();
    }, []);

    const handleSpeciesSelect = (speciesId: number) => {
        if (selectedSpecies.includes(speciesId)) {
            setSelectedSpecies(selectedSpecies.filter(id => id !== speciesId));
        } else {
            setSelectedSpecies([...selectedSpecies, speciesId]);
        }
    };

    const handleTypeStrainSelect = (strainId: number) => {
        let updatedSelectedTypeStrains: number[];

        if (selectedTypeStrains.includes(strainId)) {
            updatedSelectedTypeStrains = selectedTypeStrains.filter(id => id !== strainId);
        } else {
            updatedSelectedTypeStrains = [...selectedTypeStrains, strainId];
        }

        setSelectedTypeStrains(updatedSelectedTypeStrains);

        const updatedTypeStrains = typeStrains
            .filter(strain => updatedSelectedTypeStrains.includes(strain.id))
            .map(strain => ({id: strain.id, name: strain.isolate_name}));

        setSelectedGenomes(updatedTypeStrains);
    };

    const handleGenomeSearch = async () => {
        const results = await fetchGenomesBySearch(selectedSpecies, genomeSearchQuery);
        setGenomeResults(results || []);
    };

    const handleGeneSearch = async () => {
        const results = await fetchGenomesBySearch(selectedSpecies, geneSearchQuery);
        setGeneResults(results || []);
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

    const handleTabClick = (tabId: string) => {
        setActiveTab(tabId);
    };

    const linkData = {
        template: '/gene-viewer/gene/${id}/genome/${strain_id}',
        alias: 'Browse'
    };

    const tabs: Tab[] = [
        {id: 'vf-tabs__section--1', label: 'Search Genome'},
        {id: 'vf-tabs__section--2', label: 'Search Gene'}
    ];

    return (
        <div>
            <div>
                <HomeIntroSection/>
            </div>

            <div className="layout-container">
                {/* Left Panel */}
                <div className={styles.leftPane}>
                    {/* Species Section */}
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
                                        <i>{species.scientific_name}</i>
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Type Strains Section */}
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

                    <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>
                </div>

                {/* Right Panel - Search Form */}
                <div className={styles.rightPane}>
                    <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={handleTabClick}/>
                    {activeTab === 'vf-tabs__section--1' && (
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
                            currentPage={1}
                            totalPages={1}
                            handlePageClick={(page) => console.log('Page:', page)}
                        />
                    )}

                    {activeTab === 'vf-tabs__section--2' && (
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedSpecies={selectedSpecies}
                            selectedGenomes={selectedGenomes}
                            results={geneResults}
                            onSortClick={(sortField) => console.log('Sort by:', sortField)}
                            currentPage={1}
                            totalPages={1}
                            handlePageClick={(page) => console.log('Page:', page)}
                            linkData={linkData}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
