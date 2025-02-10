import React, {useState} from 'react';
import styles from './GeneResultsTable.module.scss';
import {createViewState} from '@jbrowse/react-app';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {GeneMeta} from '../../../../interfaces/Gene';
import {getIconForEssentiality, ZOOM_LEVELS} from '../../../../utils/appConstants';

type ViewModel = ReturnType<typeof createViewState>;

interface GeneResultsTableProps {
    results: GeneMeta[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    linkData: LinkData;
    viewState?: ViewModel;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const generateLink = (template: string, result: any) => {
    return template
        .replace('${strain_name}', result.strain.isolate_name)
        .replace('${gene_id}', result.id);
};

const handleNavigation = (
    viewState: ViewModel,
    contig: string,
    start: number,
    end: number,
    setLoading: React.Dispatch<React.SetStateAction<boolean>> // Pass setLoading to handle spinner
) => {
    const view = viewState?.session?.views?.[0];
    if (view && typeof view.navToLocString === 'function') {
        setLoading(true); // Show spinner before navigation
        try {
            view.navToLocString(`${contig}:${start}..${end}`);
            setTimeout(() => {
                view.zoomTo(ZOOM_LEVELS.DEFAULT);
                setLoading(false); // Hide spinner after navigation
            }, 200);
        } catch (error) {
            console.error('Error during navigation:', error);
            setLoading(false); // Ensure spinner is hidden on error
        }
    } else {
        console.error('navToLocString is not available on the view object');
    }
};

const GeneResultsTable: React.FC<GeneResultsTableProps> = ({
                                                               results,
                                                               onSortClick,
                                                               linkData,
                                                               viewState,
                                                               setLoading,
                                                           }) => {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const handleSort = (field: string) => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);
        onSortClick(field, newSortOrder);
    };

    return (
        <table className="vf-table vf-table--sortable">
            <thead className="vf-table__header">
            <tr className="vf-table__row">
                <th onClick={() => handleSort('strain')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Strain
                </th>
                <th onClick={() => handleSort('gene_name')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Gene
                </th>
                <th onClick={() => handleSort('seq_id')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Seq Id
                </th>
                <th onClick={() => handleSort('locus_tag')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Locus Tag
                </th>
                <th onClick={() => handleSort('product')}
                    className={`vf-table__heading ${styles.vfTableHeading} ${styles.clickableHeader}`}>
                    Product
                </th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`}>Essentiality</th>
                <th className={`vf-table__heading ${styles.vfTableHeading}`} scope="col">Actions</th>
            </tr>
            </thead>
            <tbody className="vf-table__body">
            {results.map((geneMeta, index) => (
                <tr key={index} className="vf-table__row">
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.strain.isolate_name || 'Unknown Strain'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.gene_name || 'Unknown Gene Name'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.seq_id || 'Unknown'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.locus_tag || 'Unknown Locus Tag'}</td>
                    <td className={`vf-table__cell ${styles.vfTableCell}`}>{geneMeta.product || ''}</td>

                    <td className={`vf-table__cell ${styles.vfTableCellIcon}`}>
                        {geneMeta.essentiality_data && geneMeta.essentiality_data.length > 0 ? (
                            // Filter for only 'solid' media type
                            geneMeta.essentiality_data
                                .filter((essentiality) => essentiality.media === 'solid')
                                .map((essentiality, index) => (
                                    <span
                                        key={`${geneMeta.id}-${index}`}
                                        title={`${essentiality.essentiality}`}
                                        className={styles.essentialityIcon}
                                    >
                                        {getIconForEssentiality(essentiality.essentiality)}
                                    </span>
                                ))
                        ) : (
                            '---'
                        )}
                    </td>

                    <td className={`vf-table__cell ${styles.vfTableCell}`}>
                        {viewState ? (
                            <a
                                href="#"
                                className="vf-link"
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleNavigation(
                                        viewState,
                                        geneMeta.seq_id,
                                        geneMeta.start_position ? geneMeta.start_position : 0,
                                        geneMeta.end_position ? geneMeta.end_position : 1000,
                                        setLoading
                                    );
                                }}
                            >
                                {linkData.alias}
                            </a>
                        ) : (
                            <a href={generateLink(linkData.template, geneMeta)} target="_blank" rel="noreferrer">
                                {linkData.alias}
                                <span className={`icon icon-common icon-external-link-alt ${styles.externalIcon}`}
                                      style={{paddingLeft: '5px'}}></span>
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
