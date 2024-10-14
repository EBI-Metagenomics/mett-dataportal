import React, {useEffect, useMemo, useState} from 'react';
import {JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {useParams} from 'react-router-dom';
import {getData} from '../../services/api';
import getAssembly from '@components/organisms/GeneViewer/assembly';
import getTracks from '@components/organisms/GeneViewer/tracks';
import styles from '@components/pages/GeneViewerPage.module.scss';
import getDefaultSessionConfig from '@components/organisms/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/GeneViewer/geneViewerState';
import PluginManager from '@jbrowse/core/PluginManager';
import LinearGenomeViewPlugin from '@jbrowse/plugin-linear-genome-view';
import MyCustomFeaturePanel from "@components/organisms/GeneViewer/MyCustomFeaturePanel";
import { BaseTrackModel, BaseTrackConfig } from '@jbrowse/core/pluggableElementTypes/models';



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
    species: string;
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

const GeneViewerPage: React.FC = () => {
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [pluginManager, setPluginManager] = useState<PluginManager | null>(null);

    const { geneId, genomeId } = useParams<{ geneId?: string; genomeId?: string }>();

    // Initialize PluginManager and configure it to use the hierarchical track selector
    // useEffect(() => {
    //     const manager = new PluginManager([new LinearGenomeViewPlugin()]);
    //     manager.createPluggableElements();
    //
    //     // Add the Core-preProcessTrackConfig extension point
    //     manager.addToExtensionPoint('Core-preProcessTrackConfig', (snap: BaseTrackConfig) => {
    //         snap.metadata = {
    //             ...snap.metadata,
    //             'custom info': 'Track added via plugin',
    //         };
    //         return snap;
    //     });
    //
    //     // Add the Core-extraFeaturePanel extension point
    //     manager.addToExtensionPoint(
    //         'Core-extraFeaturePanel',
    //         (DefaultFeatureExtra, { model }: { model: BaseTrackModel }) => {
    //             if (model.trackId === 'my_special_track') {
    //                 // Return the custom panel for the special track
    //                 return { name: 'Additional Info', Component: MyCustomFeaturePanel };
    //             }
    //             return DefaultFeatureExtra;
    //         },
    //     );
    //
    //     manager.configure();
    //     setPluginManager(manager); // Set the initialized PluginManager
    // }, []);

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

    return (
        <div style={{ padding: '20px' }}>
            {/* Breadcrumb Section */}
            <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                    <li className="vf-breadcrumbs__item">
                        <a href="/" className="vf-breadcrumbs__link">Search</a>
                    </li>
                    <li className="vf-breadcrumbs__item" aria-current="location">Genome View</li>
                </ul>
            </nav>

            {/* Genome Metadata Section */}
            <section style={{ marginTop: '20px' }}>
                {genomeMeta ? (
                    <div className="genome-meta-info">
                        <h2>{genomeMeta.species}: {genomeMeta.isolate_name}</h2>
                        <p><strong>Assembly Name:</strong> {genomeMeta.assembly_name}</p>
                        <p><strong>Assembly Accession:</strong> {genomeMeta.assembly_accession}</p>
                        <p><strong>FASTA:</strong> <a href={genomeMeta.fasta_url} target="_blank"
                                                      rel="noopener noreferrer">Download FASTA</a></p>
                        <p><strong>GFF:</strong> <a href={genomeMeta.gff_url} target="_blank" rel="noopener noreferrer">Download
                            GFF</a></p>
                    </div>
                ) : (
                    <p>Loading genome meta information...</p>
                )}
            </section>

            {/* JBrowse Component Section */}
            <section style={{ marginTop: '20px' }}>
                <div className={styles.sidePanel} style={{ width: '75%', float: 'left' }}>
                    {localViewState ? (
                        <div className={styles.geneViewerPage} style={{ width: '100%' }}>
                            <div className={styles.jbrowseContainer} style={{ width: '100%' }}>
                                <JBrowseLinearGenomeView viewState={localViewState} />
                            </div>
                        </div>
                    ) : (
                        <p>Loading Genome Viewer...</p>
                    )}
                </div>
                <div className={styles.sidePanel} style={{ width: '25%', float: 'right' }}>
                    <h3>Track Selector</h3>
                    {renderTrackSelector()}
                </div>
            </section>
        </div>
    );
};

export default GeneViewerPage;
