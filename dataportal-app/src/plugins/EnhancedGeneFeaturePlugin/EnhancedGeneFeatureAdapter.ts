import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';
import {GeneService} from "../../services/gene";
import {GFFParser, FeatureProcessor, ExternalLinkProcessor} from "./services";

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
        
        console.log('🔧 EnhancedGeneFeatureAdapter constructed with:', {
            gffLocation: this.gffLocation,
            apiUrl: this.apiUrl,
            isTypeStrain: this.isTypeStrain,
            includeEssentiality: this.includeEssentiality,
            speciesName: this.speciesName
        });
    }

    async freeResources(): Promise<void> {
        // Cleanup resources if needed
    }

    async getRefNames(): Promise<string[]> {
        return [];
    }

    getFeatures(region: any): Observable<SimpleFeature> {
        console.log('🔧 EnhancedGeneFeatureAdapter.getFeatures called for region:', region);
        
        // Check if essentiality setting has changed and clear cache if needed
        if (this.lastEssentialitySetting !== null && this.lastEssentialitySetting !== this.includeEssentiality) {
            console.log('🔧 Essentiality setting changed, clearing cache');
            this.clearFeatureCache();
        }
        this.lastEssentialitySetting = this.includeEssentiality;
        
        const cacheKey = this.getCacheKey(region);

        if (this.cache.has(cacheKey)) {
            console.log('🔧 Returning cached features for:', cacheKey);
            return from(this.cache.get(cacheKey)!);
        }

        // Fetch and process features if not cached
        const featuresPromise = this.fetchGFF(region).then(async (gffFeatures) => {
            const featuresWithProtein = await Promise.all(
                gffFeatures.map(serializedFeature => {
                    const feature = new SimpleFeature(serializedFeature);
                    return FeatureProcessor.fetchProteinSequence(feature);
                })
            );

            // ALWAYS add PyHMMER information - this should work for ALL features
            const flattenedFeatures = FeatureProcessor.flattenAttributes(featuresWithProtein);
            
            // Debug: Check if PyHMMER info is present
            console.log('EnhancedGeneFeatureAdapter: PyHMMER info added to', 
                flattenedFeatures.filter(f => f.get('pyhmmerSearch')).length, 
                'out of', flattenedFeatures.length, 'features');
            
            if (this.isTypeStrain && this.includeEssentiality) {
                const essentialityData = await GeneService.fetchEssentialityData(this.apiUrl, region.refName);
                const featuresWithEssentiality = FeatureProcessor.mergeAnnotationsWithEssentiality(flattenedFeatures, essentialityData);
                
                // Debug: Check if PyHMMER info is preserved after essentiality merge
                console.log('EnhancedGeneFeatureAdapter: After essentiality merge, PyHMMER info present in',
                    featuresWithEssentiality.filter(f => f.get('pyhmmerSearch')).length, 'features');
                
                // Process external links AFTER essentiality merging
                return featuresWithEssentiality.map(feature => 
                    ExternalLinkProcessor.processExternalLinks(feature, this.speciesName)
                );
            } else {
                // Process external links for non-essentiality features
                // PyHMMER info is already in flattenedFeatures
                console.log('EnhancedGeneFeatureAdapter: Processing non-essentiality features, PyHMMER info present in',
                    flattenedFeatures.filter(f => f.get('pyhmmerSearch')).length, 'features');
                
                return flattenedFeatures.map(feature => 
                    ExternalLinkProcessor.processExternalLinks(feature, this.speciesName)
                );
            }
        })
            .catch((error) => {
                console.error('Error in getFeatures pipeline:', error);
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
        console.log('🔧 EnhancedGeneFeatureAdapter: Feature cache cleared');
    }
}
