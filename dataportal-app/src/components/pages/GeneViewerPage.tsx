import React, {useEffect, useRef, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {useParams} from 'react-router-dom';
import {getData} from "../../services/api";
import getAssembly from "@components/organisms/GeneViewer/assembly";
import getTracks from "@components/organisms/GeneViewer/tracks";

interface GeneMeta {
    id: number;
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
    const [viewerReady, setViewerReady] = useState<boolean>(false);
    const viewStateRef = useRef<any>(null);

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


    // Initialize JBrowse when viewer data is ready
    useEffect(() => {
        if (!genomeMeta) return;

        const initializeViewer = async () => {
            try {
                const assembly = getAssembly(genomeMeta);
                const tracks = getTracks(genomeMeta);

                // Ensure the assembly and tracks are properly loaded
                if (!assembly || tracks.length === 0) {
                    console.warn("Assembly or tracks are not fully loaded yet");
                    return;
                } else {
                    console.log('everything loaded successfully...');
                }

                viewStateRef.current = createViewState({
                    assembly,
                    tracks,
                    location: 'all',
                    defaultSession: {
                        name: 'Gene Viewer Session',
                        view: {
                            id: 'linearGenomeView',
                            type: 'LinearGenomeView',
                            tracks: [
                                {
                                    type: 'FeatureTrack',
                                    trackId: 'structural_annotation',
                                    configuration: 'structural_annotation',
                                    visible: true,
                                },
                            ],
                            displayedRegions: [
                                {
                                    assemblyName: genomeMeta.assembly_name,
                                    refName: genomeMeta.assembly_name,
                                    start: geneMeta?.start_position || 0,
                                    end: geneMeta?.end_position || 1000,
                                },
                            ],
                        },
                    },
                });

                setViewerReady(true);
            } catch (error) {
                console.error('Error initializing JBrowse viewer:', error);
            }
        };

        initializeViewer();
    }, [genomeMeta]);


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

            {viewerReady && viewStateRef.current ? (
                <JBrowseLinearGenomeView viewState={viewStateRef.current}/>
            ) : (
                <p>Loading Genome Viewer...</p>
            )}
        </div>
    );
};

export default GeneViewerPage;
