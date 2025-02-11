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

    private cache: Map<string, SimpleFeature[]> = new Map(); // Cache for features by region key

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

    getFeatures(region: any): Observable<SimpleFeature> {
        const cacheKey = this.getCacheKey(region);
        // console.log('EssentialityAdapter - getFeatures called for region:', region);

        if (this.cache.has(cacheKey)) {
            // console.log('Using cached features for region:', cacheKey);
            return from(this.cache.get(cacheKey)!);
        }

        // Fetch and process features if not cached
        const featuresPromise = this.fetchGFF(region).then((gffFeatures) => {
            if (this.isTypeStrain && this.includeEssentiality) {
                return GeneService.fetchEssentialityData(this.apiUrl, region.refName).then((essentialityData) =>
                    this.mergeAnnotationsWithEssentiality(gffFeatures, essentialityData),
                );
            }
            // For non-type strains or includeEssentiality is false, flatten attributes
            return gffFeatures.map((serializedFeature) => {
                const feature = new SimpleFeature(serializedFeature);
                const featureData = feature.toJSON();

                // Ensure attributes is an object before spreading
                const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                    ? featureData.attributes
                    : {};

                const {attributes: _, ...featureWithoutAttributes} = featureData;
                const Essentiality = '';
                const EssentialityVisual = '';

                return new SimpleFeature({
                    ...featureWithoutAttributes,
                    ...attributes, // Flatten attributes
                    Essentiality,
                    EssentialityVisual
                });
            });
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
        // console.log('Fetching GFF file from:', this.gffLocation);

        try {
            const gffFile = await openLocation({
                locationType: 'UriLocation',
                uri: this.gffLocation,
            }).readFile();

            const compressedData = await unzip(gffFile);
            const gffContents = new TextDecoder('utf-8').decode(compressedData);

            // console.log('GFF file successfully decompressed.');

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
                    const featureStart = parseInt(start, 10);
                    const featureEnd = parseInt(end, 10);

                    if (
                        refName === region.refName &&
                        featureStart < region.end && // Adjusted to include overlaps
                        featureEnd > region.start
                    ) {
                        features.push({
                            uniqueId: attributes.locus_tag,
                            refName,
                            start: featureStart,
                            end: featureEnd,
                            strand: strand === '+' ? 1 : -1,
                            type,
                            attributes,
                        });

                        // console.log(`Parsed GFF feature: ${attributes.locus_tag}`);
                    }
                }
            }

            // console.log('Total GFF features parsed:', features.length);
            return features;
        } catch (error) {
            console.error('Error fetching GFF file:', error);
            return [];
        }
    }

    mergeAnnotationsWithEssentiality(
        gffFeatures: SimpleFeatureSerialized[],
        essentialityData: Record<string, any>,
    ): SimpleFeature[] {
        // console.log('Merging annotations with essentiality data...');
        // console.log('Number of GFF features:', gffFeatures.length);
        // console.log('Number of essentiality entries:', Object.keys(essentialityData).length);

        const mergedFeatures = gffFeatures.map((serializedFeature) => {
            const feature = new SimpleFeature(serializedFeature);
            const attributes = feature.get('attributes') || {};
            const locusTag = attributes.locus_tag;

            // Extract essentiality data
            const essentialityArray = essentialityData[locusTag]?.essentiality_data || [];
            const Essentiality = essentialityArray.length
                ? essentialityArray[0]?.essentiality.toLowerCase()
                : '';

            const EssentialityVisual = getIconForEssentiality(Essentiality);

            // Flatten attributes and add essentiality
            const {attributes: _, ...featureWithoutAttributes} = feature.toJSON();
            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
                Essentiality,
                EssentialityVisual,
            });
        });

        // console.log('Final merged features count:', mergedFeatures.length);
        // console.log('Final merged features:', mergedFeatures);
        return mergedFeatures;
    }


}
