import { generateExternalDbLink, getBacinteractomeUniprotUrl } from "../../../utils/appConstants";

export interface ExternalLink {
    label: string;
    url: string;
    id: string;
}

export class ExternalLinkProcessor {
    /**
     * Extract external links from feature attributes
     */
    static extractExternalLinks(attributes: any, speciesName?: string): Record<string, any> {
        const links: Record<string, any> = {};
        
        // Process COG
        if (attributes.cog) {
            const cogIds = Array.isArray(attributes.cog) ? attributes.cog : [attributes.cog];
            cogIds.forEach((id: string) => {
                if (/^[A-Z]$/.test(id)) {
                    // Single letter COG category
                    links.cogCategory = {
                        label: 'COG Category',
                        url: generateExternalDbLink('COG_CATEGORY', id),
                        id: id
                    };
                } else if (/^COG\d+$/.test(id)) {
                    // Full COG number
                    links.cog = {
                        label: 'COG',
                        url: generateExternalDbLink('COG', id),
                        id: id
                    };
                }
            });
        }
        
        // Process KEGG
        if (attributes.kegg) {
            const keggIds = Array.isArray(attributes.kegg) ? attributes.kegg : [attributes.kegg];
            const keggLinks: any[] = [];
            
            keggIds.forEach((id: string) => {
                // Split by comma in case there are multiple KEGG IDs
                const individualIds = id.split(',').map((i: string) => i.trim());
                individualIds.forEach((individualId: string) => {
                    const match = individualId.match(/^(ko:)?(K\d+)$/);
                    if (match) {
                        const keggId = match[2]; // Extract just the K number
                        keggLinks.push({
                            label: 'KEGG',
                            url: generateExternalDbLink('KEGG', keggId),
                            id: individualId
                        });
                    }
                });
            });
            
            if (keggLinks.length > 0) {
                links.kegg = keggLinks;
            }
        }
        
        // Process Pfam
        if (attributes.pfam) {
            const pfamIds = Array.isArray(attributes.pfam) ? attributes.pfam : [attributes.pfam];
            const pfamLinks: any[] = [];
            
            pfamIds.forEach((id: string) => {
                // Split by comma in case there are multiple Pfam IDs
                const individualIds = id.split(',').map((i: string) => i.trim());
                individualIds.forEach((individualId: string) => {
                    if (/^PF\d+$/.test(individualId)) {
                        pfamLinks.push({
                            label: 'Pfam',
                            url: generateExternalDbLink('PFAM', individualId),
                            id: individualId
                        });
                    }
                });
            });
            
            if (pfamLinks.length > 0) {
                links.pfam = pfamLinks;
            }
        }
        
        // Process InterPro
        if (attributes.interpro) {
            const interproIds = Array.isArray(attributes.interpro) ? attributes.interpro : [attributes.interpro];
            const interproLinks: any[] = [];
            
            interproIds.forEach((id: string) => {
                // Split by comma in case there are multiple InterPro IDs
                const individualIds = id.split(',').map((i: string) => i.trim());
                individualIds.forEach((individualId: string) => {
                    if (/^IPR\d+$/.test(individualId)) {
                        interproLinks.push({
                            label: 'InterPro',
                            url: generateExternalDbLink('INTERPRO', individualId),
                            id: individualId
                        });
                    }
                });
            });
            
            if (interproLinks.length > 0) {
                links.interpro = interproLinks;
            }
        }
        
        // Process GO terms
        // if (attributes.go || attributes.Ontology_term) {
        //     const goTerms = [];
        //     if (attributes.go) {
        //         goTerms.push(...(Array.isArray(attributes.go) ? attributes.go : [attributes.go]));
        //     }
        //     if (attributes.Ontology_term) {
        //         const ontologyTerms = Array.isArray(attributes.Ontology_term) ? attributes.Ontology_term : [attributes.Ontology_term];
        //         ontologyTerms.forEach((term: any) => {
        //             if (typeof term === 'string') {
        //                 goTerms.push(...term.split(',').map((t: string) => t.trim()));
        //             }
        //         });
        //     }
        //
        //     // Limit to first 10 GO terms to prevent performance issues
        //     const limitedGoTerms = goTerms.slice(0, 10);
        //     links.go = limitedGoTerms.map((term: string) => {
        //         if (/^GO:\d+$/.test(term)) {
        //             return {
        //                 label: 'GO',
        //                 url: generateExternalDbLink('GO', term),
        //                 id: term
        //             };
        //         }
        //         return null;
        //     }).filter(Boolean);
        //
        //     // Add a note if there are more GO terms
        //     if (goTerms.length > 10) {
        //         links.goNote = {
        //             label: 'GO',
        //             url: '#',
        //             id: `... and ${goTerms.length - 10} more GO terms`
        //         };
        //     }
        // }
        
        // Process Dbxref
        const dbxrefKey = Object.keys(attributes).find(key => key.toLowerCase() === 'dbxref');
        if (dbxrefKey) {
            const dbxrefValues = Array.isArray(attributes[dbxrefKey]) ? attributes[dbxrefKey] : [attributes[dbxrefKey]];
            const dbxrefLinks: any[] = [];
            
            dbxrefValues.forEach((dbxref: string) => {
                // Split by comma and process each value
                const values = dbxref.split(',').map((v: string) => v.trim());
                values.forEach((value: string) => {
                    if (/^COG:COG\d+$/.test(value)) {
                        const cogId = value.replace('COG:', '');
                        dbxrefLinks.push({
                            label: 'COG',
                            url: generateExternalDbLink('COG', cogId),
                            id: value
                        });
                    } else if (/^UniProt:[A-Z0-9]+$/.test(value)) {
                        const uniprotId = value.replace('UniProt:', '');
                        const url = speciesName 
                            ? getBacinteractomeUniprotUrl(uniprotId, speciesName)
                            : generateExternalDbLink('UNIPROT', uniprotId);
                        dbxrefLinks.push({
                            label: 'UniProt',
                            url: url,
                            id: value
                        });
                    } else if (/^Pfam:PF\d+$/.test(value)) {
                        const pfamId = value.replace('Pfam:', '');
                        dbxrefLinks.push({
                            label: 'Pfam',
                            url: generateExternalDbLink('PFAM', pfamId),
                            id: value
                        });
                    } else if (/^InterPro:IPR\d+$/.test(value)) {
                        const interproId = value.replace('InterPro:', '');
                        dbxrefLinks.push({
                            label: 'InterPro',
                            url: generateExternalDbLink('INTERPRO', interproId),
                            id: value
                        });
                    } else if (/^KEGG:ko:K\d+$/.test(value)) {
                        const keggId = value.replace('KEGG:ko:', '');
                        dbxrefLinks.push({
                            label: 'KEGG',
                            url: generateExternalDbLink('KEGG', keggId),
                            id: value
                        });
                    } else if (/^GO:GO:\d+$/.test(value)) {
                        const goId = value.replace('GO:', '');
                        dbxrefLinks.push({
                            label: 'GO',
                            url: generateExternalDbLink('GO', goId),
                            id: value
                        });
                    }
                });
            });
            
            if (dbxrefLinks.length > 0) {
                links.dbxref = dbxrefLinks;
            }
        }
        
        return links;
    }

