import React, {useEffect, useMemo, useState} from 'react';
import {useLocation} from 'react-router-dom'
import GeneSearchForm from '../organisms/GeneSearch/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '../organisms/GenomeSearch/GenomeSearchForm/GenomeSearchForm';
import SelectedGenomes from '../organisms/SelectedGenomes';
import {GenomeService} from '../../services/genomeService';
import {SpeciesService} from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";
import {BaseGenome, GenomeMeta} from "../../interfaces/Genome";
import SpeciesFilter from '@components/Filters/SpeciesFilter';
import TypeStrainsFilter from '@components/Filters/TypeStrainsFilter';
import {SPINNER_DELAY} from "../../utils/appConstants";

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
    const [selectedGenomes, setSelectedGenomes] = useState<BaseGenome[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState<number[]>([]);
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [typeStrains, setTypeStrains] = useState<GenomeMeta[]>([]);
    const [selectedTypeStrains, setSelectedTypeStrains] = useState<number[]>([]);

    // State for Genome Search
    const [genomeSearchQuery, setGenomeSearchQuery] = useState('');
    const [genomeResults, setGenomeResults] = useState<any[]>([]);

    // State for Gene Search
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    // sorting state
    const [genomeSortField, setGenomeSortField] = useState<string>('species');
    const [genomeSortOrder, setGenomeSortOrder] = useState<'asc' | 'desc'>('asc');
    const [geneSortField, setGeneSortField] = useState<string>('gene_name');
    const [geneSortOrder, setGeneSortOrder] = useState<'asc' | 'desc'>('asc');

    const essentialityFilter = useMemo(() => [], []);


    const spinner = loading && (
        <div className={styles.spinnerOverlay}>
            <div className={styles.spinner}></div>
        </div>
    );


    useEffect(() => {
        const fetchSpecies = async () => {
            const species = await SpeciesService.fetchSpeciesList();
            setSpeciesList(species || []);
        };

        const fetchTypeStrainsData = async () => {
            const strains = await GenomeService.fetchTypeStrains();
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
            const response = await GenomeService.fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, genomeSortField, genomeSortOrder);
            // console.log('Fetched results:', response.results);
            setGenomeResults(response.results);
        };
        fetchData();
    }, [genomeSearchQuery, selectedSpecies]);

    const handleSpeciesSelect = async (speciesId: number) => {
        setLoading(true); // Show spinner
        const startTime = Date.now(); // Track start time

        let updatedSelectedSpecies: number[];
        if (selectedSpecies.includes(speciesId)) {
            updatedSelectedSpecies = selectedSpecies.filter((id) => id !== speciesId);
        } else {
            updatedSelectedSpecies = [...selectedSpecies, speciesId];
        }

        setSelectedSpecies(updatedSelectedSpecies);

        if (updatedSelectedSpecies.length === 0) {
            setSelectedTypeStrains([]);
        } else {
            const validTypeStrains = typeStrains.filter((strain) =>
                updatedSelectedSpecies.includes(strain.species.id)
            );

            const updatedSelectedTypeStrains = selectedTypeStrains.filter((strainId) =>
                validTypeStrains.some((strain) => strain.id === strainId)
            );

            setSelectedTypeStrains(updatedSelectedTypeStrains);

            if (updatedSelectedTypeStrains.length > 0) {
                const filteredResults = genomeResults.filter((result) =>
                    updatedSelectedTypeStrains.includes(result.strain_id)
                );
                setGenomeResults(filteredResults);
            } else {
                await handleGenomeSearch();
            }
        }

        const elapsedTime = Date.now() - startTime; // Calculate elapsed time
        const remainingTime = SPINNER_DELAY - elapsedTime;

        setTimeout(() => {
            setLoading(false); // Hide spinner after delay
        }, remainingTime > 0 ? remainingTime : 0);
    };


    const handleTypeStrainToggle = async (strainId: number) => {
        setLoading(true); // Show spinner
        const startTime = Date.now(); // Track start time

        let updatedSelectedTypeStrains: number[];

        if (selectedTypeStrains.includes(strainId)) {
            updatedSelectedTypeStrains = selectedTypeStrains.filter((id) => id !== strainId);
        } else {
            updatedSelectedTypeStrains = [...selectedTypeStrains, strainId];
        }

        setSelectedTypeStrains(updatedSelectedTypeStrains);

        if (updatedSelectedTypeStrains.length > 0) {
            const filteredResults = genomeResults.filter((result) =>
                updatedSelectedTypeStrains.includes(result.strain_id)
            );
            setGenomeResults(filteredResults);
        } else {
            await handleGenomeSearch();
        }

        const elapsedTime = Date.now() - startTime; // Calculate elapsed time
        const remainingTime = SPINNER_DELAY - elapsedTime;

        setTimeout(() => {
            setLoading(false); // Hide spinner after delay
        }, remainingTime > 0 ? remainingTime : 0);
    };


    const handleGenomeSearch = async (field = genomeSortField, order = genomeSortOrder) => {
        const response = await GenomeService.fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, field, order);
        setGenomeResults(response.results);
    };

    //todo to be removed
    const handleGeneSearch = async (field = geneSortField, order = geneSortOrder) => {
        const response = await GenomeService.fetchGenomesBySearch(selectedSpecies, geneSearchQuery, field, order);
        setGenomeResults(response.results);
    };

    const handleGenomeSelect = (genome: BaseGenome) => {
        if (!selectedGenomes.some(g => g.id === genome.id)) {
            setSelectedGenomes([...selectedGenomes, genome]);
        }
    };

    const handleRemoveGenome = (genomeId: number) => {
        setSelectedGenomes(selectedGenomes.filter(g => g.id !== genomeId));
        setSelectedTypeStrains(selectedTypeStrains.filter(id => id !== genomeId));
    };

    const handleToggleGenomeSelect = (genome: BaseGenome) => {
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
        const newSortOrder = genomeSortField === field && genomeSortOrder === 'asc' ? 'desc' : 'asc';
        setGenomeSortField(field);
        setGenomeSortOrder(newSortOrder);
        // console.log('Sorting Genomes by:', {field, order: newSortOrder});
        handleGenomeSearch(field, newSortOrder);
    };


    const handleGeneSortClick = async (field: string) => {
        const newSortOrder = geneSortField === field && geneSortOrder === 'asc' ? 'desc' : 'asc';
        setGeneSortField(field);
        setGeneSortOrder(newSortOrder);
        // console.log('Sorting Genes by:', {field, order: newSortOrder});
        //handleGeneSearch(field, newSortOrder);
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
        {id: 'vf-tabs__section--1', label: 'Genome Search'},
        {id: 'vf-tabs__section--2', label: 'Gene Search'}
    ];

    return (
        <div>
            {spinner} {/* Display spinner */}
            <div>
                <HomePageHeadBand
                    typeStrains={typeStrains}
                    linkTemplate="/genome/$strain_name"
                />
            </div>

            <div className="layout-container">
                {/* Left Panel */}
                <div className={styles.leftPane}>
                    {/* Species Filter */}
                    <SpeciesFilter
                        speciesList={speciesList}
                        selectedSpecies={selectedSpecies}
                        onSpeciesSelect={handleSpeciesSelect}
                    />

                    {/* Type Strains Filter */}
                    <TypeStrainsFilter
                        typeStrains={typeStrains}
                        selectedTypeStrains={selectedTypeStrains}
                        selectedSpecies={selectedSpecies}
                        onTypeStrainToggle={handleTypeStrainToggle}
                    />

                    <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>
                </div>

                {/* Right Panel - Search Form */}
                {/*<div className={styles.rightPane}>*/}
                {/*    <div className={styles.rightPaneButtons}>*/}
                {/*        <button className="vf-button vf-button--primary vf-button--sm"*/}
                {/*                onClick={() => downloadTableData(genomeResults, 'csv')}>Download CSV*/}
                {/*        </button>*/}
                {/*    </div>*/}
                {/*</div>*/}
                <div className={styles.rightPane}>
                    <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={handleTabClick}/>
                    {activeTab === 'vf-tabs__section--1' && (
                        <GenomeSearchForm
                            // key={`${genomeResults.length}-${sortField}-${sortOrder}`}
                            searchQuery={genomeSearchQuery}
                            onSearchQueryChange={e => setGenomeSearchQuery(e.target.value)}
                            onSearchSubmit={handleGenomeSearch}
                            // onGenomeSelect={handleGenomeSelect}
                            selectedSpecies={selectedSpecies}
                            selectedTypeStrains={selectedTypeStrains}
                            onSortClick={handleGenomeSortClick}
                            sortField={genomeSortField}
                            sortOrder={genomeSortOrder}
                            results={genomeResults}
                            selectedGenomes={selectedGenomes}
                            onToggleGenomeSelect={handleToggleGenomeSelect}
                            linkData={genomeLinkData}
                            setLoading={setLoading}
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
                            sortField={geneSortField}
                            sortOrder={geneSortOrder}
                            linkData={geneLinkData}
                            essentialityFilter={essentialityFilter}
                            setLoading={setLoading}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
