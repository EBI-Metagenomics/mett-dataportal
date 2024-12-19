import { ConfigurationSchema } from '@jbrowse/core/configuration'

// Define the configuration schema for the custom SVG feature renderer
const CustomSvgFeatureRendererConfigSchema = ConfigurationSchema('CustomSvgFeatureRenderer', {
  color: {
    type: 'string',
    description: 'Color to use for the feature rendering',
    defaultValue: 'blue',
  },
  height: {
    type: 'number',
    description: 'Height of the rendered feature',
    defaultValue: 10,
  },
})

export default CustomSvgFeatureRendererConfigSchema
