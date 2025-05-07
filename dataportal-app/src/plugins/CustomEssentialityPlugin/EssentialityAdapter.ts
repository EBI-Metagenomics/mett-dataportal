import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import {openLocation} from '@jbrowse/core/util/io';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';
import {unzip} from '@gmod/bgzf-filehandle';
import {getIconForEssentiality} from "../../utils/appConstants";
import {GeneService} from "../../services/geneService";

export default class EssentialityAdapter extends BaseFeatureDataAdapter {
    static type = 'EssentialityAdapter';

    private gffLocation: string;
    private apiUrl: string;
    private isTypeStrain: boolean;
    private includeEssentiality: boolean;

    private cache: Map<string, SimpleFeature[]> = new Map();
    private gffCache: Map<string, SimpleFeatureSerialized[]>;

    // Generate a cache key
    private getCacheKey(region: any): string {
        return `${region.refName}:${region.start}-${region.end}`;
    }

    constructor(config: any) {
        super(config);
        this.gffLocation = config.gffGzLocation.value.uri;
        this.apiUrl = config.apiUrl.value;
        this.isTypeStrain = config.isTypeStrain.value;
        this.includeEssentiality = config.includeEssentiality.value;
        this.gffCache = new Map();
        // console.log('EssentialityAdapter initialized with includeEssentiality:', config.includeEssentiality.value);
        // console.log('EssentialityAdapter initialized with config:', config);
    }

    async freeResources(): Promise<void> {
        // console.log('EssentialityAdapter - freeResources called');
    }

    async getRefNames(): Promise<string[]> {
        // console.log('EssentialityAdapter - getRefNames called');
        return [];
    }

    private async fetchProteinSequence(feature: SimpleFeature): Promise<SimpleFeature> {
        // console.log('*****fetchProteinSequence', feature);
        const attributes = feature.get('attributes') || {};
        const locusTag = attributes.locus_tag;

        if (!locusTag) {
            return feature;
        }

        try {
            // console.log('Fetching protein sequence for:', locusTag);
            const proteinData = await GeneService.fetchGeneProteinSeq(locusTag);
            // console.log(`Fetched protein sequence for ${locusTag}:`, proteinData.protein_sequence?.substring(0, 20) + '...');

            feature.set('attributes', {
                ...attributes,
                protein_sequence: proteinData.protein_sequence
            });
        } catch (error) {
            console.warn(`Failed to fetch protein sequence for ${locusTag}:`, error);
        }
        return feature;
    }

    getFeatures(region: any): Observable<SimpleFeature> {
        const cacheKey = this.getCacheKey(region);
        // console.log('EssentialityAdapter - getFeatures called for region:', region);

        if (this.cache.has(cacheKey)) {
            // console.log('Using cached features for region:', cacheKey);
            return from(this.cache.get(cacheKey)!);
        }

        // Fetch and process features if not cached
        const featuresPromise = this.fetchGFF(region).then(async (gffFeatures) => {
            const featuresWithProtein = await Promise.all(
                gffFeatures.map(serializedFeature => {
                    const feature = new SimpleFeature(serializedFeature);
                    return this.fetchProteinSequence(feature);
                })
            );

            if (this.isTypeStrain && this.includeEssentiality) {
                const essentialityData = await GeneService.fetchEssentialityData(this.apiUrl, region.refName);
                return this.mergeAnnotationsWithEssentiality(featuresWithProtein, essentialityData);
            }

            return featuresWithProtein;
        })
            .catch((error) => {
                console.error('Error in getFeatures pipeline:', error);
                return [];
            });

        return from(featuresPromise).pipe(
            mergeMap((features) => {
                // console.log('Features ready to emit:', features.length);

                // Cache the features for this region
                this.cache.set(cacheKey, features);

                return from(features);
            }),
        );
    }

    async fetchGFF(region: any): Promise<SimpleFeatureSerialized[]> {
        // Check if the GFF data is already in the cache
        if (this.gffCache.has(this.gffLocation)) {
            const cachedFeatures = this.gffCache.get(this.gffLocation) || [];
            return this.filterFeaturesByRegion(cachedFeatures, region);
        }

        try {
            const gffFile = await openLocation({
                locationType: 'UriLocation',
                uri: this.gffLocation,
            }).readFile();

            const compressedData = await unzip(gffFile);
            const gffContents = new TextDecoder('utf-8').decode(compressedData);

            // Parse the GFF file and cache the features
            const features: SimpleFeatureSerialized[] = [];
            const lines = gffContents.split('\n');

            for (const line of lines) {
                if (line.startsWith('#') || !line.trim()) continue;

                const parts = line.split('\t');
                if (parts.length < 9) continue;

                const [refName, , type, start, end, , strand] = parts;
                const attributes = Object.fromEntries(
                    parts[8].split(';').map((attr: string) => attr.split('='))
                );

                if (type === 'gene' && attributes.locus_tag) {
                    features.push({
                        uniqueId: attributes.locus_tag,
                        refName,
                        start: parseInt(start, 10),
                        end: parseInt(end, 10),
                        strand: strand === '+' ? 1 : -1,
                        type,
                        attributes,
                    });
                }
            }

            // Cache the parsed features
            this.gffCache.set(this.gffLocation, features);

            // Filter features based on the region
            return this.filterFeaturesByRegion(features, region);
        } catch (error) {
            console.error('Error fetching GFF file:', error);
            return [];
        }
    }

    // Helper function to filter cached features by region
    private filterFeaturesByRegion(features: SimpleFeatureSerialized[], region: any): SimpleFeatureSerialized[] {
        return features.filter(
            (feature) =>
                feature.refName === region.refName &&
                feature.start < region.end && // Include overlaps
                feature.end > region.start
        );
    }

    // Optional method to clear the cache
    clearGFFCache() {
        this.gffCache.clear();
    }

    mergeAnnotationsWithEssentiality(
        gffFeatures: SimpleFeature[],
        essentialityData: Record<string, any>,
    ): SimpleFeature[] {
        return gffFeatures.map((feature) => {
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};

            const {attributes: _, ...featureWithoutAttributes} = featureData;
            const locusTag = attributes.locus_tag;
            const Essentiality = essentialityData[locusTag]?.essentiality?.toLowerCase() || 'unknown';
            const EssentialityVisual = getIconForEssentiality(Essentiality);

            const description = [
                attributes.gene ? `Gene: ${attributes.gene}` : null,
                `Locus Tag: ${locusTag}`,
                `Product: ${attributes.product}`,
                `Alias: ${attributes.alias}`,
                `Essentiality: ${Essentiality || 'unknown'}`,
            ].filter(Boolean).join('\n');

            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
                Essentiality,
                EssentialityVisual,
                // description,
            });
        });
    }


}
