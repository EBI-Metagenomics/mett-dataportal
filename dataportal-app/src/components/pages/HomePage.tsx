import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom'
import GeneSearchForm from '@components/organisms/Gene/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm';
import PyhmmerSearchForm from '@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchForm';
import { GenomeService } from '../../services/genomeService';
import { SpeciesService } from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";
import { BaseGenome, GenomeMeta } from "../../interfaces/Genome";
import { SPINNER_DELAY } from "../../utils/appConstants";

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

const TabNavigation: React.FC<TabNavigationProps> = ({ tabs, activeTab, onTabClick }) => (
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
    const [speciesList, setSpeciesList] = useState<{ acronym: string; scientific_name: string, common_name: string, taxonomy_id: number }[]>([]);
    const [selectedGenomes, setSelectedGenomes] = useState<BaseGenome[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [typeStrains, setTypeStrains] = useState<GenomeMeta[]>([]);
    const [selectedTypeStrains, setSelectedTypeStrains] = useState<string[]>([]);

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
    const [geneSortField, setGeneSortField] = useState<string>('locus_tag');
    const [geneSortOrder, setGeneSortOrder] = useState<'asc' | 'desc'>('asc');


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
        const species_acronym = params.get('species_acronym');

        if (species_acronym) {
            if (!selectedSpecies.includes(species_acronym)) {
                setSelectedSpecies([...selectedSpecies, species_acronym]);
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

    const handleSpeciesSelect = async (species_acronym: string) => {
        setLoading(true); // Show spinner
        const startTime = Date.now(); // Track start time

        let updatedSelectedSpecies: string[];
        if (selectedSpecies.includes(species_acronym)) {
            updatedSelectedSpecies = selectedSpecies.filter((acronym) => acronym !== species_acronym);
        } else {
            updatedSelectedSpecies = [...selectedSpecies, species_acronym];
        }

        setSelectedSpecies(updatedSelectedSpecies);

        if (updatedSelectedSpecies.length === 0) {
            setSelectedTypeStrains([]);
        } else {
            const validTypeStrains = typeStrains.filter((strain) =>
                updatedSelectedSpecies.includes(strain.species_acronym)
            );

            const updatedSelectedTypeStrains = selectedTypeStrains.filter((isolate_name) =>
                validTypeStrains.some((strain) => strain.isolate_name === isolate_name)
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


    const handleTypeStrainToggle = async (isolate_name: string) => {
        setLoading(true); // Show spinner
        const startTime = Date.now(); // Track start time

        let updatedSelectedTypeStrains: string[];

        if (selectedTypeStrains.includes(isolate_name)) {
            updatedSelectedTypeStrains = selectedTypeStrains.filter((id) => id !== isolate_name);
        } else {
            updatedSelectedTypeStrains = [...selectedTypeStrains, isolate_name];
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
        if (!selectedGenomes.some(g => g.isolate_name === genome.isolate_name)) {
            setSelectedGenomes([...selectedGenomes, genome]);
        }
    };

    const handleRemoveGenome = (isolate_name: string) => {
        setSelectedGenomes(selectedGenomes.filter(g => g.isolate_name !== isolate_name));
        setSelectedTypeStrains(selectedTypeStrains.filter(id => id !== isolate_name));
    };

    const handleToggleGenomeSelect = (genome: BaseGenome) => {
        if (selectedGenomes.some(g => g.isolate_name === genome.isolate_name)) {
            handleRemoveGenome(genome.isolate_name);
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
        template: '/genome/${strain_name}?locus_tag=${locus_tag}',
        alias: 'Browse'
    };

    const genomeLinkData = {
        template: '/genome/${strain_name}',
        alias: 'Browse'
    };

    const tabs: Tab[] = [
        { id: 'vf-tabs__section--1', label: 'Genome Search' },
        { id: 'vf-tabs__section--2', label: 'Gene Search' },
        { id: 'vf-tabs__section--3', label: 'Protein Search' }
    ];

    return (
        <div>
            {spinner} {/* Display spinner */}
            <div>
                <HomePageHeadBand
                    typeStrains={typeStrains}
                    linkTemplate="/genome/$strain_name"
                    speciesList={speciesList}
                    selectedSpecies={selectedSpecies}
                    handleSpeciesSelect={handleSpeciesSelect}
                />
            </div>

            <div className="layout-container">

                <div>
                    <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={handleTabClick} />
                    {activeTab === 'vf-tabs__section--1' && (
                        <GenomeSearchForm
                            // key={`${genomeResults.length}-${sortField}-${sortOrder}`}
                            searchQuery={genomeSearchQuery}
                            onSearchQueryChange={e => setGenomeSearchQuery(e.target.value)}
                            onSearchSubmit={handleGenomeSearch}
                            // onGenomeSelect={handleGenomeSelect}
                            selectedSpecies={selectedSpecies}
                            selectedTypeStrains={selectedTypeStrains}
                            typeStrains={typeStrains}
                            onSortClick={handleGenomeSortClick}
                            sortField={genomeSortField}
                            sortOrder={genomeSortOrder}
                            results={genomeResults}
                            selectedGenomes={selectedGenomes}
                            onToggleGenomeSelect={handleToggleGenomeSelect}
                            handleTypeStrainToggle={handleTypeStrainToggle}
                            handleRemoveGenome={handleRemoveGenome}
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
                            handleRemoveGenome={handleRemoveGenome}
                            setLoading={setLoading}
                        />
                    )}
                    {activeTab === 'vf-tabs__section--3' && (
                        <PyhmmerSearchForm />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
