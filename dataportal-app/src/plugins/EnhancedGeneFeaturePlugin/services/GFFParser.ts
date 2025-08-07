import {unzip} from '@gmod/bgzf-filehandle';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import pako from 'pako';

export class GFFParser {
    private gffCache: Map<string, SimpleFeatureSerialized[]> = new Map();

    /**
     * Parse GFF file and extract gene features
     */
    async parseGFF(gffLocation: string): Promise<SimpleFeatureSerialized[]> {
        // Check if the GFF data is already in the cache
        if (this.gffCache.has(gffLocation)) {
            return this.gffCache.get(gffLocation) || [];
        }

        try {
            // Use the original URL through the Vite proxy
            const response = await fetch(gffLocation);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const arrayBuffer = await response.arrayBuffer();
            let gffFile = new Uint8Array(arrayBuffer);

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
                
                // Parse attributes more robustly
                const attributes: Record<string, string> = {};
                const attrString = parts[8];
                const attrPairs = attrString.split(';');
                
                for (const pair of attrPairs) {
                    const [key, ...valueParts] = pair.split('=');
                    if (key && valueParts.length > 0) {
                        attributes[key.trim()] = valueParts.join('=').trim();
                    }
                }

                // Look for gene features that have locus_tag
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
            this.gffCache.set(gffLocation, features);

            return features;
        } catch (error) {
            console.error('Error fetching GFF file:', error);
            return [];
        }
    }

    /**
     * Helper method to decompress bgzip files
     */
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
                
                let reading = true;
                while (reading) {
                    const { done, value } = await reader.read();
                    if (done) {
                        reading = false;
                    } else {
                        chunks.push(value);
                    }
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

    /**
     * Helper function to filter cached features by region
     */
    filterFeaturesByRegion(features: SimpleFeatureSerialized[], region: any): SimpleFeatureSerialized[] {
        return features.filter(
            (feature) =>
                feature.refName === region.refName &&
                feature.start < region.end && // Include overlaps
                feature.end > region.start
        );
    }

    /**
     * Optional method to clear the cache
     */
    clearGFFCache() {
        this.gffCache.clear();
    }
}
