import React, {useState} from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-app';
import {LinkData} from "../../../../interfaces/Auxiliary";
import {GeneMeta} from "../../../../interfaces/Gene";
import {ZOOM_LEVELS} from "../../../../utils/appConstants";

type ViewModel = ReturnType<typeof createViewState>;

interface GeneResultsTableProps {
    results: GeneMeta[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    linkData: LinkData;
    viewState?: ViewModel;
}

const generateLink = (template: string, result: any) => {
    return template
        .replace('${strain_name}', result.strain)
        .replace('${gene_id}', result.id);
};

const handleNavigation = (
    viewState: ViewModel,
    contig: string,
    start: number,
    end: number,
) => {
    const view = viewState?.session?.views?.[0];
    console.log("View Object:", view);
    if (view && typeof view.navToLocString === 'function') {
        view.navToLocString(`${contig}:${start}..${end}`);
        setTimeout(() => {
            view.zoomTo(ZOOM_LEVELS.DEFAULT);
            // console.log('Zoom applied');
        }, 200);
    } else {
        console.error("navToLocString is not available on the view object");
    }
};
const GeneResultsTable: React.FC<GeneResultsTableProps> = ({
                                                               results,
                                                               onSortClick,
                                                               linkData,
                                                               viewState,
                                                           }) => {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const handleSort = (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        console.log('###### ' + field + ' ###### ' + newSortOrder);
        onSortClick(field, newSortOrder);
    };

    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th onClick={() => handleSort('strain')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Strain
                    {sortField === 'strain' ? (
                        <span className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                              style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th onClick={() => handleSort('gene_name')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Gene
                    {sortField === 'gene_name' ? (
                        <span className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                              style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th onClick={() => handleSort('seq_id')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Seq Id
                    {sortField === 'seq_id' ? (
                        <span className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                              style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th onClick={() => handleSort('locus_tag')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Locus Tag
                    {sortField === 'locus_tag' ? (
                        <span className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                              style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th onClick={() => handleSort('product')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Product
                    {sortField === 'product' ? (
                        <span className={`icon icon-common ${sortOrder === 'asc' ? 'icon-sort-up' : 'icon-sort-down'}`}
                              style={{paddingLeft: '5px'}}></span>
                    ) : (
                        <span className="icon icon-common icon-sort" style={{paddingLeft: '5px'}}></span>
                    )}
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((geneMeta, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.strain || 'Unknown Strain'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.gene_name || 'Unknown Gene Name'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.seq_id || 'Unknown'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.locus_tag || 'Unknown Locus Tag'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.description || ''}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        {viewState ? (
                            <a
                                href="#"
                                className="vf-link"
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleNavigation(viewState, geneMeta.seq_id,
                                        geneMeta.start_position ? geneMeta.start_position : 0,
                                        geneMeta.end_position ? geneMeta.end_position : 1000);
                                }}
                            >
                                {linkData.alias}
                            </a>
                        ) : (
                            <a href={generateLink(linkData.template, geneMeta)}>
                                {linkData.alias}
                            </a>
                        )}
                    </td>

                </tr>
            ))}
            </tbody>
        </table>
    );
};

export default GeneResultsTable;
