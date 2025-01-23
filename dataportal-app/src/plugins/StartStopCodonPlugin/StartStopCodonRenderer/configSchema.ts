import {ConfigurationSchema} from '@jbrowse/core/configuration'

/**
 * #config StartStopCodonRenderer
 */
function x() {
} // eslint-disable-line @typescript-eslint/no-unused-vars

const StartStopCodonRenderer = ConfigurationSchema(
    'StartStopCodonRenderer',
    {
        // Existing slots...

        /**
         * #slot
         */
        startCodonColor: {
            type: 'color',
            description: 'Color of the start codon',
            defaultValue: 'green',
            contextVariable: ['feature'],
        },

        /**
         * #slot
         */
        stopCodonColor: {
            type: 'color',
            description: 'Color of the stop codon',
            defaultValue: 'red',
            contextVariable: ['feature'],
        },
    },
    {explicitlyTyped: true},
);


export default StartStopCodonRenderer
