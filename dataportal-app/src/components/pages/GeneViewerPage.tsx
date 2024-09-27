import React, {useEffect, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {assemblyConfig} from '../organisms/GeneViewer/assemblyConfig';
import {trackConfig} from '../organisms/GeneViewer/trackConfig';
import {useParams} from 'react-router-dom';
import {getData} from "../../services/api";

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

interface GenomeMeta {
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
    const [viewState, setViewState] = useState<any>(null);
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);

    const {geneId, genomeId} = useParams<{ geneId?: string; genomeId?: string }>();

    useEffect(() => {
        if (geneId) {
            // Fetch gene meta information along with genome info
            const fetchGeneAndGenomeMeta = async () => {
                try {
                    const geneResponse = await getData(`/genes/${geneId}`);
                    console.log("Gene Response:", geneResponse);
                    const geneData = geneResponse;

                    if (!geneData || !geneData.strain_id) {
                        console.error("Gene data is undefined or missing strain_id.");
                        return;
                    }


                    setGeneMeta(geneData);

                    const genomeResponse = await getData(`/genomes/${geneData.strain_id}`);
                    console.log("Genome Response:", genomeResponse);
                    const genomeData = genomeResponse;

                    if (!genomeData) {
                        console.error("Genome data is undefined or null.");
                        return;
                    }
                    setGenomeMeta(genomeData);

                    initializeJBrowse(genomeData.fasta_file, genomeData.gff_file);
                } catch (error) {
                    console.error("Error fetching gene/genome meta information", error);
                }
            };
            fetchGeneAndGenomeMeta();
        } else if (genomeId) {
            // Fetch genome information if only genomeId is provided
            const fetchGenomeMeta = async () => {
                try {
                    const response = await getData(`/genomes/${genomeId}`);
                    const genomeData = response.data;
                    setGenomeMeta(genomeData);

                    initializeJBrowse(genomeData.fasta_file, genomeData.gff_file);
                } catch (error) {
                    console.error("Error fetching genome meta information", error);
                }
            };
            fetchGenomeMeta();
        }
    }, [geneId, genomeId]);

    const initializeJBrowse = (fastaLink: string, gffLink: string) => {
        // Set up JBrowse2 configuration with dynamic assembly and track links
        const config = {
            assembly: {
                ...assemblyConfig,
                sequence: {
                    ...assemblyConfig.sequence,
                    adapter: {
                        ...assemblyConfig.sequence.adapter,
                        fastaLocation: {uri: fastaLink},
                        faiLocation: {uri: `${fastaLink}.fai`},
                    },
                },
            },
            tracks: [
                {
                    ...trackConfig[0],
                    adapter: {
                        ...trackConfig[0].adapter,
                        gffGzLocation: {uri: gffLink},
                        index: {location: {uri: `${gffLink}.tbi`}},
                    },
                },
            ],
            defaultSession: {
                name: 'My Gene Viewer Session',
                view: {
                    id: 'linearGenomeView',
                    type: 'LinearGenomeView',
                    displayedRegions: [
                        {
                            assemblyName: assemblyConfig.name,
                            refName: 'BU_ATCC8492', // Adjust accordingly based on your needs
                            start: 0,
                            end: 50000, // Adjust the range if necessary
                        },
                    ],
                },
            },
        };

        const newViewState = createViewState(config);
        setViewState(newViewState);
    };

    return (
        <div style={{padding: '20px'}}>
            <h1>Gene Viewer</h1>
            {geneId && geneMeta ? (
                <div className="gene-meta-info">
                    <h2>{geneMeta.strain}: {geneMeta.gene_name}</h2>
                    <p><strong>Description:</strong> {geneMeta.description}</p>
                    <p><strong>Locus Tag:</strong> {geneMeta.locus_tag}</p>
                    <p><strong>Assembly:</strong> {geneMeta.assembly}</p>
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
            ) : genomeId && genomeMeta ? (
                <div className="genome-meta-info">
                    <h2>Genome: {genomeMeta.common_name}</h2>
                    <p><strong>Species:</strong> {genomeMeta.species}</p>
                    <p><strong>Isolate Name:</strong> {genomeMeta.isolate_name}</p>
                    <p><strong>Assembly Name:</strong> {genomeMeta.assembly_name}</p>
                    <p><strong>Assembly Accession:</strong> {genomeMeta.assembly_accession}</p>
                    <p><strong>FASTA:</strong> <a href={genomeMeta.fasta_file} target="_blank"
                                                  rel="noopener noreferrer">Download FASTA</a></p>
                    <p><strong>GFF:</strong> <a href={genomeMeta.gff_file} target="_blank" rel="noopener noreferrer">Download
                        GFF</a></p>
                </div>
            ) : (
                <p>Loading meta information...</p>
            )}

            {viewState ? (
                <div style={{width: '100%', height: '600px'}}>
                    <JBrowseLinearGenomeView viewState={viewState}/>
                </div>
            ) : (
                <div>Loading Genome Viewer...</div>
            )}
        </div>
    );
};

export default GeneViewerPage;
