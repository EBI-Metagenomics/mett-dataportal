import React, {useMemo} from 'react';
import {Column, Row, useExpanded, useTable,} from "react-table";
import {PyhmmerDomain} from '../../../interfaces/Pyhmmer';
import Alignment from '../Alignment/Alignment';
import './AlignmentTable.scss';

interface AlignmentTableProps {
    domain: PyhmmerDomain;
}

export const AlignmentTable: React.FC<AlignmentTableProps> = ({domain}) => {

    const columns = useMemo<Column<PyhmmerDomain>[]>(() => {
        const cols = [
        {
            Header: 'Query',
            columns: [
                {
                    Header: 'start',
                    id: 'query_start',
                    accessor: (row: PyhmmerDomain) => row.alignment_display?.hmmfrom || '-',
                },
                {
                    Header: 'end',
                    id: 'query_end',
                    accessor: (row: PyhmmerDomain) => row.alignment_display?.hmmto || '-',
                },
            ],
        },
        {
            Header: 'Target Envelope',
            columns: [
                {
                    Header: 'start',
                    id: 'env_start',
                    accessor: (row: PyhmmerDomain) => row.env_from || '-',
                },
                {
                    Header: 'end',
                    id: 'env_end',
                    accessor: (row: PyhmmerDomain) => row.env_to || '-',
                },
            ],
        },
        {
            Header: 'Target Alignment',
            columns: [
                {
                    Header: 'start',
                    id: 'align_start',
                    accessor: (row: PyhmmerDomain) => row.alignment_display?.sqfrom || '-',
                },
                {
                    Header: 'end',
                    id: 'align_end',
                    accessor: (row: PyhmmerDomain) => row.alignment_display?.sqto || '-',
                },
            ],
        },
        {
            Header: 'Bias',
            id: 'bias',
            accessor: (row: PyhmmerDomain) => row.bias ? row.bias.toPrecision(2) : '-',
        },
        {
            Header: '% Identity (count)',
            id: 'identity',
            accessor: (row: PyhmmerDomain) => {
                const identity = row.alignment_display?.identity;
                if (!identity) return '-';
                return `${(100.0 * identity[0]).toFixed(1)} (${identity[1]})`;
            },
        },
        {
            Header: '% Similarity (count)',
            id: 'similarity',
            accessor: (row: PyhmmerDomain) => {
                const similarity = row.alignment_display?.similarity;
                if (!similarity) return '-';
                return `${(100.0 * similarity[0]).toFixed(1)} (${similarity[1]})`;
            },
        },
        {
            Header: 'Bit Score',
            id: 'bitscore',
            accessor: (row: PyhmmerDomain) => row.bitscore.toFixed(1),
        },
        {
            Header: 'E-value',
            columns: [
                {
                    Header: 'Independent',
                    id: 'ievalue',
                    accessor: (row: PyhmmerDomain) => {
                        if (!row.ievalue) return '-';
                        // Format E-value in scientific notation for better readability
                        return row.ievalue < 0.01 ? row.ievalue.toExponential(2) : row.ievalue.toPrecision(2);
                    },
                },
                {
                    Header: 'Conditional',
                    id: 'cevalue',
                    accessor: (row: PyhmmerDomain) => {
                        if (!row.cevalue) return '-';
                        // Format E-value in scientific notation for better readability
                        return row.cevalue < 0.01 ? row.cevalue.toExponential(2) : row.cevalue.toPrecision(2);
                    },
                },
            ],
        },
    ];
    
    console.log('Table columns:', cols);
    return cols;
    }, []);

    const data = useMemo(() => [domain], [domain]);

    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = useTable(
        {
            columns,
            data,
        },
        useExpanded
    );

    return (
        <div style={{ overflowX: 'auto', width: '100%' }}>
            <table {...getTableProps()} className="vf-table vf-table--bordered alignment-table">
            <thead className="vf-table__header">
            {headerGroups.map((headerGroup, groupIndex) => {
                const { key, ...headerProps } = headerGroup.getHeaderGroupProps();
                return (
                    <tr {...headerProps} key={key} className="vf-table__row">
                        {headerGroup.headers.map((column, columnIndex) => {
                            const columnProps = column.getHeaderProps();
                            return (
                                <th
                                    {...columnProps}
                                    key={`header-${groupIndex}-${columnIndex}`}
                                    className="vf-table__heading"
                                    colSpan={column.columns?.length || 1}
                                    data-column-id={column.id}
                                >
                                    {column.render('Header')}
                                </th>
                            );
                        })}
                    </tr>
                );
            })}
            </thead>
            <tbody {...getTableBodyProps()} className="vf-table__body">
            {rows.map((row: Row<PyhmmerDomain>, rowIndex) => {
                prepareRow(row);
                const { key, ...rowProps } = row.getRowProps();
                return (
                    <React.Fragment key={key}>
                        <tr {...rowProps} className="vf-table__row">
                            {row.cells.map((cell, cellIndex) => {
                                const cellProps = cell.getCellProps();
                                return (
                                    <td 
                                        {...cellProps} 
                                        key={`cell-${rowIndex}-${cellIndex}`} 
                                        className="vf-table__cell"
                                        data-column-id={cell.column.id}
                                    >
                                        {cell.render('Cell')}
                                    </td>
                                );
                            })}
                        </tr>
                        {domain.alignment_display && (
                            <tr key={`alignment-${rowIndex}`}>
                                <td className="vf-table__cell" colSpan={999}>
                                    <Alignment
                                        alignment={domain.alignment_display}
                                        algorithm="phmmer"
                                        included={true}
                                    />
                                </td>
                            </tr>
                        )}
                    </React.Fragment>
                );
            })}
            </tbody>
        </table>
        </div>
    );
};

export default AlignmentTable; 