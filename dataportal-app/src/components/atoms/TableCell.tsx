import React from 'react';

interface TableCellProps {
  children: React.ReactNode;
}

const TableCell: React.FC<TableCellProps> = ({ children }) => {
  return <td className="vf-table__cell">{children}</td>;
};

export default TableCell;
