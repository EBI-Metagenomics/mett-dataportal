import SimpleFeature from '@jbrowse/core/util/simpleFeature';
import {getIconForEssentiality} from "../../../utils/common/geneUtils";


export class FeatureProcessor {
    /**
     * Flatten attributes from SimpleFeature to make them directly accessible for JBrowse display
     */
    static flattenAttributes(features: SimpleFeature[]): SimpleFeature[] {
        return features.map((feature) => {
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};
            
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const {attributes: _attrs, ...featureWithoutAttributes} = featureData;
            
            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes, // Flatten all attributes to top level
            });
        });
    }

    /**
     * Merge essentiality data for feature coloring in JBrowse tracks
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

            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const {attributes: _attrs, ...featureWithoutAttributes} = featureData;
            const locusTag = featureData.locus_tag;
            const Essentiality =
                locusTag && typeof locusTag === 'string' && essentialityData[locusTag]
                    ? essentialityData[locusTag].essentiality?.toLowerCase() || 'unknown'
                    : 'unknown';
            const EssentialityVisual = getIconForEssentiality(Essentiality);

            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
                Essentiality,
                EssentialityVisual,
            });
        });
    }
}
