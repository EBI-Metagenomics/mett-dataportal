import React, {useEffect, useRef, useState} from 'react';
import {useParams} from 'react-router-dom';
import {createViewState, JBrowseLinearGenomeView,} from '@jbrowse/react-linear-genome-view';
import {getData} from "../../utils/api";
import getAssembly from './assembly';
import getTracks from './tracks';

interface JBrowseViewerProps {
}

export interface IsolateData {
    species: string;
    isolate_name: string;
    fasta_url: string;
    gff_url: string;
    fasta_file_name: string;
    gff_file_name: string;
}

const JBrowseViewer: React.FC<JBrowseViewerProps> = () => {
    const {isolateId} = useParams<{ isolateId: string }>();
    const [isolateData, setIsolateData] = useState<IsolateData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [fastaContent, setFastaContent] = useState<string | null>(null);
    const [gffContent, setGffContent] = useState<string | null>(null);
    const [viewerReady, setViewerReady] = useState<boolean>(false);
    const [forceRender, setForceRender] = useState<boolean>(false);
    const viewStateRef = useRef<any>(null);

    // Fetch isolate data
    useEffect(() => {
        const fetchIsolateData = async () => {
            try {
                const response = await getData(`search/jbrowse/${isolateId}`);
                if (!response) {
                    throw new Error('Failed to fetch isolate data');
                }
                setIsolateData(response);
                setLoading(false);
            } catch (err) {
                if (err instanceof Error) {
                    setError(err.message);
                } else {
                    setError('An unknown error occurred');
                }
                setLoading(false);
            }
        };

        if (isolateId) {
            fetchIsolateData();
        }
    }, [isolateId]);

    // Fetch FASTA and GFF content lazily
    useEffect(() => {
        if (!isolateData) return;

        const fetchFileContent = async (url: string, setContent: React.Dispatch<React.SetStateAction<string | null>>) => {
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Failed to fetch file from ${url}`);
                }
                const text = await response.text();
                setContent(text.split('\n').slice(0, 10).join('\n'));  // Get first 10 lines of the file
            } catch (error) {
                console.error('Error fetching file:', error);
                setContent('Error fetching file');
            }
        };

        // Fetch FASTA and GFF files, and show viewer after they are loaded
        const fetchData = async () => {
            await Promise.all([
                fetchFileContent(isolateData.fasta_url, setFastaContent),
                fetchFileContent(isolateData.gff_url, setGffContent),
            ]);
            setViewerReady(true); // Show viewer after data is fetched
        };

        fetchData();
    }, [isolateData]);

    // Initialize JBrowse when the viewer is ready
    useEffect(() => {
        if (!viewerReady || !isolateData) return;

        console.log('Initializing JBrowse Viewer');

        try {
            const assembly = getAssembly(isolateData);
            const tracks = getTracks(isolateData);

            console.log('Assembly:', assembly);
            console.log('Tracks:', tracks);

            viewStateRef.current = createViewState({
                assembly,
                tracks,
                location: 'all',
                defaultSession: {
                    name: 'Default session',
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
                    },
                },
            });
            console.log('View state created:', viewStateRef.current);
            setForceRender(true);  // Trigger re-render of the viewer
        } catch (error) {
            console.error('Error initializing JBrowse viewer:', error);
        }
    }, [viewerReady, isolateData]);

    if (loading) {
        return <p>Loading isolate data...</p>;
    }

    if (error) {
        return <p>Error: {error}</p>;
    }

    if (!isolateData) {
        return <p>No data found for isolate {isolateId}</p>;
    }

    return (
        <div>
            <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                    <li className="vf-breadcrumbs__item">
                        <a href="/" className="vf-breadcrumbs__link">Search</a>
                    </li>
                    <li className="vf-breadcrumbs__item" aria-current="location">
                        Genome View
                    </li>
                </ul>
            </nav>

            <div className="vf-box vf-box--primary">
                <h2>{isolateData.species}: {isolateData.isolate_name}</h2>
                <p><strong>Assembly Name:</strong> {isolateData.isolate_name}</p>
                <p><strong>ENA Accession:</strong> {isolateData.isolate_name}</p>
                <p><strong>Assembly:</strong> <a href={isolateData.fasta_url}>{isolateData.fasta_file_name}</a></p>
                <p><strong>Annotations:</strong> <a href={isolateData.gff_url}>{isolateData.gff_file_name}</a></p>
            </div>
            <h1>Genome Viewer for {isolateData.isolate_name}</h1>

            <h2>FASTA File Preview:</h2>
            <pre>{fastaContent ? fastaContent : 'Loading FASTA file...'}</pre>

            <h2>GFF File Preview:</h2>
            <pre>{gffContent ? gffContent : 'Loading GFF file...'}</pre>

            <div id="jbrowse_linear_genome_view" style={{height: '600px'}}>
                {viewerReady && viewStateRef.current && forceRender ? (
                    <JBrowseLinearGenomeView viewState={viewStateRef.current}/>
                ) : (
                    <p>Loading JBrowse viewer...</p>
                )}
            </div>
        </div>
    );
};

export default JBrowseViewer;
