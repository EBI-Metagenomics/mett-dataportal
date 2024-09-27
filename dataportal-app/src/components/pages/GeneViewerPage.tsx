import React, {useEffect, useState} from 'react';
import {createViewState, JBrowseLinearGenomeView} from '@jbrowse/react-linear-genome-view';
import {assemblyConfig} from '../organisms/GeneViewer/assemblyConfig';
import {trackConfig} from '../organisms/GeneViewer/trackConfig';
import axios from 'axios';
import {useParams} from 'react-router-dom';

interface GeneMeta {
    strain: string;
    geneName: string;
    description: string;
    locusTag: string;
    enaAccession: string;
    assemblyLink: string;
    annotationsLink: string;
}

interface GenomeMeta {
    genomeName: string;
    assemblyName: string;
    enaAccession: string;
    fastaLink: string;
    gffLink: string;
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
                    const geneResponse = await axios.get<GeneMeta>(`/api/genes/${geneId}`);
                    setGeneMeta(geneResponse.data);

                    const genomeResponse = await axios.get<GenomeMeta>(`/api/genomes/${geneResponse.data.strain}`);
                    setGenomeMeta(genomeResponse.data);

                    initializeJBrowse(genomeResponse.data.fastaLink, genomeResponse.data.gffLink);
                } catch (error) {
                    console.error("Error fetching gene/genome meta information", error);
                }
            };
            fetchGeneAndGenomeMeta();
        } else if (genomeId) {
            // Fetch genome information if only genomeId is provided
            const fetchGenomeMeta = async () => {
                try {
                    const response = await axios.get<GenomeMeta>(`/api/genomes/${genomeId}`);
                    setGenomeMeta(response.data);

                    initializeJBrowse(response.data.fastaLink, response.data.gffLink);
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
                    <h2>{geneMeta.strain}: {geneMeta.geneName}</h2>
                    <p><strong>Description:</strong> {geneMeta.description}</p>
                    <p><strong>Locus Tag:</strong> {geneMeta.locusTag}</p>
                    <p><strong>ENA Accession:</strong> <a href={geneMeta.enaAccession} target="_blank"
                                                          rel="noopener noreferrer">{geneMeta.enaAccession}</a></p>
                    <p><strong>Assembly:</strong> <a href={geneMeta.assemblyLink} target="_blank"
                                                     rel="noopener noreferrer">Download Assembly</a></p>
                    <p><strong>Annotations:</strong> <a href={geneMeta.annotationsLink} target="_blank"
                                                        rel="noopener noreferrer">Download Annotations</a></p>
                </div>
            ) : genomeId && genomeMeta ? (
                <div className="genome-meta-info">
                    <h2>Genome: {genomeMeta.genomeName}</h2>
                    <p><strong>Assembly Name:</strong> {genomeMeta.assemblyName}</p>
                    <p><strong>ENA Accession:</strong> <a href={genomeMeta.enaAccession} target="_blank"
                                                          rel="noopener noreferrer">{genomeMeta.enaAccession}</a></p>
                    <p><strong>FASTA:</strong> <a href={genomeMeta.fastaLink} target="_blank" rel="noopener noreferrer">Download
                        FASTA</a></p>
                    <p><strong>GFF:</strong> <a href={genomeMeta.gffLink} target="_blank" rel="noopener noreferrer">Download
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
