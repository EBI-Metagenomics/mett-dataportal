import SimpleFeature from '@jbrowse/core/util/simpleFeature';
import {GeneService} from "../../../services/geneService";
import {getIconForEssentiality} from "../../../utils/appConstants";

export class FeatureProcessor {
    /**
     * Fetch protein sequence for a feature
     */
    static async fetchProteinSequence(feature: SimpleFeature): Promise<SimpleFeature> {
        const attributes = feature.get('attributes') || {};
        const locusTag = attributes.locus_tag;

        if (!locusTag) {
            return feature;
        }

        try {
            const proteinData = await GeneService.fetchGeneProteinSeq(locusTag);

            feature.set('attributes', {
                ...attributes,
                protein_sequence: proteinData.protein_sequence
            });
        } catch (error) {
            console.warn(`Failed to fetch protein sequence for ${locusTag}:`, error);
        }
        return feature;
    }

    /**
     * Flatten attributes from SimpleFeature to make them directly accessible
     */
    static flattenAttributes(features: SimpleFeature[]): SimpleFeature[] {
        return features.map(feature => {
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};
            
            const {attributes: _, ...featureWithoutAttributes} = featureData;
            const newFeature = new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
                // Don't add attributes object to avoid duplication
            });
            
            return newFeature;
        });
    }

    /**
     * Merge annotations with essentiality data
     */
    static mergeAnnotationsWithEssentiality(
        gffFeatures: SimpleFeature[],
        essentialityData: Record<string, any>,
    ): SimpleFeature[] {
        return gffFeatures.map((feature) => {
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};

            const {attributes: _, ...featureWithoutAttributes} = featureData;
            const locusTag = featureData.locus_tag;
            const Essentiality =
                locusTag && typeof locusTag === 'string' && essentialityData[locusTag]
                    ? essentialityData[locusTag].essentiality?.toLowerCase() || 'unknown'
                    : 'unknown';
            const EssentialityVisual = getIconForEssentiality(Essentiality);

            // Preserve external links from the original feature
            const externalLinks = feature.get('externalLinks');

            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
                Essentiality,
                EssentialityVisual,
                externalLinks, // Preserve the processed external links
            });
        });
    }
}
