import React, {useEffect, useMemo, useState} from 'react';
import {useParams} from 'react-router-dom';
import getAssembly from '@components/organisms/GeneViewer/assembly';
import getTracks from '@components/organisms/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/GeneSearch/GeneSearchForm";
import {fetchGenomeById} from "../../services/genomeService";
import {fetchGeneById, fetchGeneBySearch} from "../../services/geneService";
import {JBrowseApp} from "@jbrowse/react-app";

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
    species: number;
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
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [totalPages, setTotalPages] = useState(1);
    const [geneCurrentPage, setGeneCurrentPage] = useState(1);

    const { geneId, genomeId } = useParams<{ geneId?: string; genomeId?: string }>();
    const searchParams = new URLSearchParams(location.search);
    // const genomeId = searchParams.get('genomeId');

    useEffect(() => {
        const fetchGeneAndGenomeMeta = async () => {
            try {
                if (geneId) {
                    const geneResponse = await fetchGeneById(Number(geneId));
                    setGeneMeta(geneResponse);

                    const genomeResponse = await fetchGenomeById(geneResponse.strain_id);
                    setGenomeMeta(genomeResponse);
                } else if (genomeId) {
                    const genomeResponse = await fetchGenomeById(Number(genomeId));
                    setGenomeMeta(genomeResponse);
                }
            } catch (error) {
                console.error('Error fetching gene/genome meta information', error);
            }
        };

        fetchGeneAndGenomeMeta();
    }, [geneId, genomeId]);

    const assembly = useMemo(() => {
        if (genomeMeta) {
            return getAssembly(genomeMeta, genomeMeta.fasta_url.replace(/\/[^/]+$/, ''));
        }
        return null; // return null if genomeMeta is missing
    }, [genomeMeta]);

    const tracks = useMemo(() => {
        return genomeMeta ? getTracks(genomeMeta, genomeMeta.gff_url.replace(/\/[^/]+$/, '')) : [];
    }, [genomeMeta]);

    const sessionConfig = useMemo(() => {
         console.log('sdfghjkkjmhngbfv: ' + genomeMeta)
        if (genomeMeta && geneMeta) {
            console.log('1234567890')
            return getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
        } else if (genomeMeta) {
            console.log('12345098765432167890')
            // Default session configuration if only genomeMeta is available
            return {
                name: "Default Genome View",
                views: [
                    {
                        type: "LinearGenomeView",
                        bpPerPx: 1,
                        tracks: tracks,
                        displayedRegions: [
                            {
                                refName: genomeMeta.assembly_name,
                                start: 0,
                                end: 5000000  // Adjust as needed
                            }
                        ]
                    }
                ]
            };
        }
        return null;
    }, [genomeMeta, geneMeta, assembly, tracks]);

    // wait until `assembly` is ready
    useEffect(() => {
        const checkAssemblyReady = setInterval(() => {
            if (assembly) {
                clearInterval(checkAssemblyReady); // Clear
            }
        }, 100); // Check every 100 milliseconds

        return () => clearInterval(checkAssemblyReady);
    }, [assembly]);

    const localViewState = useGeneViewerState(assembly, tracks, sessionConfig);

    if (!localViewState) {
        return <p>Loading Genome Viewer...</p>;
    }

    const handleGeneSearch = async () => {
        if (genomeId) {
            const response = await fetchGeneBySearch(parseInt(genomeId, 10), geneSearchQuery);
            setGeneResults(response.results || []);
            setTotalPages(response.num_pages || 1);
        }
    };

    const linkData = {
        template: '/gene-viewer/gene/${id}/details?genomeId=${strain_id}',
        alias: 'Select'
    };

    return (
        <div style={{ padding: '20px' }}>
            {/* Breadcrumb Section */}
            <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                    <li className={styles.breadcrumbsItem}>
                        <a href="/" className="vf-breadcrumbs__link">Home</a>
                    </li>
                    <span className={styles.separator}> | </span>
                    <li className={styles.breadcrumbsItem}>
                        <b>Genome View</b>
                    </li>
                    <span className={styles.separator}> | </span>
                    <li className={`${styles.breadcrumbsItem} ${styles.dropdown}`}>
                        <a href="#" className="vf-breadcrumbs__link vf-dropdown__trigger">
                            Related <span className={`${styles.icon} ${styles.iconDownTriangle}`}></span>
                        </a>
                        <ul className={styles.dropdownList}>
                            <li className={styles.dropdownItem}>
                                <a href="/" className={styles.dropdownLink}>Other Strains of Bacteroides uniformis</a>
                            </li>
                        </ul>
                    </li>
                </ul>
            </nav>

            {/* Genome Metadata Section */}
            <section style={{ marginTop: '20px' }}>
                {genomeMeta ? (
                    <div className="genome-meta-info">
                        <h2>{genomeMeta.species}: {genomeMeta.isolate_name}</h2>
                        <p><strong>Assembly Name:&nbsp;</strong>
                            <a href={genomeMeta.fasta_url} target="_blank"
                               rel="noopener noreferrer">{genomeMeta.assembly_name}
                            </a>
                        </p>
                        <p><strong>Annotations:&nbsp;</strong>
                            <a href={genomeMeta.gff_url} target="_blank"
                               rel="noopener noreferrer">{genomeMeta.gff_file}
                            </a>
                        </p>
                        <p><strong>ENA Accession:&nbsp;</strong>
                            <a href={genomeMeta.gff_url} target="_blank"
                               rel="noopener noreferrer">{genomeMeta.assembly_accession}
                            </a>
                        </p>
                    </div>
                ) : (
                    <p>Loading genome meta information...</p>
                )}
            </section>

            {/* Gene Search Section */}
            <div style={{ paddingLeft: '5px', paddingTop: '20px' }}>
                <section style={{ marginTop: '20px' }}>
                    <GeneSearchForm
                        searchQuery={geneSearchQuery}
                        onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                        onSearchSubmit={handleGeneSearch}
                        selectedGenomes={genomeId ? [{ id: parseInt(genomeId, 10), name: '' }] : []}
                        results={geneResults}
                        onSortClick={(sortField) => console.log('Sort by:', sortField)}
                        currentPage={geneCurrentPage}
                        totalPages={totalPages}
                        handlePageClick={(page) => setGeneCurrentPage(page)}
                        linkData={linkData}
                        viewState={localViewState}
                    />
                </section>
            </div>

            {/* JBrowse Component Section */}
            <section style={{ marginTop: '20px' }}>
                <div className={styles.sidePanel}>
                    {localViewState ? (
                        <div className={styles.geneViewerPage} style={{ width: '100%' }}>
                            <div className={styles.jbrowseContainer}>
                                <JBrowseApp viewState={localViewState} />
                            </div>
                        </div>
                    ) : (
                        <p>Loading Genome Viewer...</p>
                    )}
                </div>
            </section>
        </div>
    );
};

export default GeneViewerPage;

