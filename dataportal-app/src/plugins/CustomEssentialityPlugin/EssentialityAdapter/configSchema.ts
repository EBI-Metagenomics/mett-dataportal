import { ConfigurationSchema } from '@jbrowse/core/configuration';

const essentialityAdapterConfigSchema = ConfigurationSchema('EssentialityAdapter', {
  type: {
    type: 'string',
    defaultValue: 'EssentialityAdapter',
  },
  gffGzLocation: {
    type: 'fileLocation',
    defaultValue: { uri: '' },
  },
  apiUrl: {
    type: 'string',
    defaultValue: '',
  },
});

export default essentialityAdapterConfigSchema;
