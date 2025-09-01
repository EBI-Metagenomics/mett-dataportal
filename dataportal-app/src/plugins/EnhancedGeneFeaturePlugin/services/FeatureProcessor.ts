import SimpleFeature from '@jbrowse/core/util/simpleFeature';
import {GeneService} from "../../../services/gene";
import {getIconForEssentiality} from "../../../utils/common/constants";


export class FeatureProcessor {
    /**
     * Fetch protein sequence for a feature
     */
    static async fetchProteinSequence(feature: SimpleFeature): Promise<SimpleFeature> {
        const attributes = feature.get('attributes') || {};
        const locusTag = attributes.locus_tag;

        console.log('🔧 fetchProteinSequence called for feature:', {
            hasAttributes: !!attributes,
            locusTag,
            featureKeys: Object.keys(feature.toJSON())
        });

        if (!locusTag) {
            console.log('🔧 No locus tag found, returning feature as-is');
            return feature;
        }

        try {
            console.log('🔧 Fetching protein sequence for locus tag:', locusTag);
            const proteinData = await GeneService.fetchGeneProteinSeq(locusTag);
            console.log('🔧 Protein data received:', {
                hasSequence: !!proteinData.protein_sequence,
                sequenceLength: proteinData.protein_sequence?.length || 0
            });

            // Create a new feature with protein sequence as a direct property
            const updatedFeature = new SimpleFeature({
                ...feature.toJSON(),
                protein_sequence: proteinData.protein_sequence  // Set as direct property
            });
            
            console.log('🔧 Protein sequence set on feature');
            console.log('🔧 Feature after setting protein sequence:', {
                hasProteinSequence: !!updatedFeature.get('protein_sequence'),
                proteinSequenceLength: updatedFeature.get('protein_sequence')?.length || 0,
                allKeys: Object.keys(updatedFeature.toJSON())
            });
            
            return updatedFeature;
        } catch (error) {
            console.warn(`Failed to fetch protein sequence for ${locusTag}:`, error);
        }
        return feature;
    }

    /**
     * Flatten attributes from SimpleFeature to make them directly accessible
     */
    static flattenAttributes(features: SimpleFeature[]): SimpleFeature[] {
        console.log('🔧 flattenAttributes called with', features.length, 'features');
        
        return features.map((feature, index) => {
            console.log(`🔧 Before toJSON for feature ${index}:`, {
                hasProteinSequence: !!feature.get('protein_sequence'),
                proteinSequenceLength: feature.get('protein_sequence')?.length || 0
            });
            
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};
            
            console.log(`🔧 Processing feature ${index}:`, {
                hasAttributes: !!attributes,
                attributeKeys: Object.keys(attributes),
                locusTag: attributes.locus_tag,
                hasProteinSequenceInData: !!featureData.protein_sequence,
                proteinSequenceInDataLength: (featureData.protein_sequence as string)?.length || 0
            });
            
            const {attributes: _, ...featureWithoutAttributes} = featureData;
            
            // Add PyHMMER search information
            const pyhmmerInfo = this.createPyhmmerSearchInfo(feature);
            console.log(`🔧 PyHMMER info for feature ${index}:`, pyhmmerInfo ? 'created' : 'null');
            
            const newFeature = new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes, // Keep all original attributes
                pyhmmerSearch: pyhmmerInfo, // Add PyHMMER search info
            });
            
            return newFeature;
        });
    }

    /**
     * Create PyHMMER search information for a feature
     */
    static createPyhmmerSearchInfo(feature: SimpleFeature): any {
        const proteinSequence = feature.get('protein_sequence');
        
        console.log('🔧 createPyhmmerSearchInfo called for feature:', {
            hasProteinSequence: !!proteinSequence,
            proteinSequenceLength: proteinSequence?.length || 0,
            featureKeys: Object.keys(feature.toJSON())
        });
        
        if (!proteinSequence) {
            console.log('🔧 No protein sequence found, returning null');
            return null;
        }

        console.log('🔧 Creating PyHMMER info for protein sequence length:', proteinSequence.length);
        
        // Return the search link that will appear in JBrowse feature panel
        return {
            proteinSequence: proteinSequence, // Keep the actual sequence for search
            proteinLength: proteinSequence.length,
            // Add a clickable search link that will appear in JBrowse feature panel
            pyhmmerSearchLink: `<a href="#" data-pyhmmer-search="${proteinSequence}" class="pyhmmer-search-link">Search Protein Domains (${proteinSequence.length})</a>`,
        };
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

            // Add PyHMMER search information
            const pyhmmerInfo = this.createPyhmmerSearchInfo(feature);

            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes, // Keep all original attributes
                Essentiality,
                EssentialityVisual,
                externalLinks, // Preserve the processed external links
                pyhmmerSearch: pyhmmerInfo, // Add PyHMMER search info
            });
        });
    }
}
