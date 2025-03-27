const externalLinksConfig = [
    {
        label: 'InterPro',
        baseUrl: 'https://www.ebi.ac.uk/interpro/protein/entry/IPR/',
        getValue: (feature: any) => {
            // Check if interpro array exists and has entries
            if (feature.interpro && feature.interpro.length > 0) {
                // Return the first InterPro ID
                return feature.interpro[0];
            }
            return '';
        }
    },
    {
        label: 'KEGG',
        baseUrl: 'https://www.kegg.jp/kegg-bin/show_pathway?',
        getValue: (feature: any) => {
            return feature.kegg || '';
        }
    },
    {
        label: 'UniProt',
        baseUrl: 'https://www.uniprot.org/uniprot/',
        getValue: (feature: any) => {
            // Try to extract UniProt ID from various possible sources
            const uniprotSources = [
                feature.dbxref,
                feature.inference?.find((inf: string) => inf.includes('UniProtKB:'))
            ];

            const uniprotMatch = uniprotSources.find(src => src && src.includes('UniProtKB:'));

            return uniprotMatch
                ? uniprotMatch.split(':')[1]
                : '';
        }
    },
    {
        label: 'Gene Name',
        baseUrl: 'https://www.ncbi.nlm.nih.gov/gene/?term=',
        getValue: (feature: any) => {
            return feature.gene || feature.name || '';
        }
    }
];

export default externalLinksConfig;