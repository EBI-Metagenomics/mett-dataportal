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
import {GenomeMeta} from "@components/interfaces/Genome";
import {GeneMeta} from "@components/interfaces/Gene";

const GeneViewerPage: React.FC = () => {
    const [geneMeta, setGeneMeta] = useState<GeneMeta | null>(null);
    const [genomeMeta, setGenomeMeta] = useState<GenomeMeta | null>(null);
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [totalPages, setTotalPages] = useState(1);
    const [geneCurrentPage, setGeneCurrentPage] = useState(1);

    const {geneId, genomeId} = useParams<{ geneId?: string; genomeId?: string }>();

    const [sortField, setSortField] = useState<string>('species');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

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
            console.log("base fasta indexes path: " + process.env.REACT_APP_ASSEMBLY_INDEXES_PATH)
            return getAssembly(genomeMeta, process.env.REACT_APP_ASSEMBLY_INDEXES_PATH
                ? process.env.REACT_APP_ASSEMBLY_INDEXES_PATH : '');
        }
        return null; // return null if genomeMeta is missing
    }, [genomeMeta]);

    const tracks = useMemo(() => {
        console.log("base gff indexes path: " + process.env.REACT_APP_GFF_INDEXES_PATH)
        return genomeMeta ? getTracks(genomeMeta, process.env.REACT_APP_GFF_INDEXES_PATH
            ? process.env.REACT_APP_GFF_INDEXES_PATH : '') : [];
    }, [genomeMeta]);

    const sessionConfig = useMemo(() => {
        if (genomeMeta) {
            return getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
        } else {
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
                                refName: 'Default assembly',
                                start: 0,
                                end: 5000000
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
        <div>
            <div className={`vf-content ${styles.vfContent}`}>
                <div style={{height: '20px'}}></div>
            </div>
            <div className={`vf-content ${styles.vfContent}`}>
                <span style={{display: 'none'}}><p>
                placeholder
            </p></span>
            </div>

            <section className="vf-u-fullbleed">
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
                        {genomeMeta ? (
                            <li className={`${styles.breadcrumbsItem} ${styles.dropdown}`}>
                                <a href="#" className="vf-breadcrumbs__link vf-dropdown__trigger">
                                    Related <span className={`${styles.icon} ${styles.iconDownTriangle}`}></span>
                                </a>
                                <ul className={styles.dropdownList}>
                                    <li className={styles.dropdownItem}>
                                        <a href="/" className={styles.dropdownLink}>Other Strains
                                            of <i>{genomeMeta.species}</i></a>
                                    </li>
                                </ul>
                            </li>
                        ) : (
                            <p>Loading genome meta information...</p>)}
                    </ul>
                </nav>

                {/* Genome Metadata Section */}
                <section>
                    {genomeMeta ? (
                        <div className="genome-meta-info">
                            <h2><i>{genomeMeta.species}</i>: {genomeMeta.isolate_name}</h2>
                            <p><strong>Assembly Name:&nbsp;</strong>
                                <a href={genomeMeta.fasta_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.assembly_name}
                                    <span className="icon icon-common icon-download"
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            </p>
                            <p><strong>Annotations:&nbsp;</strong>
                                <a href={genomeMeta.gff_url} target="_blank"
                                   rel="noopener noreferrer">{genomeMeta.gff_file}
                                    <span className="icon icon-common icon-download"
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            </p>
                            <p><strong>ENA Accession:&nbsp;</strong>
                                <a
                                    href={
                                        genomeMeta.assembly_accession
                                            ? `${process.env.REACT_APP_ENA_BASE_URL}${genomeMeta.assembly_accession}`
                                            : undefined
                                    }
                                    target="_blank"
                                    rel="noopener noreferrer">
                                    {genomeMeta.assembly_accession ? `XX000000${genomeMeta.assembly_accession}` : "Not Available"}
                                    <span className="icon icon-common icon-external-link-alt"
                                          style={{paddingLeft: '5px'}}></span>
                                </a>
                            </p>
                        </div>
                    ) : (
                        <p>Loading genome meta information...</p>
                    )}
                </section>


                {/* Gene Search Section */}
                <div style={{paddingLeft: '5px', paddingTop: '20px'}}>
                    <section style={{marginTop: '20px'}}>
                        <GeneSearchForm
                            searchQuery={geneSearchQuery}
                            onSearchQueryChange={e => setGeneSearchQuery(e.target.value)}
                            onSearchSubmit={handleGeneSearch}
                            selectedGenomes={genomeId ? [{id: parseInt(genomeId, 10), name: ''}] : []}
                            results={geneResults}
                            onSortClick={handleGeneSearch}
                            sortField={sortField}
                            sortOrder={sortOrder}
                            currentPage={geneCurrentPage}
                            totalPages={totalPages}
                            handlePageClick={(page) => setGeneCurrentPage(page)}
                            linkData={linkData}
                            viewState={localViewState}
                        />
                    </section>
                </div>

                {/* JBrowse Component Section */}
                <div>
                    {localViewState ? (
                        <div className={styles.jbrowseViewer}>
                            <div className={styles.jbrowseContainer} style={{width: '100%', height: '100%'}}>
                                <JBrowseApp viewState={localViewState}/>
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

