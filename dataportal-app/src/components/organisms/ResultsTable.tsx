import React from 'react';
import ResultRow from '../molecules/ResultRow';

interface ResultsTableProps {
  results: any[];
  onGenomeSelect: (id: string) => void;
  selectedGenome: string;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, onGenomeSelect, selectedGenome }) => {
  return (
    <table className="vf-table vf-table--sortable">
      <thead>
        <tr>
          <th>Species</th>
          <th>Strain</th>
          <th>Assembly</th>
          <th>Annotations</th>
          <th>Search Gene</th>
        </tr>
      </thead>
      <tbody>
        {results.map((result) => (
          <ResultRow
            key={result.id}
            result={result}
            onGenomeSelect={() => onGenomeSelect(result.id)}
            isSelected={selectedGenome === result.id}
          />
        ))}
      </tbody>
    </table>
  );
};

export default ResultsTable;