    /**
     * Process external links for a feature and replace attributes with clickable links
     */
    static processExternalLinks(feature: any, speciesName?: string): any {
        // Get attributes from the feature - try multiple approaches
        let attributes = feature.get('attributes');
        if (!attributes || Object.keys(attributes).length === 0) {
            const featureData = feature.toJSON();
            attributes = featureData;
        }
        
        // Extract external links from attributes
        const externalLinks = this.extractExternalLinks(attributes, speciesName);
        
        // Replace existing attributes with clickable links
        if (Object.keys(externalLinks).length > 0) {
            Object.entries(externalLinks).forEach(([key, linkData]: [string, any]) => {
                if (Array.isArray(linkData)) {
                    // Handle arrays (like GO terms)
                    const linkTexts = linkData.map((link: any) => {
                        if (link && link.url && link.url !== '#') {
                            return `<a href="${link.url}" target="_blank" rel="noopener noreferrer">${link.id}</a>`;
                        } else if (link) {
                            return link.id;
                        }
                        return null;
                    }).filter(Boolean);
                    
                    if (linkTexts.length > 0) {
                        // Replace the original attribute with clickable links
                        const originalKey = this.getOriginalAttributeKey(key);
                        if (originalKey) {
                                                    // Set the attribute directly on the feature (flattened)
                        feature.set(originalKey, linkTexts.join(', '));
                        }
                    }
                } else if (linkData && linkData.url && linkData.url !== '#') {
                    // Handle single links - replace the original attribute
                    const originalKey = this.getOriginalAttributeKey(key);
                    if (originalKey) {
                        // Set the attribute directly on the feature (flattened)
                        feature.set(originalKey, `<a href="${linkData.url}" target="_blank" rel="noopener noreferrer">${linkData.id}</a>`);
                    }
                }
            });
        }
        
        return feature;
    }

    /**
     * Helper method to map external link keys back to original attribute names
     */
    private static getOriginalAttributeKey(externalKey: string): string | null {
        const keyMapping: Record<string, string> = {
            'cog': 'cog',
            'cogCategory': 'cog',
            'kegg': 'kegg',
            'pfam': 'pfam',
            'interpro': 'interpro',
            'go': 'Ontology_term',
            'dbxref': 'Dbxref'
        };
        
        return keyMapping[externalKey] || null;
    }
}
