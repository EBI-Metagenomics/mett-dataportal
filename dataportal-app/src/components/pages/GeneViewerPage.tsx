import React, {useEffect, useMemo, useState} from 'react';
import {ThemeProvider} from '@mui/material';
import {useParams} from 'react-router-dom';
import getAssembly from '@components/organisms/GeneViewer/assembly';
import getTracks from '@components/organisms/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/GeneViewer/defaultSessionConfig';
import useGeneViewerState from '@components/organisms/GeneViewer/geneViewerState';
import {createJBrowseTheme} from '@jbrowse/core/ui';
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

        const {geneId} = useParams<{ geneId?: string }>();
        const searchParams = new URLSearchParams(location.search);
        const genomeId = searchParams.get('genomeId');

        // Fetch gene and genome metadata
        useEffect(() => {
            const fetchGeneAndGenomeMeta = async () => {
                try {
                    if (geneId) {
                        const geneResponse = await fetchGeneById(Number(geneId));
                        console.log('Gene data fetched:', geneResponse);
                        setGeneMeta(geneResponse);

                        const genomeResponse = await fetchGenomeById(geneResponse.strain_id);
                        console.log('Genome data fetched:', genomeResponse);
                        setGenomeMeta(genomeResponse);
                    } else if (genomeId) {
                        const genomeResponse = await fetchGenomeById(Number(genomeId));
                        console.log('Genome data fetched:', genomeResponse);
                        setGenomeMeta(genomeResponse);
                    }
                } catch (error) {
                    console.error('Error fetching gene/genome meta information', error);
                }
            };

            fetchGeneAndGenomeMeta();
        }, [geneId, genomeId]);

        const assembly = useMemo(() => {
            const result = genomeMeta ? getAssembly(genomeMeta, genomeMeta.fasta_url.replace(/\/[^/]+$/, '')) : null;
            console.log('Assembly computed:', result);
            return result;
        }, [genomeMeta]);

        const tracks = useMemo(() => {
            const result = genomeMeta ? getTracks(genomeMeta, genomeMeta.gff_url.replace(/\/[^/]+$/, '')) : [];
            console.log('Tracks computed:', result);
            return result;
        }, [genomeMeta]);

        const sessionConfig = useMemo(() => {
            if (genomeMeta && geneMeta) {
                const config = getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
                console.log("sessionconfig1: " + config);
                console.log("sessionconfig2: " + config);
                return config;
            }
            return null;
        }, [genomeMeta, geneMeta, assembly, tracks]);

        const localViewState = useGeneViewerState(assembly, tracks, sessionConfig);
        console.log('Local View State:', localViewState);


        if (!localViewState) {
            return <p>Loading Genome Viewer...</p>;
        }

        // Log all widgets in the session
        console.log('Session Widgets:', localViewState?.session?.widgets);

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
            <div style={{padding: '20px'}}>

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
                                    <a href="/" className={styles.dropdownLink}>Other Strains of Bacteroides
                                        uniformis</a>
                                </li>
                            </ul>
                        </li>
                    </ul>
                </nav>

                {/* Genome Metadata Section */}
                <section style={{marginTop: '20px'}}>
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
                <div style={{padding: '20px'}}>
                    <section style={{marginTop: '20px'}}>
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedGenomes={genomeId ? [{id: parseInt(genomeId, 10), name: ''}] : []}
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
                <section style={{marginTop: '20px'}}>
                    <div className={styles.sidePanel}>
                        {localViewState ? (
                            <div className={styles.geneViewerPage} style={{width: '100%'}}>
                                <div className={styles.jbrowseContainer} style={{width: '100%'}}>
                                    <ThemeProvider theme={createJBrowseTheme()}>
                                        <JBrowseApp viewState={localViewState}/>
                                    </ThemeProvider>
                                </div>
                            </div>
                        ) : (
                            <p>Loading Genome Viewer...</p>
                        )}
                    </div>

                </section>
            </div>
        )
            ;
    }
;

export default GeneViewerPage;
