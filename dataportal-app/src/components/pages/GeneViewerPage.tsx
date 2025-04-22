import React, {useEffect, useMemo, useState} from 'react';
import {useParams} from 'react-router-dom';
import getAssembly from '@components/organisms/Gene/GeneViewer/assembly';
import getTracks from '@components/organisms/Gene/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/Gene/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/Gene/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import "./GeneViewerPage.module.scss";
import {GenomeService} from "../../services/genomeService";
import {GeneService} from '../../services/geneService';
import {JBrowseApp} from "@jbrowse/react-app";
import {GenomeMeta} from "../../interfaces/Genome";
import {GeneMeta} from "../../interfaces/Gene";
import {getEssentialityDataUrl, SPINNER_DELAY, ZOOM_LEVELS} from "../../utils/appConstants";
import GeneSearchForm from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm";
import GeneViewerLegends from "@components/molecules/GeneViewerLegends";

const GeneViewerPage: React.FC = () => {
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [totalPages, setTotalPages] = useState(1);

    const [sortField, setSortField] = useState<string>('locus_tag');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const {strainName} = useParams<{ strainName?: string }>();
    const searchParams = new URLSearchParams(location.search);
    const geneId = searchParams.get('locus_tag');
    const [height, setHeight] = useState(450);

    const [includeEssentiality, setIncludeEssentiality] = useState(true);
    const selectedSpecies = useMemo(() => [], []);

    const spinner = loading && (
        <div className={styles.spinnerOverlay}>
            <div className={styles.spinner}></div>
        </div>
    );

    useEffect(() => {
        const fetchGeneAndGenomeMeta = async () => {
            setLoading(true); // Show spinner
            try {
                if (geneId) {
                    const geneResponse = await GeneService.fetchGeneByLocusTag(geneId);
                    setGeneMeta(geneResponse);

                    const genomeResponse = await GenomeService.fetchGenomeByIsolateNames([geneResponse.isolate_name]);
                    setGenomeMeta(genomeResponse[0]);
                } else if (strainName) {
                    const genomeResponse = await GenomeService.fetchGenomeByIsolateNames([strainName]);
                    setGenomeMeta(genomeResponse[0]);
                }

                // Adjust height based on essentiality track
                // setHeight(genomeMeta?.type_strain ? 300 : 300);

            } catch (error) {
                console.error('Error fetching gene/genome meta information', error);
            } finally {
                setTimeout(() => setLoading(false), SPINNER_DELAY); // Hide spinner after delay
            }
        };

        fetchGeneAndGenomeMeta();
    }, [geneId, strainName]);

    const assembly = useMemo(() => {
        if (genomeMeta) {
            // console.log("base fasta indexes path: " + process.env.REACT_APP_ASSEMBLY_INDEXES_PATH)
            return getAssembly(genomeMeta, process.env.REACT_APP_ASSEMBLY_INDEXES_PATH
                ? process.env.REACT_APP_ASSEMBLY_INDEXES_PATH : '');
        }
        return null;
    }, [genomeMeta]);

    const tracks = useMemo(() => {
        // console.log("base gff indexes path: " + process.env.REACT_APP_GFF_INDEXES_PATH)
        return genomeMeta
            ? getTracks(
                genomeMeta,
                process.env.REACT_APP_GFF_INDEXES_PATH
                    ? process.env.REACT_APP_GFF_INDEXES_PATH : '',
                getEssentialityDataUrl(genomeMeta.isolate_name),
                includeEssentiality
            ) : [];
    }, [genomeMeta, includeEssentiality]);

    const selectedGenomes = useMemo(() => {
        return genomeMeta
            ? [{
                id: genomeMeta.isolate_name,
                isolate_name: genomeMeta.isolate_name,
                type_strain: genomeMeta.type_strain
            }]
            : [];
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
    const {viewState, initializationError} = useGeneViewerState(
        assembly,
        tracks,
        sessionConfig,
        getEssentialityDataUrl(genomeMeta?.isolate_name || ''));

    useEffect(() => {
        const waitForInitialization = async () => {
            if (viewState && geneMeta) {
                const linearGenomeView = viewState.session.views[0];

                if (linearGenomeView?.type === 'LinearGenomeView') {
                    console.log('Waiting for LinearGenomeView to initialize...');

                    const waitForReady = async () => {
                        const maxRetries = 2; // Retry for a maximum of 10 times (200 milliseconds each)
                        let retries = 0;

                        while (!linearGenomeView.initialized && retries < maxRetries) {
                            console.log(`Retry ${retries + 1}: LinearGenomeView not initialized yet.`);
                            await new Promise(resolve => setTimeout(resolve, 200)); // Wait 200ms
                            retries++;
                        }

                        if (!linearGenomeView.initialized) {
                            console.error('LinearGenomeView failed to initialize within the timeout period.');
                            return;
                        }

                        // Once initialized, execute the navigation and zoom logic
                        console.log('LinearGenomeView initialized:', linearGenomeView.initialized);

                        try {
                            setLoading(true); // Show spinner
                            const locationString = `${geneMeta.seq_id}:${geneMeta.start_position}..${geneMeta.end_position}`;
                            console.log('Navigating to:', locationString);

                            // Perform navigation
                            linearGenomeView.navToLocString(locationString);

                            // Apply zoom with a delay
                            setTimeout(() => {
                                linearGenomeView.zoomTo(ZOOM_LEVELS.NAV);
                                console.log('Zoom applied');
                                setLoading(false); // Hide spinner after zoom
                            }, 200);
                        } catch (error) {
                            console.error('Error during navigation or zoom:', error);
                            setLoading(false); // Hide spinner on error
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


    useEffect(() => {
        if (viewState) {
            setLoading(true); // Show spinner while JBrowse refreshes
            const refreshTimeout = setTimeout(() => setLoading(false), SPINNER_DELAY);
            return () => clearTimeout(refreshTimeout);
        }
    }, [viewState]);


    if (!viewState) {
        return <p>Loading Genome Viewer...</p>;
    } else {

        //refresh essentiality track
        const view = viewState.session.views?.[0];
        viewState.session.tracks.forEach((track: any) => {
            const trackId = track.trackId || track.get('trackId');
            if (trackId === 'structural_annotation') {
                view.hideTrack(trackId);
                view.showTrack(trackId);
            }
        });

        // if (viewState?.session) {
        //     const activeWidgets = viewState.session.activeWidgets
        //     const alreadyOpen =
        //         Array.isArray(activeWidgets) && activeWidgets.includes('BaseFeatureWidget')
        //
        //     if (!alreadyOpen) {
        //         try {
        //             const widget = viewState.session.addWidget('BaseFeatureWidget', 'featureDetails')
        //             viewState.session.showWidget(widget)
        //         } catch (err) {
        //             console.warn('Could not show feature panel:', err)
        //         }
        //     }
        // }
    }

    const handleRemoveGenome = (isolate_name: string) => {
        //pass
    };


    const handleGeneSearch = async () => {
        if (genomeMeta?.isolate_name) {
            setLoading(true);
            const response = await GeneService.fetchGeneBySearch(genomeMeta.isolate_name, geneSearchQuery);
            setGeneResults(response.results || []);
            setTotalPages(response.num_pages || 1);
            setTimeout(() => setLoading(false), SPINNER_DELAY);
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
            {spinner} {/* Display spinner */}
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
                <section className={styles.infoSection}>
                    <div className={styles.infoGrid}>

                        {/* Left pane: Genome metadata */}
                        <div className={styles.leftPane}>
                            {genomeMeta ? (
                                <div className="genome-meta-info">
                                    <h2><i>{genomeMeta.species_scientific_name}</i>: {genomeMeta.isolate_name}</h2>
                                    <p><strong>Assembly Name:&nbsp;</strong>
                                        <a href={genomeMeta.fasta_url} target="_blank" rel="noopener noreferrer">
                                            {genomeMeta.assembly_name}
                                            <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                                                  style={{paddingLeft: '5px'}}></span>
                                        </a>
                                    </p>
                                    <p><strong>Annotations:&nbsp;</strong>
                                        <a href={genomeMeta.gff_url} target="_blank" rel="noopener noreferrer">
                                            {genomeMeta.gff_file}
                                            <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                                                  style={{paddingLeft: '5px'}}></span>
                                        </a>
                                    </p>
                                </div>
                            ) : (
                                <p>Loading genome meta information...</p>
                            )}
                        </div>
                        {/* Right pane: Legend */}
                        <div className={styles.rightPane}>
                            {genomeMeta && (
                                <GeneViewerLegends showEssentiality={genomeMeta.type_strain === true}/>
                            )}
                        </div>

                    </div>
                </section>
                {/* Essentiality Toggle Checkbox */}
                {genomeMeta?.type_strain && (
                    <div className={styles.essentialityToggleContainer}>
                        <label htmlFor="toggleEssentiality" className={styles.essentialityLabel}>
                            <input
                                type="checkbox"
                                id="toggleEssentiality"
                                checked={includeEssentiality}
                                onChange={() => setIncludeEssentiality(prev => !prev)}
                                className={styles.essentialityCheckbox}
                            />
                            Include Essentiality in viewer
                        </label>
                    </div>
                )}

                {/* JBrowse Component Section */}
                <div
                    style={{
                        // paddingTop: '5px',
                        maxHeight: `${height}px`,
                        overflowY: 'auto',
                        overflowX: 'auto',
                        // border: '1px solid #ddd',
                    }}
                >
                    {viewState ? (
                        <div className={styles.jbrowseViewer}>
                            <div className={styles.jbrowseContainer}>
                                <JBrowseApp viewState={viewState}/>
                            </div>
                        </div>
                    ) : (
                        <p>Loading Genome Viewer...</p>
                    )}
                </div>


                {/* Gene Search Section */}
                <div className={styles.geneSearchContainer}>
                    <section>
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
                            linkData={linkData}
                            viewState={viewState}
                            setLoading={setLoading}
                            handleRemoveGenome={handleRemoveGenome}
                        />
                        {/*)}*/}
                    </section>

                </div>


            </section>
        </div>
    );
};

export default GeneViewerPage;

