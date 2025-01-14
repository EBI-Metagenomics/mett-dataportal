import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import {openLocation} from '@jbrowse/core/util/io';
import SimpleFeature, {SimpleFeatureSerialized} from '@jbrowse/core/util/simpleFeature';
import {from, Observable} from 'rxjs';
import {mergeMap} from 'rxjs/operators';

export default class EssentialityAdapter extends BaseFeatureDataAdapter {
    static type = 'EssentialityAdapter';

    private gffLocation: string;
    private apiUrl: string;

    constructor(config: any) {
        super(config);
        this.gffLocation = config.gffGzLocation.uri;
        this.apiUrl = config.apiUrl;
        console.log('EssentialityAdapter loaded with config:', this.config);
    }

    // Method to release resources if necessary
    async freeResources(): Promise<void> {
        // No resources to free in this implementation
    }

    async getRefNames() {
        console.log('EssentialityAdapter - getRefNames called');
        return [];
    }

    getFeatures(region: any): Observable<SimpleFeature> {
        console.log('EssentialityAdapter - getFeatures called', region);

        const featuresPromise = this.fetchGFF(region).then((gffFeatures) =>
            this.fetchEssentialityData(region.refName).then((essentialityData) =>
                this.mergeAnnotationsWithEssentiality(gffFeatures, essentialityData),
            ),
        );

        return from(featuresPromise).pipe(mergeMap((features) => from(features)));
    }

    async fetchGFF(region: any): Promise<SimpleFeatureSerialized[]> {
        const gffFile = await openLocation({
            locationType: 'UriLocation',
            uri: this.gffLocation,
        });
        const gffContents = await gffFile.readFile('utf8');
        const features: SimpleFeatureSerialized[] = [];

        const lines = gffContents.split('\n');
        for (const line of lines) {
            if (line.startsWith('#')) continue;
            const parts = line.split('\t');
            if (parts.length < 9) continue;

            const attributes = Object.fromEntries(parts[8].split(';').map((attr) => attr.split('=')));
            if (attributes.locus_tag) {
                features.push({
                    uniqueId: attributes.locus_tag,
                    start: parseInt(parts[3], 10),
                    end: parseInt(parts[4], 10),
                    strand: parts[6] === '+' ? 1 : -1,
                    type: parts[2],
                    refName: parts[0],
                    attributes,
                });
            }
        }

        return features;
    }

    async fetchEssentialityData(refName: string): Promise<Record<string, any>> {
        const response = await fetch(`${this.apiUrl}/essentiality/${refName}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch essentiality data for ${refName}`);
        }
        return response.json();
    }

    mergeAnnotationsWithEssentiality(
        gffFeatures: SimpleFeatureSerialized[],
        essentialityData: any,
    ): SimpleFeature[] {
        return gffFeatures.map((serializedFeature) => {
            const feature = new SimpleFeature(serializedFeature);
            const locusTag = feature.get('locus_tag') as string;
            const essentiality = essentialityData[locusTag]?.essentiality_data || [];

            return new SimpleFeature({
                ...feature.toJSON(),
                essentiality,
            });
        });
    }
}
