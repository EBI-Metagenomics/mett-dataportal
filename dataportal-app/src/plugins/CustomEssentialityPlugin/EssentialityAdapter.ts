import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import {openLocation} from '@jbrowse/core/util/io';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';
import {unzip} from '@gmod/bgzf-filehandle';
import {getIconForEssentiality} from "../../utils/appConstants";
import {GeneService} from "../../services/geneService";
import pako from 'pako';

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

    private flattenAttributes(features: SimpleFeature[]): SimpleFeature[] {
        return features.map(feature => {
            const featureData = feature.toJSON();
            const attributes = featureData.attributes && typeof featureData.attributes === 'object'
                ? featureData.attributes as Record<string, string>
                : {};
            const {attributes: _, ...featureWithoutAttributes} = featureData;
            return new SimpleFeature({
                ...featureWithoutAttributes,
                ...attributes,
            });
        });
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

            const flattenedFeatures = this.flattenAttributes(featuresWithProtein);
            if (this.isTypeStrain && this.includeEssentiality) {
                const essentialityData = await GeneService.fetchEssentialityData(this.apiUrl, region.refName);
                return this.mergeAnnotationsWithEssentiality(flattenedFeatures, essentialityData);
            }

            return flattenedFeatures;
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
            // Use the original URL through the Vite proxy
            const response = await fetch(this.gffLocation);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const arrayBuffer = await response.arrayBuffer();
            let gffFile = new Uint8Array(arrayBuffer);

            // Debug: Check the first few bytes to understand the file format
            console.log('GFF file loaded, size:', gffFile.length);
            
            // Check if it's actually a gzip file by looking at the magic number
            const isGzip = gffFile[0] === 0x1f && gffFile[1] === 0x8b;

            // Use a bgzip-compatible decompressor
            let gffContents: string;
            
            // Check if the file is actually compressed
            if (isGzip) {
                // File is compressed, try to decompress
                try {
                    // First try with bgzip decompression
                    const compressedData = await this.decompressBgzip(gffFile);
                    gffContents = new TextDecoder('utf-8').decode(compressedData);
                } catch (bgzipError) {
                    // Fallback to standard gzip if bgzip fails
                    console.warn('Bgzip decompression failed, trying standard gzip:', bgzipError);
                    try {
                        const compressedData = await unzip(gffFile);
                        gffContents = new TextDecoder('utf-8').decode(compressedData);
                    } catch (gzipError) {
                        throw new Error(`Failed to decompress gzip file: ${gzipError}`);
                    }
                }
            } else {
                // File is not compressed, read as plain text
                console.log('File appears to be uncompressed, reading as plain text');
                gffContents = new TextDecoder('utf-8').decode(gffFile);
            }

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

    // Helper method to decompress bgzip files
    private async decompressBgzip(data: Uint8Array): Promise<Uint8Array> {
        // Try multiple decompression approaches for bgzip files
        
        // Method 1: Try pako with different options
        try {
            const decompressed = pako.inflate(data);
            return new Uint8Array(decompressed);
        } catch (error) {
            // Silently try next method
        }

        // Method 2: Try pako with raw option (for bgzip)
        try {
            const decompressed = pako.inflateRaw(data);
            return new Uint8Array(decompressed);
        } catch (error) {
            // Silently try next method
        }

        // Method 3: Try browser's built-in decompression
        if (typeof window !== 'undefined' && 'DecompressionStream' in window) {
            try {
                const stream = new ReadableStream({
                    start(controller) {
                        controller.enqueue(data);
                        controller.close();
                    }
                });
                
                const decompressedStream = stream.pipeThrough(new DecompressionStream('gzip'));
                const reader = decompressedStream.getReader();
                const chunks: Uint8Array[] = [];
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    chunks.push(value);
                }
                
                // Combine all chunks
                const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
                const result = new Uint8Array(totalLength);
                let offset = 0;
                for (const chunk of chunks) {
                    result.set(chunk, offset);
                    offset += chunk.length;
                }
                
                return result;
            } catch (error) {
                // Silently try next method
            }
        }

        // Method 4: Try the original unzip function as last resort
        try {
            return await unzip(data);
        } catch (error) {
            console.warn('All decompression methods failed for bgzip file');
        }

        // If all methods fail, throw a comprehensive error
        throw new Error('All decompression methods failed for bgzip file');
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
            const locusTag = featureData.locus_tag;
            const Essentiality =
                locusTag && typeof locusTag === 'string' && essentialityData[locusTag]
                    ? essentialityData[locusTag].essentiality?.toLowerCase() || 'unknown'
                    : 'unknown';
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
