import React from 'react';
import styles from './GeneViewerLegends.module.scss';
import {getColorForEssentiality, getIconForEssentiality} from "../../utils/common/geneUtils";
import {VIEWPORT_SYNC_CONSTANTS} from "../../utils/gene-viewer";

interface GeneViewerLegendsProps {
    showEssentiality: boolean;
}

const GeneViewerLegends: React.FC<GeneViewerLegendsProps> = ({showEssentiality}) => {
    const essentialityLegend = [
        {
            label: 'Essential (Solid)',
            color: getColorForEssentiality('essential_solid'),
            icon: getIconForEssentiality('essential_solid'),
        },
        {
            label: 'Essential (Liquid)',
            color: getColorForEssentiality('essential_liquid'),
            icon: getIconForEssentiality('essential_liquid'),
        },
        {
            label: 'Essential',
            color: getColorForEssentiality('essential'),
            icon: getIconForEssentiality('essential'),
        },
        {
            label: 'Non-Essential',
            color: getColorForEssentiality('not_essential'),
            icon: getIconForEssentiality('not_essential'),
        },
        {
            label: 'Unclear',
            color: getColorForEssentiality('unclear'),
            icon: getIconForEssentiality('unclear'),
        },
    ];


    const codonLegend = [
        {label: 'Start Codon', color: 'green'},
        {label: 'Stop Codon', color: 'red'},
    ];

    const userActionsLegend = [
        {label: 'Selected gene highlight', color: VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_COLOR},
    ];

    const renderLegendItems = (
        items: { label: string; color: string; icon?: string }[]
    ) =>
        items.map((item, index) => (
            <div key={index} className={styles.legendItem}>
                <span className={styles.colorSwatch} style={{backgroundColor: item.color}}></span>
                <span className={styles.legendLabel}>
        {item.label}
                    {item.icon && <span className={styles.legendIcon}>{item.icon}</span>}
      </span>
            </div>
        ));


    return (
        <div className={styles.viewerLegend}>
            <div className={styles.legendHeader}>Legend</div>
            <div className={`${styles.legendColumns} ${showEssentiality ? styles.threeColumns : styles.twoColumns}`}>
                {showEssentiality && (
                    <div>
                        <div className={styles.legendTitle}>Essentiality</div>
                        {renderLegendItems(essentialityLegend)}
                    </div>
                )}
                <div>
                    <div className={styles.legendTitle}>Codons</div>
                    {renderLegendItems(codonLegend)}
                </div>
                <div>
                    <div className={styles.legendTitle}>User Actions</div>
                    {renderLegendItems(userActionsLegend)}
                </div>
            </div>
        </div>
    );
};

export default GeneViewerLegends;

