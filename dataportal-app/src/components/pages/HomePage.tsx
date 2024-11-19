import React, {useEffect, useState} from 'react';
import {useLocation} from 'react-router-dom'
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
    const location = useLocation();
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

    const [sortField, setSortField] = useState<string>('species');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

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

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const speciesId = params.get('speciesId');

        if (speciesId) {
            const id = parseInt(speciesId, 10);
            if (!selectedSpecies.includes(id)) {
                setSelectedSpecies([...selectedSpecies, id]);
            }
        }
    }, [location.search]);

    useEffect(() => {
        const fetchData = async () => {
            const response = await fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, sortField, sortOrder);
            console.log('Fetched results:', response.results);
            setGenomeResults(response.results);
        };
        fetchData();
    }, [genomeSearchQuery, selectedSpecies]);

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

    const handleGenomeSearch = async (field = sortField, order = sortOrder) => {
        const response = await fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, sortField, sortOrder);
        setGenomeResults(response.results);
    };

    const handleGeneSearch = async () => {
        const response = await fetchGenomesBySearch(selectedSpecies, geneSearchQuery, sortField, sortOrder);
        setGenomeResults(response.results);
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

    const handleGenomeSortClick = async (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        console.log('Sorting Genomes by:', {field, order: newSortOrder});
    };

    const handleGeneSortClick = async (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        console.log('HomePage Sorting Genes by:', {field, order: newSortOrder});
    };

    const geneLinkData = {
        template: '/genome/${strain_name}?gene_id=${gene_id}',
        alias: 'Browse'
    };

    const genomeLinkData = {
        template: '/genome/${strain_name}',
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
                            // key={`${genomeResults.length}-${sortField}-${sortOrder}`}
                            searchQuery={genomeSearchQuery}
                            onSearchQueryChange={e => setGenomeSearchQuery(e.target.value)}
                            onSearchSubmit={handleGenomeSearch}
                            onGenomeSelect={handleGenomeSelect}
                            selectedSpecies={selectedSpecies}
                            onSortClick={handleGenomeSortClick}
                            sortField={sortField}
                            sortOrder={sortOrder}
                            results={genomeResults}
                            selectedGenomes={selectedGenomes}
                            onToggleGenomeSelect={handleToggleGenomeSelect}
                            linkData={genomeLinkData}
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
                            onSortClick={handleGeneSortClick}
                            sortField={sortField}
                            sortOrder={sortOrder}
                            linkData={geneLinkData}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
