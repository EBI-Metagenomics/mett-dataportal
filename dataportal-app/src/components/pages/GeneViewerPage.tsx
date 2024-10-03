import React, {useEffect, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import makeWorkerInstance from '@jbrowse/react-linear-genome-view/esm/makeWorkerInstance';
import {useParams} from 'react-router-dom';
import {getData} from "../../services/api";
import getAssembly from "@components/organisms/GeneViewer/assembly";
import getTracks from "@components/organisms/GeneViewer/tracks";
import styles from "@components/pages/GeneViewerPage.module.scss";


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


    const [localViewState, setLocalViewState] = useState<any>(null);

    useEffect(() => {
        if (!genomeMeta || !geneMeta) return;
        const initializeViewState = async () => {
            try {
                const gffBaseUrl = genomeMeta.gff_url.replace(/\/[^/]+$/, '');
                const fastaBaseUrl = genomeMeta.fasta_url.replace(/\/[^/]+$/, '');
                const assembly = getAssembly(genomeMeta, fastaBaseUrl);
                const tracks = getTracks(genomeMeta, gffBaseUrl);

                console.log("Initializing with assembly and track information:");
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz`)
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.fai`)
                console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.gzi`)
                console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz`)
                console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz.tbi`)
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ix`)
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ixx`)
                console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz_meta.json`)

                console.log('Tracks:', tracks);
                console.log('Assembly:', assembly);

                const defaultSession = {
                    name: 'Gene Viewer Session',
                    view: {
                        id: 'linearGenomeView',
                        type: 'LinearGenomeView',
                        displayedRegions: [
                            {
                                refName: geneMeta.seq_id,
                                start: geneMeta?.start_position || 0,
                                end: geneMeta?.end_position || 50000,
                                assemblyName: genomeMeta.assembly_name,
                            },
                        ],
                        tracks: tracks.map(track => ({
                            id: track.trackId,
                            type: track.type,
                            configuration: track.trackId,
                            minimized: false,
                            visible: true,
                            displays: [
                                {
                                    id: track.trackId,
                                    type: 'LinearReferenceSequenceDisplay',
                                    height: 180,
                                },
                            ],
                        })),
                    },
                    hideHeader: false,
                    hideHeaderOverview: false,
                    hideNoTracksActive: false,
                    trackSelectorType: 'hierarchical',
                    trackLabels: 'overlapping',
                    showCenterLine: false,
                    showCytobandsSetting: true,
                    showGridlines: true,
                };


                const state = createViewState({
                    assembly,
                    tracks: tracks.filter(track => track.platform === 'jbrowse'),
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

                    if (state.session.view.displayedRegions.length === 0) {
                        state.session.view.setDisplayedRegions([
                            {
                                assemblyName: genomeMeta.assembly_name,
                                refName: geneMeta.seq_id,
                                start: geneMeta?.start_position || 0,
                                end: geneMeta?.end_position || 50000,
                            }
                        ]);
                    }
                }
            } catch (error) {
                console.error('Error initializing view state:', error);
            }
        };

        initializeViewState();
    }, [genomeMeta, geneMeta]);

    if (!localViewState) {
        return <p>Loading...</p>;
    }

    return (
        <div style={{padding: '20px'}}>
            <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                    <li className="vf-breadcrumbs__item">
                        <a href="/" className="vf-breadcrumbs__link">Search</a>
                    </li>
                    <li className="vf-breadcrumbs__item" aria-current="location">Genome View</li>
                </ul>
            </nav>

            {genomeMeta ? (
                <div className="genome-meta-info">
                    <div className="vf-box vf-box--primary">
                        <h2>{genomeMeta.species}: {genomeMeta.isolate_name}</h2>
                        <p><strong>Assembly Name:</strong> {genomeMeta.assembly_name}</p>
                        <p><strong>Assembly Accession:</strong> {genomeMeta.assembly_accession}</p>
                        <p><strong>FASTA:</strong> <a href={genomeMeta.fasta_url} target="_blank"
                                                      rel="noopener noreferrer">Download FASTA</a></p>
                        <p><strong>GFF:</strong> <a href={genomeMeta.gff_url} target="_blank"
                                                    rel="noopener noreferrer">Download GFF</a></p>
                    </div>
                </div>
            ) : (
                <p>Loading genome meta information...</p>
            )}

            {geneId && geneMeta && (
                <div className="gene-meta-info">
                    <h2>{geneMeta.strain}: {geneMeta.gene_name}</h2>
                    <p><strong>Description:</strong> {geneMeta.description}</p>
                    <p><strong>Locus Tag:</strong> {geneMeta.locus_tag}</p>
                    <p><strong>COG:</strong> {geneMeta.cog || 'N/A'}</p>
                    <p><strong>KEGG:</strong> {geneMeta.kegg || 'N/A'}</p>
                    <p><strong>PFAM:</strong> {geneMeta.pfam || 'N/A'}</p>
                    <p><strong>InterPro:</strong> {geneMeta.interpro || 'N/A'}</p>
                    <p><strong>DBXref:</strong> {geneMeta.dbxref || 'N/A'}</p>
                    <p><strong>EC Number:</strong> {geneMeta.ec_number || 'N/A'}</p>
                    <p><strong>Product:</strong> {geneMeta.product || 'N/A'}</p>
                    <p><strong>Start
                        Position:</strong> {geneMeta.start_position !== null ? geneMeta.start_position : 'N/A'}</p>
                    <p><strong>End Position:</strong> {geneMeta.end_position !== null ? geneMeta.end_position : 'N/A'}
                    </p>
                    <p>
                        <strong>Annotations:</strong> {geneMeta.annotations ? JSON.stringify(geneMeta.annotations) : 'N/A'}
                    </p>

                </div>
            )}

            {localViewState ? (
                <div className={styles.jbrowseContainer}>
                    <JBrowseLinearGenomeView viewState={localViewState}/>
                </div>
            ) : (
                <p>Loading Genome Viewer...</p>
            )}
        </div>
    );
};

export default GeneViewerPage;