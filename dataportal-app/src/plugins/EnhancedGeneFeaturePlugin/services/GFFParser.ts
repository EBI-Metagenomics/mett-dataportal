import { SimpleFeatureSerialized } from '@jbrowse/core/util/simpleFeature';
import { decompressGffBytes, isGzipMagic } from './gffDecompression';

export class GFFParser {
  private gffCache: Map<string, SimpleFeatureSerialized[]> = new Map();

  async parseGFF(gffLocation: string): Promise<SimpleFeatureSerialized[]> {
    if (this.gffCache.has(gffLocation)) {
      return this.gffCache.get(gffLocation) || [];
    }

    try {
      const response = await fetch(gffLocation);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      const gffFile = new Uint8Array(arrayBuffer);
      let gffContents: string;

      if (isGzipMagic(gffFile)) {
        try {
          const decompressed = await decompressGffBytes(gffFile);
          gffContents = new TextDecoder('utf-8').decode(decompressed);
        } catch (bgzipError) {
          console.warn('Bgzip decompression failed:', bgzipError);
          throw new Error(`Failed to decompress gzip file: ${bgzipError}`);
        }
      } else {
        gffContents = new TextDecoder('utf-8').decode(gffFile);
      }

      const features = this.parseGffContents(gffContents);
      this.gffCache.set(gffLocation, features);
      return features;
    } catch (error) {
      console.error('Error fetching GFF file:', error);
      return [];
    }
  }

  private parseGffContents(gffContents: string): SimpleFeatureSerialized[] {
    const features: SimpleFeatureSerialized[] = [];
    const lines = gffContents.split('\n');

    for (const line of lines) {
      if (line.startsWith('#') || !line.trim()) continue;

      const parts = line.split('\t');
      if (parts.length < 9) continue;

      const [refName, , type, start, end, , strand] = parts;
      const attributes = this.parseAttributes(parts[8]);

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

    return features;
  }

  private parseAttributes(attrString: string): Record<string, string> {
    const attributes: Record<string, string> = {};
    for (const pair of attrString.split(';')) {
      const [key, ...valueParts] = pair.split('=');
      if (key && valueParts.length > 0) {
        attributes[key.trim()] = valueParts.join('=').trim();
      }
    }
    return attributes;
  }

  filterFeaturesByRegion(
    features: SimpleFeatureSerialized[],
    region: { refName: string; start: number; end: number }
  ): SimpleFeatureSerialized[] {
    return features.filter(
      feature =>
        feature.refName === region.refName &&
        feature.start < region.end &&
        feature.end > region.start
    );
  }

  clearGFFCache(): void {
    this.gffCache.clear();
  }
}
