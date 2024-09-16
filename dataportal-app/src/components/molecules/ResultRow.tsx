import React from 'react';
import TableCell from '../atoms/TableCell';

interface ResultRowProps {
  result: any;
  onGenomeSelect: () => void;
  isSelected: boolean;
}

const ResultRow: React.FC<ResultRowProps> = ({ result, onGenomeSelect, isSelected }) => {
  return (
    <tr className="vf-table__row">
      <TableCell>{result.species || 'Unknown Species'}</TableCell>
      <TableCell>{result.isolate_name || 'Unknown Isolate'}</TableCell>
      <TableCell>
        <a href={result.fasta_file || '#'}>{result.assembly_name || 'Unknown Assembly'}</a>
      </TableCell>
      <TableCell><a href={result.gff_file || '#'}>GFF</a></TableCell>
      <TableCell>
        <input type="checkbox" onChange={onGenomeSelect} checked={isSelected} />
      </TableCell>
    </tr>
  );
};

export default ResultRow;
