import React, {useEffect, useRef, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {useParams} from 'react-router-dom';
import {getData} from "../../services/api";
import getAssembly from "@components/organisms/GeneViewer/assembly";
import getTracks from "@components/organisms/GeneViewer/tracks";

export interface GeneMeta {
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
    const [fastaPreview, setFastaPreview] = useState<string | null>(null);
    const [ixPreview, setIxPreview] = useState<string | null>(null);
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

    // Fetch content previews for FASTA and .ix files
    useEffect(() => {
        if (!genomeMeta) return;

        const fetchFileContent = async (url: string, setContent: React.Dispatch<React.SetStateAction<string | null>>, fileType: string) => {
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Failed to fetch ${fileType} file from ${url}`);
                const text = await response.text();
                setContent(text.split('\n').slice(0, 10).join('\n')); // Get first 10 lines of the file
            } catch (error) {
                console.error(`Error fetching ${fileType} file:`, error);
                setContent(`Error fetching ${fileType} file`);
            }
        };

        const fetchData = async () => {
            const gffBaseUrl = genomeMeta.gff_url.replace(/\/[^/]+$/, '');
            await Promise.all([
                fetchFileContent(`${genomeMeta.fasta_url}.gz.fai`, setFastaPreview, 'FASTA'),
                fetchFileContent(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ix`, setIxPreview, '.ix'),
            ]);
            setViewerReady(true);
        };

        fetchData();
    }, [genomeMeta]);

    // Initialize JBrowse
    useEffect(() => {
        if (!genomeMeta) return;

        const gffBaseUrl = genomeMeta.gff_url.replace(/\/[^/]+$/, '');
        const fastaBaseUrl = genomeMeta.fasta_url.replace(/\/[^/]+$/, '');

        console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz`)
        console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.fai`)
        console.log(`${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.gzi`)
        console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz`)
        console.log(`${gffBaseUrl}/${genomeMeta.gff_file}.gz.tbi`)
        console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ix`)
        console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ixx`)
        console.log(`${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz_meta.json`)

        const initializeViewer = async () => {
            try {
                const assembly = getAssembly(genomeMeta, fastaBaseUrl);
                const tracks = getTracks(genomeMeta, gffBaseUrl);

                if (!assembly || tracks.length === 0) {
                    console.warn("Assembly or tracks are not fully loaded yet");
                    return;
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
                                    refName: geneMeta.,
                                    start: geneMeta?.start_position || 0,
                                    end: geneMeta?.end_position || 50000,
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

            <h2>FASTA File Preview:</h2>
            <pre>{fastaPreview ? fastaPreview : 'Loading FASTA file...'}</pre>

            <h2>.ix File Preview:</h2>
            <pre>{ixPreview ? ixPreview : 'Loading .ix file...'}</pre>

            {viewerReady && viewStateRef.current ? (
                <JBrowseLinearGenomeView viewState={viewStateRef.current}/>
            ) : (
                <p>Loading Genome Viewer...</p>
            )}
        </div>
    );
};

export default GeneViewerPage;
