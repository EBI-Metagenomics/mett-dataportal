/**
 * Utility functions to enhance JBrowse feature panel with external database links
 */

import { EXTERNAL_DB_URLS, generateExternalDbLink } from './appConstants';

export interface ExternalLink {
    label: string;
    url: string;
    id: string;
}

export const getExternalLinks = (feature: any): ExternalLink[] => {
    const links: ExternalLink[] = [];
    
    // Process InterPro IDs
    if (feature.interpro) {
        const interproIds = Array.isArray(feature.interpro) ? feature.interpro : [feature.interpro];
        interproIds.forEach((id: string) => {
            if (/^IPR\d+$/.test(id)) {
                links.push({
                    label: 'InterPro',
                    url: generateExternalDbLink('INTERPRO', id),
                    id
                });
            }
        });
    }
    
    // Process KEGG IDs (handle both K numbers and ko:K numbers)
    if (feature.kegg) {
        const keggIds = Array.isArray(feature.kegg) ? feature.kegg : [feature.kegg];
        keggIds.forEach((id: string) => {
            const match = id.match(/^(ko:)?(K\d+)$/);
            if (match) {
                const keggId = match[2]; // Extract just the K number
                links.push({
                    label: 'KEGG',
                    url: generateExternalDbLink('KEGG', keggId),
                    id
                });
            }
        });
    }
    
    // Process COG IDs (handle single letters like 'L' and full COG numbers)
    if (feature.cog) {
        const cogIds = Array.isArray(feature.cog) ? feature.cog : [feature.cog];
        cogIds.forEach((id: string) => {
            if (/^[A-Z]$/.test(id)) {
                // Single letter COG category
                links.push({
                    label: 'COG Category',
                    url: generateExternalDbLink('COG_CATEGORY', id),
                    id
                });
            } else if (/^COG\d+$/.test(id)) {
                // Full COG number
                links.push({
                    label: 'COG',
                    url: generateExternalDbLink('COG', id),
                    id
                });
            }
        });
    }
    
    // Process GO terms (handle comma-separated lists)
    if (feature.go || feature.Ontology_term) {
        const goTerms = [];
        if (feature.go) {
            goTerms.push(...(Array.isArray(feature.go) ? feature.go : [feature.go]));
        }
        if (feature.Ontology_term) {
            const ontologyTerms = Array.isArray(feature.Ontology_term) ? feature.Ontology_term : [feature.Ontology_term];
            ontologyTerms.forEach((term: any) => {
                if (typeof term === 'string') {
                    goTerms.push(...term.split(',').map((t: string) => t.trim()));
                }
            });
        }
        
        // Limit to first 10 GO terms to prevent performance issues
        const limitedGoTerms = goTerms.slice(0, 10);
        limitedGoTerms.forEach((term: string) => {
            if (/^GO:\d+$/.test(term)) {
                links.push({
                    label: 'GO',
                    url: generateExternalDbLink('GO', term),
                    id: term
                });
            }
        });
        
        // Add a note if there are more GO terms
        if (goTerms.length > 10) {
            links.push({
                label: 'GO',
                url: '#',
                id: `... and ${goTerms.length - 10} more GO terms`
            });
        }
    }
    
    // Process Pfam IDs
    if (feature.pfam) {
        const pfamIds = Array.isArray(feature.pfam) ? feature.pfam : [feature.pfam];
        pfamIds.forEach((id: string) => {
            if (/^PF\d+$/.test(id)) {
                links.push({
                    label: 'Pfam',
                    url: generateExternalDbLink('PFAM', id),
                    id
                });
            }
        });
    }
    
    // Process Dbxref IDs (comma-separated values like "COG:COG0593,UniProt:A7V2E8")
    if (feature.dbxref) {
        const dbxrefValues = Array.isArray(feature.dbxref) ? feature.dbxref : [feature.dbxref];
        dbxrefValues.forEach((dbxref: string) => {
            // Split by comma and process each value
            const values = dbxref.split(',').map((v: string) => v.trim());
            values.forEach((value: string) => {
                if (/^COG:COG\d+$/.test(value)) {
                    const cogId = value.replace('COG:', '');
                    links.push({
                        label: 'COG',
                        url: generateExternalDbLink('COG', cogId),
                        id: value
                    });
                } else if (/^UniProt:[A-Z0-9]+$/.test(value)) {
                    const uniprotId = value.replace('UniProt:', '');
                    links.push({
                        label: 'UniProt',
                        url: generateExternalDbLink('UNIPROT', uniprotId),
                        id: value
                    });
                }
            });
        });
    }
    
    return links;
};




