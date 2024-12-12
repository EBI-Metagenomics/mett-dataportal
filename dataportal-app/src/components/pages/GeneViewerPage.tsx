import React, {useEffect, useMemo, useState} from 'react';
import {useParams} from 'react-router-dom';
import getAssembly from '@components/organisms/GeneViewer/assembly';
import getTracks from '@components/organisms/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/GeneSearch/GeneSearchForm/GeneSearchForm";
import {GenomeService} from "../../services/genomeService";
import { GeneService } from '../../services/geneService';
import {JBrowseApp} from "@jbrowse/react-app";
import {GenomeMeta} from "../../interfaces/Genome";
import {GeneMeta} from "../../interfaces/Gene";
import {DisplayedRegion} from "../../interfaces/jbrowse";
import {ZOOM_LEVELS} from "../../utils/appConstants";
import GeneSearchWithFilters from "@components/organisms/GeneSearch/GeneSearchModules/GeneSearchWithFilters";

const GeneViewerPage: React.FC = () => {
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [totalPages, setTotalPages] = useState(1);

    const [sortField, setSortField] = useState<string>('species');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const {strainName} = useParams<{ strainName?: string }>();
    const searchParams = new URLSearchParams(location.search);
    const geneId = searchParams.get('gene_id');

    useEffect(() => {
        const fetchGeneAndGenomeMeta = async () => {
            try {
                if (geneId) {
                    const geneResponse = await GeneService.fetchGeneById(Number(geneId));
                    setGeneMeta(geneResponse);

                    const genomeResponse = await GenomeService.fetchGenomeByStrainIds([geneResponse.strain_id]);
                    setGenomeMeta(genomeResponse[0]);
                } else if (strainName) {
                    const genomeResponse = await GenomeService.fetchGenomeByIsolateNames([strainName]);
                    setGenomeMeta(genomeResponse[0]);
                }
            } catch (error) {
                console.error('Error fetching gene/genome meta information', error);
            }
        };

        fetchGeneAndGenomeMeta();
    }, [geneId, strainName]);

    const assembly = useMemo(() => {
        if (genomeMeta) {
            console.log("base fasta indexes path: " + process.env.REACT_APP_ASSEMBLY_INDEXES_PATH)
            return getAssembly(genomeMeta, process.env.REACT_APP_ASSEMBLY_INDEXES_PATH
                ? process.env.REACT_APP_ASSEMBLY_INDEXES_PATH : '');
        }
        return null; // return null if genomeMeta is missing
    }, [genomeMeta]);

    const tracks = useMemo(() => {
        console.log("base gff indexes path: " + process.env.REACT_APP_GFF_INDEXES_PATH)
        return genomeMeta ? getTracks(genomeMeta, process.env.REACT_APP_GFF_INDEXES_PATH
            ? process.env.REACT_APP_GFF_INDEXES_PATH : '') : [];
    }, [genomeMeta]);

    const sessionConfig = useMemo(() => {
        if (genomeMeta) {
            return getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
        } else {
            // Default session configuration if only genomeMeta is available
            return {
                name: "Default Genome View",
                views: [
                    {
                        type: "LinearGenomeView",
                        bpPerPx: 2,
                        tracks: tracks,
                        displayedRegions: [
                            {
                                refName: 'Default assembly',
                                start: 0,
                                end: 5000000
                            }
                        ]
                    }
                ]
            };
        }
        return null;
    }, [genomeMeta, geneMeta, assembly, tracks]);

    // wait until `assembly` is ready
    useEffect(() => {
        const checkAssemblyReady = setInterval(() => {
            if (assembly) {
                clearInterval(checkAssemblyReady); // Clear
            }
        }, 100); // Check every 100 milliseconds

        return () => clearInterval(checkAssemblyReady);
    }, [assembly]);


    // const localViewState = useGeneViewerState(assembly, tracks, sessionConfig).viewState;
    const {viewState, initializationError} = useGeneViewerState(assembly, tracks, sessionConfig);

    useEffect(() => {
        const waitForInitialization = async () => {
            if (viewState && geneMeta) {
                console.log("geneMeta view state", geneMeta);
                const linearGenomeView = viewState.session.views[0];

                if (linearGenomeView?.type === 'LinearGenomeView') {
                    console.log('Waiting for LinearGenomeView to initialize...');

                    // Wait until linearGenomeView.initialized
                    const waitForReady = async () => {
                        const maxRetries = 1; // Retry for a maximum of 2 times (200 milliseconds)
                        let retries = 0;

                        while (!linearGenomeView.initialized && retries < maxRetries) {
                            console.log(`Retry ${retries + 1}: LinearGenomeView not initialized yet.`);
                            await new Promise(resolve => setTimeout(resolve, 200)); // Wait 100ms
                            retries++;
                        }

                        if (!linearGenomeView.initialized) {
                            console.error('LinearGenomeView failed to initialize within the timeout period.');
                            return;
                        }

                        // Once initialized, execute the navigation and zoom logic
                        console.log('LinearGenomeView initialized:', linearGenomeView.initialized);

                        try {
                            const locationString = `${geneMeta.seq_id}:${geneMeta.start_position}..${geneMeta.end_position}`;
                            // console.log('Navigating to:', locationString);

                            // Perform navigation
                            linearGenomeView.navToLocString(locationString);

                            // Apply zoom with a delay
                            setTimeout(() => {
                                linearGenomeView.zoomTo(ZOOM_LEVELS.DEFAULT);
                                // console.log('Zoom applied');
                            }, 200);

                        } catch (error) {
                            console.error('Error during navigation or zoom:', error);
                        }
                    };

                    await waitForReady();
                } else {
                    console.error('LinearGenomeView not found or of incorrect type.');
                }
            } else {
                console.log('viewState or geneMeta not ready.');
            }
        };

        waitForInitialization();
    }, [viewState, geneMeta]);


    if (!viewState) {
        return <p>Loading Genome Viewer...</p>;
    }


    const handleGeneSearch = async () => {
        if (genomeMeta?.id) {
            const response = await GeneService.fetchGeneBySearch(genomeMeta.id, geneSearchQuery);
            setGeneResults(response.results || []);
            setTotalPages(response.num_pages || 1);
        }
    };

    const handleGeneSortClick = async (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        console.log('Geneviewer Sorting Genes by:', {field, order: newSortOrder});
    };

    const linkData = {
        template: '/genome/${strain_name}',
        alias: 'Select'
    };

    return (
        <div>
            <div className={`vf-content ${styles.vfContent}`}>
                <div style={{height: '20px'}}></div>
            </div>
            <div className={`vf-content ${styles.vfContent}`}>
                <span style={{display: 'none'}}><p>
                placeholder
            </p></span>
            </div>

            <section>
                {/* Breadcrumb Section */}
                <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                    <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                        <li className={styles.breadcrumbsItem}>
                            <a href="/" className="vf-breadcrumbs__link">Home</a>
                        </li>
                        <span className={styles.separator}> | </span>
                        <li className={styles.breadcrumbsItem}>
                            <b>Genome View</b>
                        </li>
                        {/*<span className={styles.separator}> | </span>*/}
                        {/*{genomeMeta ? (*/}
                        {/*    <li className={`${styles.breadcrumbsItem} ${styles.dropdown}`}>*/}
                        {/*        <a href="#" className="vf-breadcrumbs__link vf-dropdown__trigger">*/}
                        {/*            Related <span className={`${styles.icon} ${styles.iconDownTriangle}`}></span>*/}
                        {/*        </a>*/}
                        {/*        <ul className={styles.dropdownList}>*/}
                        {/*            <li className={styles.dropdownItem}>*/}
                        {/*                <a href={`/home?speciesId=${genomeMeta.species_id}`}*/}
                        {/*                   className={styles.dropdownLink}>Other Strains*/}
                        {/*                    of <i>{genomeMeta.species}</i></a>*/}
                        {/*            </li>*/}
                        {/*        </ul>*/}
                        {/*    </li>*/}
                        {/*) : (*/}
                        {/*    <p>Loading genome meta information...</p>)}*/}
                    </ul>
                </nav>

                {/* Genome Metadata Section */}
                <section>
                    {genomeMeta ? (
                        <div className="genome-meta-info">
                            <h2><i>{genomeMeta.species}</i>: {genomeMeta.isolate_name}</h2>
                            <p><strong>Assembly Name:&nbsp;</strong>
                                <a href={genomeMeta.fasta_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.assembly_name}
                                    <span className="icon icon-common icon-download"
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            </p>
                            <p><strong>Annotations:&nbsp;</strong>
                                <a href={genomeMeta.gff_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.gff_file}
                                    <span className="icon icon-common icon-download"
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            </p>
                            {/* commented ENA link for now till the assemblies become public */}
                            {/*<p><strong>ENA Accession:&nbsp;</strong>*/}
                            {/*    <a*/}
                            {/*        href={*/}
                            {/*            genomeMeta.assembly_accession*/}
                            {/*                ? `${process.env.REACT_APP_ENA_BASE_URL}${genomeMeta.assembly_accession}`*/}
                            {/*                : undefined*/}
                            {/*        }*/}
                            {/*        target="_blank"*/}
                            {/*        rel="noopener noreferrer">*/}
                            {/*        {genomeMeta.assembly_accession ? `XX000000${genomeMeta.assembly_accession}` : "Not Available"}*/}
                            {/*        <span className="icon icon-common icon-external-link-alt"*/}
                            {/*              style={{paddingLeft: '5px'}}></span>*/}
                            {/*    </a>*/}
                            {/*</p>*/}
                        </div>
                    ) : (
                        <p>Loading genome meta information...</p>
                    )}
                </section>
                {/* JBrowse Component Section */}
                <div style={{paddingTop: '20px', height: '425px'}}>
                    {viewState ? (
                        <div className={styles.jbrowseViewer}>
                            <div className={styles.jbrowseContainer}>
                                <JBrowseApp viewState={viewState}

                                />
                            </div>
                        </div>
                    ) : (
                        <p>Loading Genome Viewer...</p>
                    )}
                </div>

                {/* Gene Search Section */}
                <div className={styles.geneSearchContainer}>
                    <section>
                        <GeneSearchWithFilters
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedGenomes={
                                genomeMeta ? [{
                                    id: genomeMeta.id,
                                    isolate_name: genomeMeta.isolate_name,
                                    type_strain: genomeMeta.type_strain
                                }] : []
                            }
                            results={geneResults}
                            onSortClick={handleGeneSortClick}
                            sortField={sortField}
                            sortOrder={sortOrder}
                            linkData={linkData}
                            viewState={viewState}
                        />
                    </section>
                </div>


            </section>
        </div>
    );
};

export default GeneViewerPage;

