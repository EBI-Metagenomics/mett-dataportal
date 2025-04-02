import React from 'react';
import styles from './GeneViewerLegends.module.scss';
import {getColorForEssentiality} from "../../utils/appConstants";

interface GeneViewerLegendsProps {
    showEssentiality: boolean;
}

const GeneViewerLegends: React.FC<GeneViewerLegendsProps> = ({showEssentiality}) => {
    const essentialityLegend = [
        {label: 'Essential (Solid)', color: getColorForEssentiality('essential_solid')},
        {label: 'Essential (Liquid)', color: getColorForEssentiality('essential_liquid')},
        {label: 'Essential (Unspecified)', color: getColorForEssentiality('essential')},
        {label: 'Non-Essential', color: getColorForEssentiality('not_essential')},
        {label: 'Unknown', color: getColorForEssentiality('unclear')},
    ];

    const codonLegend = [
        {label: 'Start Codon', color: 'green'},
        {label: 'Stop Codon', color: 'red'},
    ];

    const renderLegendItems = (items: { label: string; color: string }[]) =>
        items.map((item, index) => (
            <div key={index} className={styles.legendItem}>
                <span className={styles.colorSwatch} style={{backgroundColor: item.color}}></span>
                {item.label}
            </div>
        ));

    return (
        <div className={styles.viewerLegend}>
            <div className={styles.legendHeader}>Legend</div>
            <div className={styles.legendColumns}>
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
            </div>
        </div>
    );
};

export default GeneViewerLegends;

