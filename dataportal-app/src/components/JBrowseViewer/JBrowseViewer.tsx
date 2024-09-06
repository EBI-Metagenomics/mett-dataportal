import React, {useEffect, useRef, useState} from 'react';
import {useParams} from 'react-router-dom';
import {createViewState, JBrowseLinearGenomeView, loadPlugins,} from '@jbrowse/react-linear-genome-view';
import {getData} from "../../utils/api";
import getAssembly from './assembly';
import getTracks from './tracks';

interface JBrowseViewerProps {}

export interface IsolateData {
  species: string;
  isolate_name: string;
  fasta_url: string;
  gff_url: string;
  fasta_file_name: string;
  gff_file_name: string;
}

const JBrowseViewer: React.FC<JBrowseViewerProps> = () => {
  const { isolateId } = useParams<{ isolateId: string }>(); // Get isolateId from URL
  const [isolateData, setIsolateData] = useState<IsolateData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const viewStateRef = useRef<any>(null);

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

  useEffect(() => {
    const initializeJBrowse = async () => {
      if (!isolateData) return; // Do not initialize until data is fetched

      try {
        console.log('Loading plugins...');
        const loadedPlugins = await loadPlugins([
          {
            name: 'GWAS',
            url: 'https://unpkg.com/jbrowse-plugin-gwas/dist/jbrowse-plugin-gwas.umd.production.min.js',
          },
        ]);

        console.log('Plugins loaded:', loadedPlugins);

        // Initialize view state
        viewStateRef.current = createViewState({
          assembly: getAssembly(isolateData), // Pass isolateData to assembly function
          tracks: getTracks(isolateData),     // Pass isolateData to tracks function
          location: '1:1000..20000',
          plugins: loadedPlugins.map((p) => p.plugin),
          defaultSession: {
            name: 'My session',
            view: {
              id: 'linearGenomeView',
              type: 'LinearGenomeView',
              tracks: [
                {
                  type: 'FeatureTrack',
                  configuration: 'annotations',
                },
              ],
            },
          },
        });

        console.log('View state created:', viewStateRef.current);
      } catch (error) {
        console.error('Error loading plugins or initializing JBrowse:', error);
      }
    };

    initializeJBrowse();
  }, [isolateData]);

  if (loading) {
    return <p>Loading...</p>;
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
      <div id="jbrowse_linear_genome_view" style={{ height: '600px' }}>
        {viewStateRef.current && (
          <JBrowseLinearGenomeView viewState={viewStateRef.current} />
        )}
      </div>
    </div>
  );
};

export default JBrowseViewer;
