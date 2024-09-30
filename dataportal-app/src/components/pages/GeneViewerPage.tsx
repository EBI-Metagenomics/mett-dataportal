import React, { useEffect, useRef, useState } from 'react';
import { createViewState, JBrowseLinearGenomeView } from '@jbrowse/react-linear-genome-view';
import { useParams } from 'react-router-dom';
import { getData } from "../../services/api";
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
}

const GeneViewerPage: React.FC = () => {
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [fastaContent, setFastaContent] = useState<string | null>(null);
    const [gffContent, setGffContent] = useState<string | null>(null);
    const [viewerReady, setViewerReady] = useState<boolean>(false);
    const viewStateRef = useRef<any>(null);

    const { geneId, genomeId } = useParams<{ geneId?: string; genomeId?: string }>();

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

    // Fetch FASTA and GFF content
    useEffect(() => {
        if (!genomeMeta) return;

        const fetchFileContent = async (url: string, setContent: React.Dispatch<React.SetStateAction<string | null>>) => {
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Failed to fetch file from ${url}`);
                const text = await response.text();
                setContent(text.split('\n').slice(0, 10).join('\n'));  // Get first 10 lines of the file
            } catch (error) {
                console.error('Error fetching file:', error);
                setContent('Error fetching file');
            }
        };

        const fetchData = async () => {
            await Promise.all([
                fetchFileContent(genomeMeta.fasta_file, setFastaContent),
                fetchFileContent(genomeMeta.gff_file, setGffContent),
            ]);
            setViewerReady(true);
        };

        fetchData();
    }, [genomeMeta]);

    // Initialize JBrowse when viewer data is ready
    useEffect(() => {
    if (!viewerReady || !genomeMeta) return;

    try {
        const assembly = getAssembly(genomeMeta);
        const tracks = getTracks(genomeMeta);

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
                            trackId: 'annotations',
                            configuration: 'annotations',
                            visible: true,
                        },
                    ],
                    displayedRegions: [
                        {
                            assemblyName: assembly.name,
                            refName: assembly.name,
                            start: 0,
                            end: 50000,
                        },
                    ],
                },
            },
        });

        // setForceRender(true);  // Only if you need to force re-render
    } catch (error) {
        console.error('Error initializing JBrowse viewer:', error);
    }
}, [viewerReady, genomeMeta]);

    return (
        <div style={{ padding: '20px' }}>
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
                        <p><strong>FASTA:</strong> <a href={genomeMeta.fasta_file} target="_blank" rel="noopener noreferrer">Download FASTA</a></p>
                        <p><strong>GFF:</strong> <a href={genomeMeta.gff_file} target="_blank" rel="noopener noreferrer">Download GFF</a></p>
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
                    <p><strong>Start Position:</strong> {geneMeta.start_position !== null ? geneMeta.start_position : 'N/A'}</p>
                    <p><strong>End Position:</strong> {geneMeta.end_position !== null ? geneMeta.end_position : 'N/A'}</p>
                    <p><strong>Annotations:</strong> {geneMeta.annotations ? JSON.stringify(geneMeta.annotations) : 'N/A'}</p>
                </div>
            )}

            <h2>FASTA File Preview:</h2>
            <pre>{fastaContent ? fastaContent : 'Loading FASTA file...'}</pre>

            <h2>GFF File Preview:</h2>
            <pre>{gffContent ? gffContent : 'Loading GFF file...'}</pre>

            {viewerReady && viewStateRef.current ? (
                <JBrowseLinearGenomeView viewState={viewStateRef.current} />
            ) : (
                <p>Loading Genome Viewer...</p>
            )}
        </div>
    );
};

export default GeneViewerPage;
