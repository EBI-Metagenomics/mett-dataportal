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
    const {isolateId} = useParams<{ isolateId: string }>(); // Get isolateId from URL
    const [isolateData, setIsolateData] = useState<IsolateData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const viewStateRef = useRef<any>(null);
    const [jbrowseReady, setJbrowseReady] = useState(false);

    useEffect(() => {
        const fetchIsolateData = async () => {
            try {
                const response = await getData(`search/jbrowse/${isolateId}`, {cache: 'no-store'});
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

    useEffect(() => {
        const initializeJBrowse = async () => {
            if (!isolateData) {
                console.log('Isolate data not yet available, skipping JBrowse initialization');
                return;
            }

            console.log('Assembly:', getAssembly(isolateData));
            console.log('Tracks:', getTracks(isolateData));

            // Initialize view state without plugins
            viewStateRef.current = createViewState({
                assembly: getAssembly(isolateData),
                tracks: getTracks(isolateData),
                location: 'all',
                defaultSession: {
                    name: 'Default session',
                    view: {
                        id: 'linearGenomeView',
                        type: 'LinearGenomeView',
                        tracks: [
                            {
                                type: 'FeatureTrack',
                                configuration: 'annotations',
                                visible: true,
                            },
                        ],
                    },
                },
            });

            setJbrowseReady(true); // Indicate that JBrowse is ready to render
        };

        initializeJBrowse();
    }, [isolateData]);

// Render the JBrowse component only when viewStateRef.current is set
    if (loading) {
        console.log('Loading data...');
        return <p>Loading...</p>;
    }

    if (error) {
        console.log('Error occurred:', error);
        return <p>Error: {error}</p>;
    }

    if (!isolateData) {
        console.log('No isolate data found for isolateId:', isolateId);
        return <p>No data found for isolate {isolateId}</p>;
    }

    console.log('Rendering JBrowse component for isolate:', isolateData.isolate_name);

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
            <div id="jbrowse_linear_genome_view" style={{height: '600px'}}>
                {jbrowseReady ? (
                    <JBrowseLinearGenomeView viewState={viewStateRef.current}/>
                ) : (
                    <p>Initializing JBrowse viewer...</p>
                )}
            </div>
        </div>
    );
};

export default JBrowseViewer;
