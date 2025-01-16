import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import {openLocation} from '@jbrowse/core/util/io';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';
import {unzip} from '@gmod/bgzf-filehandle';

export default class EssentialityAdapter extends BaseFeatureDataAdapter {
    static type = 'EssentialityAdapter';

    private gffLocation: string;
    private apiUrl: string;

    private cache: Map<string, SimpleFeature[]> = new Map(); // Cache for features by region key

    // Generate a cache key
    private getCacheKey(region: any): string {
        return `${region.refName}:${region.start}-${region.end}`;
    }

    constructor(config: any) {
        super(config);
        this.gffLocation = config.gffGzLocation.value.uri;
        this.apiUrl = config.apiUrl.value;
        console.log('EssentialityAdapter initialized with config:', config);
    }

    async freeResources(): Promise<void> {
        console.log('EssentialityAdapter - freeResources called');
    }

    async getRefNames(): Promise<string[]> {
        console.log('EssentialityAdapter - getRefNames called');
        return [];
    }

    getFeatures(region: any): Observable<SimpleFeature> {
        const cacheKey = this.getCacheKey(region);
        console.log('EssentialityAdapter - getFeatures called for region:', region);

        if (this.cache.has(cacheKey)) {
            console.log('Using cached features for region:', cacheKey);
            return from(this.cache.get(cacheKey)!);
        }

        // Fetch and process features if not cached
        const featuresPromise = this.fetchGFF(region)
            .then((gffFeatures) => {
                console.log('Fetched GFF features:', gffFeatures.length);
                return this.fetchEssentialityData(region.refName).then((essentialityData) => {
                    console.log('Fetched essentiality data:', Object.keys(essentialityData).length);
                    return this.mergeAnnotationsWithEssentiality(gffFeatures, essentialityData);
                });
            })
            .catch((error) => {
                console.error('Error in getFeatures pipeline:', error);
                return [];
            });

        return from(featuresPromise).pipe(
            mergeMap((features) => {
                console.log('Features ready to emit:', features.length);

                // Cache the features for this region
                this.cache.set(cacheKey, features);

                return from(features);
            }),
        );
    }

    async fetchGFF(region: any): Promise<SimpleFeatureSerialized[]> {
        console.log('Fetching GFF file from:', this.gffLocation);

        try {
            const gffFile = await openLocation({
                locationType: 'UriLocation',
                uri: this.gffLocation,
            }).readFile();

            const compressedData = await unzip(gffFile);
            const gffContents = new TextDecoder('utf-8').decode(compressedData);

            console.log('GFF file successfully decompressed.');

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

                        console.log(`Parsed GFF feature: ${attributes.locus_tag}`);
                    }
                }
            }

            console.log('Total GFF features parsed:', features.length);
            return features;
        } catch (error) {
            console.error('Error fetching GFF file:', error);
            return [];
        }
    }

    async fetchEssentialityData(refName: string): Promise<Record<string, any>> {
        console.log('Fetching essentiality data for:', refName);

        try {
            const response = await fetch(`${this.apiUrl}/${refName}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch essentiality data for ${refName}`);
            }

            const data = await response.json();
            console.log(`Essentiality data fetched for ${refName}:`, Object.keys(data).length);
            return data;
        } catch (error) {
            console.error('Error fetching essentiality data:', error);
            return {};
        }
    }

    mergeAnnotationsWithEssentiality(
        gffFeatures: SimpleFeatureSerialized[],
        essentialityData: Record<string, any>,
    ): SimpleFeature[] {
        console.log('Merging annotations with essentiality data...');
        console.log('Number of GFF features:', gffFeatures.length);
        console.log('Number of essentiality entries:', Object.keys(essentialityData).length);

        const mergedFeatures = gffFeatures.map((serializedFeature) => {
            const feature = new SimpleFeature(serializedFeature);
            const locusTag = feature.get('attributes')?.locus_tag;

            const essentiality = essentialityData[locusTag]?.essentiality_data || [];
            if (essentiality.length > 0) {
                console.log(`Merging essentiality data for ${locusTag}:`, essentiality);
            } else {
                console.warn(`No essentiality data found for ${locusTag}`);
            }

            return new SimpleFeature({
                ...feature.toJSON(),
                essentiality,
            });
        });

        console.log('Final merged features count:', mergedFeatures.length);
        return mergedFeatures;
    }
}
