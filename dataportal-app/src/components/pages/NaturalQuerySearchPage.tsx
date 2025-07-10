import React, {useState} from "react";
import styles from "@components/pages/GeneViewerPage.module.scss";
import {NaturalQueryService} from "../../services/naturalQueryService";
import {GeneService} from "../../services/geneService";
import {GeneMeta} from "../../interfaces/Gene";
import {DEFAULT_PER_PAGE_CNT} from "../../utils/appConstants";
import Pagination from "@components/molecules/Pagination";

interface GeneResult {
    id: string;
    locus_tag: string;
    product: string;
    essentiality?: string;
    amr?: boolean;
    strain?: string;
}

const NaturalQuerySearchPage = () => {
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<GeneMeta[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PER_PAGE_CNT);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        setLoading(true);
        setError(null);
        setResults([]);

        try {
            const filters = await NaturalQueryService.query({query: input});

            if (filters.error) {
                setError("Could not understand query.");
                return;
            }

            const species = [filters.species]
            // Map keys for correct Elasticsearch field names
            const selectedFacetFilters: Record<string, string[]> = {};

            if (filters.essentiality) {
                selectedFacetFilters["essentiality"] = [filters.essentiality];
            }
            if (filters.amr !== undefined) {
                selectedFacetFilters["has_amr_info"] = [String(filters.amr)];
            }

            type FacetKey = keyof typeof selectedFacetFilters;

            const facetOperators: Record<FacetKey, "AND" | "OR"> = Object.keys(selectedFacetFilters).reduce(
                (acc, key) => {
                    const typedKey = key as FacetKey;
                    if (selectedFacetFilters[typedKey] !== undefined && selectedFacetFilters[typedKey] !== null) {
                        acc[typedKey] = "AND";
                    }
                    return acc;
                },
                {} as Record<FacetKey, "AND" | "OR">
            );

            console.log("Search input:", {
                species,
                selectedFacetFilters,
                facetOperators,
            });


            const geneRes = await GeneService.fetchGeneSearchResultsAdvanced(
                "",
                1,
                10,
                "locus_tag",
                "asc",
                [],
                species,
                selectedFacetFilters,
                facetOperators
            );

            setResults(geneRes.data || []);
            setCurrentPage((geneRes.pagination.page_number))
            setTotalPages((geneRes.pagination.num_pages))
            setHasNext((geneRes.pagination.has_next))
            setHasPrevious((geneRes.pagination.has_previous))
        } catch (err) {
            console.error(err);
            setError("Something went wrong.");
        } finally {
            setLoading(false);
        }
    };

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
    };


    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <div className={`vf-content ${styles.vfContent}`}>
                <div style={{height: '20px'}}></div>
            </div>
            <div className={`vf-content ${styles.vfContent}`}>
                <span style={{display: 'none'}}><p>
                placeholder
            </p></span>
            </div>

            <section>
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
                        <li className={styles.breadcrumbsItem}>
                            <b>Natural Search Query</b>
                        </li>
                    </ul>
                </nav>
                <h1 className="text-2xl font-bold">Natural Language Gene Search</h1>

                <div className="space-y-4">
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', fontWeight: 500, marginBottom: '8px' }}>Ask a question</label>
                        <div style={{ border: '1px solid #bdbdbd', borderRadius: '4px', background: '#fafafa', padding: '8px', marginBottom: '8px' }}>
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="e.g. Show essential genes in PV not involved in AMR"
                                rows={6}
                                style={{
                                    width: '100%',
                                    minHeight: '70px',
                                    maxHeight: '140px',
                                    border: 'none',
                                    background: 'transparent',
                                    fontFamily: 'monospace',
                                    fontSize: '1rem',
                                    resize: 'vertical',
                                    outline: 'none',
                                    borderRadius: '4px',
                                    boxSizing: 'border-box',
                                    margin: 0,
                                    padding: 0
                                }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                            <button
                                onClick={handleSearch}
                                disabled={loading}
                                style={{
                                    minWidth: '70px',
                                    padding: '5px 14px',
                                    borderRadius: '4px',
                                    border: 'none',
                                    fontWeight: 500,
                                    fontSize: '0.98em',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s',
                                    background: '#1976d2',
                                    color: '#fff'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.background = '#125ea2'}
                                onMouseOut={(e) => e.currentTarget.style.background = '#1976d2'}
                            >
                                {loading ? "Searching..." : "Search"}
                            </button>
                        </div>
                    </div>
                </div>

                {error && <div className="text-red-600">{error}</div>}

                {results.length > 0 && (
                    <div>
                        <h2 className="text-lg font-semibold mb-2">Results</h2>
                        <table className="vf-table">
                            <thead className="vf-table__header">
                            <tr className="vf-table__row">
                                <th className="vf-table__heading">Locus Tag</th>
                                <th className="vf-table__heading">Product</th>
                                <th className="vf-table__heading">Strain</th>
                                <th className="vf-table__heading">Essentiality</th>
                                <th className="vf-table__heading">AMR</th>
                            </tr>
                            </thead>
                            <tbody className="vf-table__body">
                            {results.map((gene) => (
                                <tr key={gene.locus_tag} className="vf-table__row">
                                    <td className="vf-table__cell">{gene.locus_tag}</td>
                                    <td className="vf-table__cell">{gene.product}</td>
                                    <td className="vf-table__cell">{gene.species_scientific_name}</td>
                                    <td className="vf-table__cell">{gene.essentiality || "-"}</td>
                                    <td className="vf-table__cell">{gene.has_amr_info ? "Yes" : "No"}</td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}
                <div className={styles.paginationBar}>
                    {totalPages > 1 && (
                        <Pagination
                            currentPage={currentPage}
                            totalPages={totalPages}
                            hasPrevious={hasPrevious}
                            hasNext={hasNext}
                            onPageClick={handlePageClick}
                        />
                    )}
                </div>
            </section>
        </div>
    );
};

export default NaturalQuerySearchPage;
