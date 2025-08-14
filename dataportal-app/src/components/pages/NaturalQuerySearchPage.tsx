import React, { useState, useCallback } from 'react';
import { ApiClient } from '../../services/common/apiInstance';
import GeneResultsTable from '@components/features/gene-viewer/GeneResultsHandler/GeneResultsTable';
import Pagination from '@components/molecules/Pagination';
import { GeneMeta } from '../../interfaces/Gene';
import { LinkData } from '../../interfaces/Auxiliary';

interface QueryResult {
  query_interpretation: {
    original_query: string;
    interpreted_parameters: any;
    api_method_used: string;
    api_parameters: any;
  };
  results: any;
  summary: {
    total_results: number;
    result_type: string;
    success: boolean;
  };
}

interface ApiResponse {
  status: string;
  message: string;
  data: QueryResult;
}

const NaturalQuerySearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interpretationOnly, setInterpretationOnly] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [hasNext, setHasNext] = useState(false);
  const [sortField, setSortField] = useState<string>('locus_tag');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const api = ApiClient.getInstance();
      const endpoint = interpretationOnly ? '/query/interpret' : '/query/query';
      
      // Send query as URL parameter, not in request body
      const encodedQuery = encodeURIComponent(query.trim());
      const urlWithQuery = `${endpoint}?query=${encodedQuery}`;
      
      const response = await api.post(urlWithQuery);
      const data: ApiResponse = response.data;
      
      if (data.status === 'success') {
        setResults(data.data);
        
        // Extract pagination info if available
        if (data.data?.results) {
          const paginationInfo = getPaginationInfo();
          setTotalPages(paginationInfo.totalPages);
          setHasPrevious(paginationInfo.hasPrevious);
          setHasNext(paginationInfo.hasNext);
          setCurrentPage(paginationInfo.currentPage);
        }
      } else {
        setError(data.message || 'Query failed');
      }
    } catch (err: any) {
      console.error('Query error:', err);
      setError(err.response?.data?.message || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Handle sorting
  const handleSortClick = useCallback((field: string, order: 'asc' | 'desc') => {
    setSortField(field);
    setSortOrder(order);
    // Note: For now, we'll just update the sort state
    // In a full implementation, you might want to re-execute the query with new sort parameters
  }, []);

  // Extract gene results and pagination info
  const getGeneResults = (): GeneMeta[] => {
    console.log('getGeneResults - results:', results);
    console.log('getGeneResults - results?.results:', results?.results);
    console.log('getGeneResults - results?.results?.results:', results?.results?.results);
    
    // The correct path based on actual response structure
    if (!results?.results?.results) {
      console.log('No gene results found in expected path');
      return [];
    }
    return results.results.results;
  };

  const getPaginationInfo = () => {
    console.log('getPaginationInfo - results?.results:', results?.results);
    
    if (!results?.results) {
      return {
        totalPages: 1,
        hasPrevious: false,
        hasNext: false,
        currentPage: 1
      };
    }
    
    const data = results.results;
    console.log('getPaginationInfo - data:', data);
    
    return {
      totalPages: data.num_pages || 1,
      hasPrevious: data.has_previous || false,
      hasNext: data.has_next || false,
      currentPage: data.page_number || 1
    };
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <div className="query-results">
        <h3>Query Results</h3>
        
        {/* Query Interpretation */}
        <div className="interpretation-section">
          <h4>Query Interpretation</h4>
          <div className="interpretation-details">
            <p><strong>Original Query:</strong> {results.query_interpretation.original_query}</p>
            <p><strong>API Method:</strong> {results.query_interpretation.api_method_used}</p>
            <p><strong>Total Results:</strong> {results.summary.total_results}</p>
          </div>
          
          <details>
            <summary>Interpreted Parameters</summary>
            <pre>{JSON.stringify(results.query_interpretation.interpreted_parameters, null, 2)}</pre>
          </details>
          
          <details>
            <summary>API Parameters</summary>
            <pre>{JSON.stringify(results.query_interpretation.api_parameters, null, 2)}</pre>
          </details>
        </div>

        {/* Gene Results */}
        {(() => {
          const geneResults = getGeneResults();
          console.log('renderResults - geneResults:', geneResults);
          console.log('renderResults - geneResults.length:', geneResults.length);
          
          if (geneResults.length > 0) {
            return (
              <div className="gene-results">
                <h4>Gene Results ({geneResults.length} genes found)</h4>
                
                {/* Gene Results Table */}
                <div className="results-table-container">
                  <GeneResultsTable
                    results={geneResults}
                    onSortClick={handleSortClick}
                    linkData={{
                      template: '/genome/${isolate_name}?locus_tag=${locus_tag}',
                      alias: 'Browse'
                    }}
                    setLoading={setLoading}
                    isTypeStrainAvailable={true}
                  />
                  
                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="pagination-container">
                      <Pagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        hasPrevious={hasPrevious}
                        hasNext={hasNext}
                        onPageClick={(page) => {
                          setCurrentPage(page);
                          // TODO: Re-execute the query with new page and sort parameters
                          // This would require updating the backend to support pagination in NL queries
                          console.log(`Navigate to page ${page}`);
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          }
          return null;
        })()}
      </div>
    );
  };

  return (
    <div className="natural-query-page">
      <div className="container">
        <h1>Natural Language Gene Query</h1>
        <p className="description">
          Ask questions about genes in natural language. The system will automatically interpret your query 
          and execute the appropriate database search.
        </p>

        {/* Example Queries */}
        <div className="example-queries">
          <h3>Example Queries</h3>
          <div className="query-examples">
            <button 
              onClick={() => setQuery("Show essential genes in Bacteroides uniformis")}
              className="example-query-btn"
            >
              "Show essential genes in Bacteroides uniformis"
            </button>
            <button 
              onClick={() => setQuery("Find genes involved in AMR in PV")}
              className="example-query-btn"
            >
              "Find genes involved in AMR in PV"
            </button>
            <button 
              onClick={() => setQuery("Get all transport proteins in BU")}
              className="example-query-btn"
            >
              "Get all transport proteins in BU"
            </button>
            <button 
              onClick={() => setQuery("Show non-essential genes with COG category J")}
              className="example-query-btn"
            >
              "Show non-essential genes with COG category J"
            </button>
          </div>
        </div>

        {/* Query Form */}
        <form onSubmit={handleSubmit} className="query-form">
          <div className="form-group">
            <label htmlFor="query">Your Query:</label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your natural language query here..."
              rows={3}
              className="query-input"
              disabled={loading}
            />
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={interpretationOnly}
                onChange={(e) => setInterpretationOnly(e.target.checked)}
                disabled={loading}
              />
              Interpretation only (don't execute query)
            </label>
          </div>

          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading || !query.trim()}
          >
            {loading ? 'Processing...' : 'Execute Query'}
          </button>
        </form>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            <h4>Error</h4>
            <p>{error}</p>
          </div>
        )}

        {/* Results Display */}
        {renderResults()}
      </div>

      <style>{`
        .natural-query-page {
          padding: 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .description {
          font-size: 1.1rem;
          color: #666;
          margin-bottom: 2rem;
        }

        .example-queries {
          margin-bottom: 2rem;
          padding: 1rem;
          background-color: #f8f9fa;
          border-radius: 8px;
        }

        .query-examples {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .example-query-btn {
          padding: 0.5rem 1rem;
          background-color: #e9ecef;
          border: 1px solid #dee2e6;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: background-color 0.2s;
        }

        .example-query-btn:hover {
          background-color: #dee2e6;
        }

        .query-form {
          margin-bottom: 2rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: bold;
        }

        .query-input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
          resize: vertical;
        }

        .form-options {
          margin-bottom: 1rem;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .submit-btn {
          padding: 0.75rem 1.5rem;
          background-color: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .submit-btn:hover:not(:disabled) {
          background-color: #0056b3;
        }

        .submit-btn:disabled {
          background-color: #6c757d;
          cursor: not-allowed;
        }

        .error-message {
          padding: 1rem;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 4px;
          color: #721c24;
          margin-bottom: 1rem;
        }

        .query-results {
          margin-top: 2rem;
        }

        .interpretation-section {
          margin-bottom: 2rem;
          padding: 1rem;
          background-color: #f8f9fa;
          border-radius: 8px;
        }

        .interpretation-details p {
          margin: 0.5rem 0;
        }

        details {
          margin: 1rem 0;
        }

        summary {
          cursor: pointer;
          font-weight: bold;
          padding: 0.5rem;
          background-color: #e9ecef;
          border-radius: 4px;
        }

        pre {
          background-color: #f8f9fa;
          padding: 1rem;
          border-radius: 4px;
          overflow-x: auto;
          font-size: 0.9rem;
        }

        .gene-results {
          margin-top: 2rem;
        }

        .results-table-container {
          margin-top: 1rem;
        }

        .pagination-container {
          margin-top: 1rem;
          display: flex;
          justify-content: center;
        }
      `}</style>
    </div>
  );
};

export default NaturalQuerySearchPage;
