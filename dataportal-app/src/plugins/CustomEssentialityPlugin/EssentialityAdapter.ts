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
        this.gffLocation = config.gffGzLocation.value.uri;
        this.apiUrl = config.apiUrl.value;
        console.log('EssentialityAdapter loaded with config:', this.config);
        console.log('EssentialityAdapter loaded with config.gffGzLocation.value.uri:', config.gffGzLocation.value.uri);
        console.log('EssentialityAdapter loaded with config.apiUrl.value:', config.apiUrl.value);
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
        try {
            console.log('Fetching GFF file from:', this.gffLocation);

            const gffFile = await openLocation({
                locationType: 'UriLocation',
                uri: this.gffLocation, // Ensure this is a string
            });

            const gffContents = await gffFile.readFile('utf8');
            console.log('GFF file successfully read.');

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
        } catch (error) {
            console.error('Error fetching GFF file:', error);
            throw new Error('Failed to fetch GFF file.');
        }
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
