import React, {useEffect, useState} from 'react';
import {useLocation} from 'react-router-dom'
import GeneSearchForm from '@components/organisms/Gene/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm';
import {GenomeService} from '../../services/genomeService';
import {SpeciesService} from "../../services/speciesService";
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";
import {BaseGenome, GenomeMeta} from "../../interfaces/Genome";
import {SPINNER_DELAY, DEFAULT_PER_PAGE_CNT} from "../../utils/appConstants";
import {GeneService} from '../../services/geneService';
import {GeneMeta} from '../../interfaces/Gene';

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
    const [speciesList, setSpeciesList] = useState<{ acronym: string; scientific_name: string, common_name: string, taxonomy_id: number }[]>([]);
    const [selectedGenomes, setSelectedGenomes] = useState<BaseGenome[]>([]);
    const [selectedSpecies, setSelectedSpecies] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState('vf-tabs__section--1');
    const [typeStrains, setTypeStrains] = useState<GenomeMeta[]>([]);
    const [selectedTypeStrains, setSelectedTypeStrains] = useState<string[]>([]);

    // State for Genome Search
    const [genomeSearchQuery, setGenomeSearchQuery] = useState('');
    const [genomeResults, setGenomeResults] = useState<GenomeMeta[]>([]);

    // State for Gene Search
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<GeneMeta[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    // sorting state
    const [genomeSortField, setGenomeSortField] = useState<string>('species');
    const [genomeSortOrder, setGenomeSortOrder] = useState<'asc' | 'desc'>('asc');
    const [geneSortField, setGeneSortField] = useState<string>('locus_tag');
    const [geneSortOrder, setGeneSortOrder] = useState<'asc' | 'desc'>('asc');

    const [totalPages, setTotalPages] = useState<number>(1);

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
            setLoading(true);
            try {
                const response = await GenomeService.fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, genomeSortField, genomeSortOrder);
                setGenomeResults(response.results);
            } catch (error) {
                console.error('Error fetching genome data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [genomeSearchQuery, selectedSpecies, genomeSortField, genomeSortOrder]);

    const handleSpeciesSelect = async (species_acronym: string) => {
        setLoading(true);
        try {
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
                        updatedSelectedTypeStrains.includes(result.isolate_name)
                    );
                    setGenomeResults(filteredResults);
                } else {
                    await handleGenomeSearch();
                }
            }
        } catch (error) {
            console.error('Error in handleSpeciesSelect:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTypeStrainToggle = async (isolate_name: string) => {
        setLoading(true);
        try {
            let updatedSelectedTypeStrains: string[];

            if (selectedTypeStrains.includes(isolate_name)) {
                updatedSelectedTypeStrains = selectedTypeStrains.filter((id) => id !== isolate_name);
            } else {
                updatedSelectedTypeStrains = [...selectedTypeStrains, isolate_name];
            }

            setSelectedTypeStrains(updatedSelectedTypeStrains);

            if (updatedSelectedTypeStrains.length > 0) {
                const filteredResults = genomeResults.filter((result) =>
                    updatedSelectedTypeStrains.includes(result.isolate_name)
                );
                setGenomeResults(filteredResults);
            } else {
                await handleGenomeSearch();
            }
        } catch (error) {
            console.error('Error in handleTypeStrainToggle:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenomeSearch = async (field = genomeSortField, order = genomeSortOrder) => {
        setLoading(true);
        try {
            const response = await GenomeService.fetchGenomesBySearch(selectedSpecies, genomeSearchQuery, field, order);
            setGenomeResults(response.results);
        } catch (error) {
            console.error('Error in handleGenomeSearch:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGeneSearch = async (field?: string, order?: 'asc' | 'desc') => {
        setLoading(true);
        try {
            const response = await GeneService.fetchGeneSearchResultsAdvanced(
                geneSearchQuery,
                1, // page
                DEFAULT_PER_PAGE_CNT, // pageSize
                field || geneSortField,
                order || geneSortOrder,
                selectedGenomes.map(genome => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                })),
                selectedSpecies
            );
            setGeneResults(response.results || []);
            setTotalPages(response.num_pages || 1);
        } catch (error) {
            console.error('Error searching genes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGeneResultsChange = (results: GeneMeta[]) => {
        setGeneResults(results);
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
        await handleGeneSearch(field, newSortOrder);
    };


    const geneLinkData = {
        template: '/genome/${strain_name}',
        alias: 'Select'
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
                    speciesList={speciesList}
                    selectedSpecies={selectedSpecies}
                    handleSpeciesSelect={handleSpeciesSelect}
                />
            </div>

            <div className="layout-container">

                <div>
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
                            onResultsChange={handleGeneResultsChange}
                            isTypeStrainAvailable={selectedGenomes.some(genome => genome.type_strain === true)}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomePage;
