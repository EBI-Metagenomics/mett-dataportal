import React, {lazy, useEffect, useMemo, useState} from 'react';
import {ThemeProvider} from '@mui/material';
import {makeStyles} from 'tss-react/mui';
import {useParams, useLocation} from 'react-router-dom';
import {JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {getData} from '../../services/api';
import getAssembly from '@components/organisms/GeneViewer/assembly';
import getTracks from '@components/organisms/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/GeneViewer/geneViewerState';
import PluginManager from '@jbrowse/core/PluginManager';
import LinearGenomeViewPlugin from '@jbrowse/plugin-linear-genome-view';
import {configSchema, stateModelFactory} from '@jbrowse/core/BaseFeatureWidget';
import BaseFeatureDetails from '@jbrowse/core/BaseFeatureWidget/BaseFeatureDetail';
import WidgetType from '@jbrowse/core/pluggableElementTypes/WidgetType';
import {createJBrowseTheme} from '@jbrowse/core/ui';
import HierarchicalTrackSelector
    from '@jbrowse/plugin-data-management/dist/HierarchicalTrackSelectorWidget/components/HierarchicalTrackSelector';
import {
    HierarchicalTrackSelectorModel
} from '@jbrowse/plugin-data-management/dist/HierarchicalTrackSelectorWidget/model';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/GeneSearch/GeneSearchForm";
import {fetchGenomesBySearch} from "../../services/genomeService";
import {fetchGeneBySearch, fetchGenesByGenome} from "../../services/geneService";


const DrawerWidget = lazy(() => import('../atoms/DrawerWidget'))


export interface GeneMeta {
    id: number;
    seq_id: string;
    gene_name: string;
    description: string;
    strain_id: number;
    strain: string;
    assembly: string;
    locus_tag: string;
    cog: string | null;
    kegg: string | null;
    pfam: string | null;
    interpro: string | null;
    dbxref: string | null;
    ec_number: string | null;
    product: string | null;
    start_position: number | null;
    end_position: number | null;
    annotations: Record<string, any> | null;
}

export interface GenomeMeta {
    species: number;
    id: number;
    common_name: string;
    isolate_name: string;
    assembly_name: string;
    assembly_accession: string;
    fasta_file: string;
    gff_file: string;
    fasta_url: string;
    gff_url: string;
}

const useStyles = makeStyles()(theme => ({
    root: {
        display: 'grid',
        height: '100vh',
        width: '100%',
        colorScheme: theme.palette.mode,
    },
    appContainer: {
        gridColumn: 'main',
        display: 'grid',
        gridTemplateRows: '[menubar] min-content [components] auto',
        height: '100vh',
    },
    appBar: {
        flexGrow: 1,
        gridRow: 'menubar',
    },
}));

const GeneViewerPage: React.FC = () => {

        const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
        const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
        const [pluginManager, setPluginManager] = useState<PluginManager | null>(null);

        // const [selectedGenomeId, setSelectedGenomeId] = useState<number>(); // State to manage selected genome
        const [geneSearchQuery, setGeneSearchQuery] = useState('');
        const [geneResults, setGeneResults] = useState<any[]>([]);
        const [totalPages, setTotalPages] = useState(1);

        const [geneCurrentPage, setGeneCurrentPage] = useState(1);

        const {geneId} = useParams<{ geneId?: string }>();
        const searchParams = new URLSearchParams(location.search);
        const genomeId = searchParams.get('genomeId');

        // Initialize PluginManager and configure it to use the hierarchical track selector
        useEffect(() => {
            const manager = new PluginManager([new LinearGenomeViewPlugin()]);
            manager.createPluggableElements();
            manager.configure();

            const baseFeatureWidgetType = new WidgetType({
                name: 'BaseFeatureWidget',
                heading: 'Feature details',
                configSchema,
                stateModel: stateModelFactory(manager),
                ReactComponent: lazy(
                    () => import('@jbrowse/core/BaseFeatureWidget/BaseFeatureDetail'),
                ),
            });

            manager.addWidgetType(() => baseFeatureWidgetType);

            // Add the widget to the session
            if (localViewState?.session) {
                // Check if widget exists first and add it if not
                if (!localViewState.session.widgets.has('BaseFeatureWidget')) {
                    const widget = localViewState.session.addWidget(
                        'BaseFeatureWidget',
                        'BaseFeatureWidget',
                        {
                            featureData: {
                                // Add relevant feature data here, if needed
                            },
                        }
                    );
                    localViewState.session.showWidget(widget); // Make the widget visible
                }
            }

            console.log('BaseFeatureWidget added:', localViewState?.session.widgets.has('BaseFeatureWidget'));

            setPluginManager(manager);
        }, []);

        // Fetch gene and genome metadata
        useEffect(() => {
            const fetchGeneAndGenomeMeta = async () => {
                try {
                    if (geneId) {
                        const geneResponse = await getData(`/genes/${geneId}`);
                        console.log('Gene data fetched:', geneResponse);
                        setGeneMeta(geneResponse);

                        const genomeResponse = await getData(`/genomes/${geneResponse.strain_id}`);
                        console.log('Genome data fetched:', genomeResponse);
                        setGenomeMeta(genomeResponse);
                    } else if (genomeId) {
                        const genomeResponse = await getData(`/genomes/${genomeId}`);
                        console.log('Genome data fetched:', genomeResponse);
                        setGenomeMeta(genomeResponse);
                    }
                } catch (error) {
                    console.error('Error fetching gene/genome meta information', error);
                }
            };

            fetchGeneAndGenomeMeta();
        }, [geneId, genomeId]);

        const assembly = useMemo(() => {
            const result = genomeMeta ? getAssembly(genomeMeta, genomeMeta.fasta_url.replace(/\/[^/]+$/, '')) : null;
            console.log('Assembly computed:', result);
            return result;
        }, [genomeMeta]);

        const tracks = useMemo(() => {
            const result = genomeMeta ? getTracks(genomeMeta, genomeMeta.gff_url.replace(/\/[^/]+$/, '')) : [];
            console.log('Tracks computed:', result);
            return result;
        }, [genomeMeta]);

        const sessionConfig = useMemo(() => {
            if (genomeMeta && geneMeta) {
                const config = getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
                config.view.trackSelectorType = 'hierarchical';
                return config;
            }
            return null;
        }, [genomeMeta, geneMeta, assembly, tracks]);

        const localViewState = useGeneViewerState(assembly, tracks, sessionConfig);
        console.log('Local View State:', localViewState);

        const renderTrackSelector = () => {
            if (!localViewState?.session?.views?.length) {
                return <p>Loading tracks...</p>;
            }

            const trackSelectorModel = localViewState.session.views[0]; // Assuming the first view
            console.log('TrackSelectorModel:', trackSelectorModel);

            if (trackSelectorModel.trackSelectorType === 'hierarchical') {
                return (
                    <div>
                        <p>Using default hierarchical track selector from JBrowse.</p>
                    </div>
                );
            }

            return <p>Track Selector not configured.</p>;
        };

        if (!localViewState) {
            return <p>Loading Genome Viewer...</p>;
        }

        const drawerVisible = true;
        const theme = createJBrowseTheme();
        const sessionWithFocusedView = {
            ...localViewState.session,
            setFocusedWidgetId: (widgetId: string) => {
                localViewState.session.activeWidgets.set(widgetId, true);
            }
        };

        // Log all widgets in the session
        console.log('Session Widgets:', localViewState?.session?.widgets);

        // Access the widget directly using the key 'BaseFeatureWidget'
        const featureWidgetModel = localViewState?.session?.widgets?.get('BaseFeatureWidget');

        // Log the result to check if the widget is found
        console.log('featureWidgetModel:', featureWidgetModel);

        const handleGeneSearch = async () => {
            if (genomeId) {
                const response = await fetchGeneBySearch(parseInt(genomeId, 10), geneSearchQuery);
                setGeneResults(response.results || []);
                setTotalPages(response.num_pages || 1);
            }
        };

        const linkData = {
            template: '/gene-viewer/gene/${id}/details?genomeId=${strain_id}',
            alias: 'Select'
        };


        // const hierarchicalTrackSelectorModel = localViewState.session.views[0].activateTrackSelector() as HierarchicalTrackSelectorModel;

        return (
            <div style={{padding: '20px'}}>

                {/* Breadcrumb Section */}
                <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                    <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                        <li className="vf-breadcrumbs__item">
                            <a href="/" className="vf-breadcrumbs__link">Search</a>
                        </li>
                        <li className="vf-breadcrumbs__item">
                            <b>Genome View</b>
                        </li>
                        <li className="vf-breadcrumbs__item">
                            <a href="/" className="vf-breadcrumbs__link">Related Genomes</a>
                        </li>
                    </ul>
                </nav>

                {/* Genome Metadata Section */}
                <section style={{marginTop: '20px'}}>
                    {genomeMeta ? (
                        <div className="genome-meta-info">
                            <h2>{genomeMeta.species}: {genomeMeta.isolate_name}</h2>
                            <p><strong>Assembly Name:&nbsp;</strong>
                                <a href={genomeMeta.fasta_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.assembly_name}
                                </a>
                            </p>
                            <p><strong>Annotations:&nbsp;</strong>
                                <a href={genomeMeta.gff_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.gff_file}
                                </a>
                            </p>
                            <p><strong>ENA Accession:&nbsp;</strong>
                                <a href={genomeMeta.gff_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.assembly_accession}
                                </a>
                            </p>

                        </div>
                    ) : (
                        <p>Loading genome meta information...</p>
                    )}
                </section>
                {/* Gene Search Section */}
                <div style={{padding: '20px'}}>
                    <section style={{marginTop: '20px'}}>
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedGenomes={genomeId ? [{id: parseInt(genomeId, 10), name: ''}] : []}
                            results={geneResults}
                            onSortClick={(sortField) => console.log('Sort by:', sortField)}
                            currentPage={geneCurrentPage}
                            totalPages={totalPages}
                            handlePageClick={(page) => setGeneCurrentPage(page)}
                            linkData={linkData}
                            viewState={localViewState}
                        />
                    </section>
                </div>
                {/* JBrowse Component Section */}
                <section style={{marginTop: '20px'}}>
                    <div className={styles.sidePanel} style={{width: '75%', float: 'left'}}>
                        {localViewState ? (
                            <div className={styles.geneViewerPage} style={{width: '100%'}}>
                                <div className={styles.jbrowseContainer} style={{width: '100%'}}>
                                    <JBrowseLinearGenomeView viewState={localViewState}/>
                                </div>
                            </div>
                        ) : (
                            <p>Loading Genome Viewer...</p>
                        )}
                    </div>
                    <div className={styles.sidePanel} style={{width: '25%', float: 'right'}}>
                        <h4>Track Selector</h4>

                        <ThemeProvider theme={createJBrowseTheme()}>
                            <HierarchicalTrackSelector
                                model={localViewState.session.views[0].activateTrackSelector() as HierarchicalTrackSelectorModel}
                                toolbarHeight={500}/>

                            {
                                featureWidgetModel ? (
                                    <BaseFeatureDetails model={featureWidgetModel}/>
                                ) : (
                                    <p>No feature details available</p>
                                )
                            }

                            {/*<BaseFeatureDetails model={model.widget}/>*/}
                        </ThemeProvider>

                    </div>


                </section>
            </div>
        )
            ;
    }
;

export default GeneViewerPage;
