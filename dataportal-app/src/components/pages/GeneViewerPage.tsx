import React, {useEffect, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import makeWorkerInstance from '@jbrowse/react-linear-genome-view/esm/makeWorkerInstance';
import {useParams} from 'react-router-dom';
import {getData} from "../../services/api";
import getAssembly from "@components/organisms/GeneViewer/assembly";
import getTracks from "@components/organisms/GeneViewer/tracks";
import styles from "@components/pages/GeneViewerPage.module.scss";
import getDefaultSessionConfig from "@components/organisms/GeneViewer/defaultSessionConfig";

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
    const [localViewState, setLocalViewState] = useState<any>(null);

    const {geneId, genomeId} = useParams<{ geneId?: string; genomeId?: string }>();

    useEffect(() => {
        const fetchGeneAndGenomeMeta = async () => {
            try {
                if (geneId) {
                    const geneResponse = await getData(`/genes/${geneId}`);
                    setGeneMeta(geneResponse);

                    const genomeResponse = await getData(`/genomes/${geneResponse.strain_id}`);
                    setGenomeMeta(genomeResponse);
                } else if (genomeId) {
                    const genomeResponse = await getData(`/genomes/${genomeId}`);
                    setGenomeMeta(genomeResponse);
                }
            } catch (error) {
                console.error("Error fetching gene/genome meta information", error);
            }
        };

        fetchGeneAndGenomeMeta();
    }, [geneId, genomeId]);

    useEffect(() => {
        if (!genomeMeta || !geneMeta) return;

        const initializeViewState = async () => {
            try {
                const gffBaseUrl = genomeMeta.gff_url.replace(/\/[^/]+$/, '');
                const fastaBaseUrl = genomeMeta.fasta_url.replace(/\/[^/]+$/, '');
                const assembly = getAssembly(genomeMeta, fastaBaseUrl);
                const tracks = getTracks(genomeMeta, gffBaseUrl);

                console.log('Initializing with assembly and track information:');
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz`);
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.fai`);
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.gzi`);
                console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz`);
                console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz.tbi`);
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ix`);
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ixx`);
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz_meta.json`);

                console.log('Tracks:', tracks);
                console.log('Assembly:', assembly);

                const defaultSession = getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);

                console.log("Tracks being passed: ", tracks);
                const visibleTracks = tracks.filter(track => track.visible === true);
                console.log("Visible Tracks: ", visibleTracks);


                const state = createViewState({
                    assembly,
                    tracks: tracks.map(track => ({
                        ...track,
                        visible: true,
                    })),
                    onChange: (patch: any) => {
                        console.log(JSON.stringify(patch));
                    },
                    defaultSession,
                    configuration: {
                        rpc: {
                            defaultDriver: 'WebWorkerRpcDriver',
                        },
                    },
                    makeWorkerInstance,
                });

                setLocalViewState(state);

                const assemblyManager = state.assemblyManager;
                const assemblyInstance = assemblyManager.get(assembly.name);

                if (assemblyInstance) {
                    await assemblyInstance.load();
                }
            } catch (error) {
                console.error('Error initializing view state:', error);
            }
        };

        initializeViewState();
    }, [genomeMeta, geneMeta]);

    const renderTrackSelector = () => {
        if (!localViewState?.pluginManager?.rootModel?.views?.length) {
            return <p>Loading tracks...</p>;
        }

        const trackSelectorModel = localViewState.pluginManager.rootModel.views[0];
        const TrackSelectorComponent = trackSelectorModel.trackSelectorType;

        return <TrackSelectorComponent model={trackSelectorModel}/>;
    };

    if (!localViewState) {
        return <p>Loading...</p>;
    }

    return (
        <div style={{padding: '20px'}}>
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
            <section style={{marginTop: '20px'}}>
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
                    <h3>Track Selector</h3>
                    {renderTrackSelector()}
                </div>
            </section>
        </div>

    );
};

export default GeneViewerPage;
