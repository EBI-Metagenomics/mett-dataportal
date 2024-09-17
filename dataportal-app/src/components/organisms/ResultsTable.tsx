// Assuming ResultsTableProps is an interface
interface ResultsTableProps {
  results: any[]; // Adjust the type based on your actual results
  pagination?: {
    page: number;
    totalPages: number;
  };
  onPageChange?: (newPage: number) => void;
  onIsolateSelect: (isolate: string) => void; // Add this as well
}

// Example of how to handle pagination and results in ResultsTable
const ResultsTable: React.FC<ResultsTableProps> = ({ results, pagination, onPageChange, onIsolateSelect }) => {
  return (
    <div>
      {/* Render the results */}
      <table>
        <thead>
          <tr>
            {/* Table header */}
          </tr>
        </thead>
        <tbody>
          {results.map(result => (
            <tr key={result.id} onClick={() => onIsolateSelect(result.id)}>
              {/* Render table rows based on result */}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination controls, if pagination exists */}
      {pagination && (
        <div>
          <button
            disabled={pagination.page === 1}
            onClick={() => onPageChange && onPageChange(pagination.page - 1)}
          >
            Previous
          </button>
          <span>Page {pagination.page} of {pagination.totalPages}</span>
          <button
            disabled={pagination.page === pagination.totalPages}
            onClick={() => onPageChange && onPageChange(pagination.page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default ResultsTable;
