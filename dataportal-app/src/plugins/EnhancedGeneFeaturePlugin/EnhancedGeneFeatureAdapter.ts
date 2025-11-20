import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';
import {GeneService} from "../../services/gene";
import {GFFParser, FeatureProcessor} from "./services";

export default class EnhancedGeneFeatureAdapter extends BaseFeatureDataAdapter {
    static type = 'EnhancedGeneFeatureAdapter';

    private gffLocation: string;
    private apiUrl: string;
    private isTypeStrain: boolean;
    private includeEssentiality: boolean;
    private speciesName?: string;

    private cache: Map<string, SimpleFeature[]> = new Map();
    private gffParser: GFFParser;
    private lastEssentialitySetting: boolean | null = null;

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
        this.speciesName = config.speciesName?.value || config.speciesName;
        this.gffParser = new GFFParser();
        
    }

    async freeResources(): Promise<void> {
        // Cleanup resources if needed
    }

    async getRefNames(): Promise<string[]> {
        return [];
    }

    getFeatures(region: any): Observable<SimpleFeature> {
        // Check if essentiality setting has changed and clear cache if needed
        if (this.lastEssentialitySetting !== null && this.lastEssentialitySetting !== this.includeEssentiality) {
            this.clearFeatureCache();
        }
        this.lastEssentialitySetting = this.includeEssentiality;
        
        const cacheKey = this.getCacheKey(region);

        if (this.cache.has(cacheKey)) {
            return from(this.cache.get(cacheKey)!);
        }

        // Fetch and process features if not cached
        const featuresPromise = this.fetchGFF(region).then(async (gffFeatures) => {
            // Convert to SimpleFeature and flatten attributes for JBrowse display
            const features = gffFeatures.map(serializedFeature => new SimpleFeature(serializedFeature));
            const flattenedFeatures = FeatureProcessor.flattenAttributes(features);
            
            // Add essentiality data for feature coloring if this is a type strain
            if (this.isTypeStrain && this.includeEssentiality) {
                const essentialityData = await GeneService.fetchEssentialityData(this.apiUrl, region.refName);
                return FeatureProcessor.mergeAnnotationsWithEssentiality(flattenedFeatures, essentialityData);
            }
            
            return flattenedFeatures;
        })
            .catch(() => {
                return [];
            });

        return from(featuresPromise).pipe(
            mergeMap((features) => {
                // Cache the features for this region
                this.cache.set(cacheKey, features);

                return from(features);
            }),
        );
    }

    async fetchGFF(region: any): Promise<SimpleFeatureSerialized[]> {
        const allFeatures = await this.gffParser.parseGFF(this.gffLocation);
        return this.gffParser.filterFeaturesByRegion(allFeatures, region);
    }

    // Optional method to clear the cache
    clearGFFCache() {
        this.gffParser.clearGFFCache();
    }

    // Clear the adapter's feature cache
    clearFeatureCache() {
        this.cache.clear();
    }
}
