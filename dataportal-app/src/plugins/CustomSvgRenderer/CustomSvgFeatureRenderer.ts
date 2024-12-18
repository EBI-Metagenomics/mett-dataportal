import BoxRendererType, { RenderArgsDeserialized, RenderResults } from '@jbrowse/core/pluggableElementTypes/renderers/BoxRendererType';
import { Feature } from '@jbrowse/core/util/simpleFeature';
import SimpleFeature from '@jbrowse/core/util/simpleFeature';

export default class CustomSvgFeatureRenderer extends BoxRendererType {
  supportsSVG = true;

  async render(renderProps: RenderArgsDeserialized): Promise<RenderResults> {
    const { features, ...rest } = renderProps;

    // Cast features to an array of Feature
    const featureArray = features as Feature[];

    // Decorate each feature with essentiality information
    const decoratedFeatures = featureArray.map((feature) => {
      const essentiality = this.getEssentialityData(feature);

      // Clone the feature's data and add a custom color
      const data = { ...feature.toJSON(), color: this.getColorBasedOnEssentiality(essentiality) };

      return new SimpleFeature(data);
    });

    // Call the parent render method with updated features
    return super.render({ features: decoratedFeatures, ...rest });
  }

  // Method to get essentiality data from the feature
  getEssentialityData(feature: Feature): string {
    return feature.get('essentiality_solid') || 'unknown';
  }

  // Method to determine color based on essentiality
  getColorBasedOnEssentiality(essentiality: string): string {
    switch (essentiality) {
      case 'essential':
        return 'red';
      case 'not_essential':
        return 'blue';
      case 'liquid':
        return 'orange';
      case 'solid':
        return 'green';
      default:
        return 'gray';
    }
  }
}
