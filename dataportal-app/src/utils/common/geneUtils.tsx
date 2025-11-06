import React from 'react';
import type { GeneMeta } from '../../interfaces/Gene';
import { ANNOTATION_INDICATORS, EXTERNAL_DB_URLS, BACINTERACTOME_SHINY_APP_BASE_URL } from './constants';

/**
 * Gets the color for essentiality status
 */
export const getColorForEssentiality = (essentiality: string): string => {
  switch (essentiality) {
    case 'essential':
      return '#FF0000'; // Red (critical importance)
    case 'essential_liquid':
      return '#1E90FF'; // Dodger Blue (fluid and vibrant for liquid)
    case 'essential_solid':
      return '#8B4513'; // Saddle Brown (earthy, solid representation)
    case 'not_essential':
      return '#555555'; // Dark Gray (subdued and non-critical)
    case 'unclear':
      return '#808080'; // Medium Gray (neutral and ambiguous)
    default:
      return '#DAA520'; // Goldenrod (fallback color)
  }
};

/**
 * Gets the icon for essentiality status
 */
export const getIconForEssentiality = (essentiality: string) => {
  switch (essentiality) {
    case 'essential':
      return '🧪🧫'; // Test Tube + Petri Dish (U+1F9EA U+1F9EB)
    case 'essential_liquid':
      return '🧪'; // Test Tube (U+1F9EA)
    case 'essential_solid':
      return '🧫'; // Petri Dish (U+1F9EB)
    case 'not_essential':
      return '⛔'; // No Entry Sign (U+26D4)
    case 'unclear':
    default:
      return '❓'; // Question Mark (U+2753)
  }
};

/**
 * Generates annotation availability indicators for a gene
 * Returns React elements with bordered colored boxes
 */
export const getAnnotationIndicators = (gene: GeneMeta): React.ReactNode => {
  const indicators: React.ReactNode[] = [];
  
  const boxStyle = (color: string, isLast: boolean) => ({
    display: 'inline-block',
    width: '18px',
    height: '18px',
    lineHeight: '18px',
    textAlign: 'center' as const,
    border: `2px solid ${color}`,
    borderRadius: '3px',
    color: color,
    backgroundColor: 'transparent',
    fontSize: '11px',
    fontWeight: 'bold' as const,
    marginRight: isLast ? '0' : '3px',
  });
  
  // Check each annotation type and add its colored bordered box if data is present
  if (gene.interpro && Array.isArray(gene.interpro) && gene.interpro.length > 0) {
    indicators.push(
      <span key="interpro" style={boxStyle(ANNOTATION_INDICATORS.interpro.color, false)}>
        {ANNOTATION_INDICATORS.interpro.icon}
      </span>
    );
  }
  
  if (gene.pfam && Array.isArray(gene.pfam) && gene.pfam.length > 0) {
    indicators.push(
      <span key="pfam" style={boxStyle(ANNOTATION_INDICATORS.pfam.color, false)}>
        {ANNOTATION_INDICATORS.pfam.icon}
      </span>
    );
  }
  
  if (gene.kegg && Array.isArray(gene.kegg) && gene.kegg.length > 0) {
    indicators.push(
      <span key="kegg" style={boxStyle(ANNOTATION_INDICATORS.kegg.color, false)}>
        {ANNOTATION_INDICATORS.kegg.icon}
      </span>
    );
  }
  
  if (gene.cog_id && Array.isArray(gene.cog_id) && gene.cog_id.length > 0) {
    indicators.push(
      <span key="cog" style={boxStyle(ANNOTATION_INDICATORS.cog_id.color, false)}>
        {ANNOTATION_INDICATORS.cog_id.icon}
      </span>
    );
  }
  
  if (gene.amr && Array.isArray(gene.amr) && gene.amr.length > 0) {
    indicators.push(
      <span key="amr" style={boxStyle(ANNOTATION_INDICATORS.amr.color, true)}>
        {ANNOTATION_INDICATORS.amr.icon}
      </span>
    );
  }
  
  return indicators.length > 0 ? <>{indicators}</> : '---';
};

/**
 * Gets the full tooltip text for annotation indicators with actual values
 * Uses [I] style boxes to match the visual representation
 */
export const getAnnotationIndicatorsTooltip = (gene: GeneMeta): string => {
  const tooltips: string[] = [];
  
  if (gene.interpro && Array.isArray(gene.interpro) && gene.interpro.length > 0) {
    const values = gene.interpro.join(', ');
    tooltips.push(`[${ANNOTATION_INDICATORS.interpro.icon}] ${ANNOTATION_INDICATORS.interpro.label}: ${values}`);
  }
  
  if (gene.pfam && Array.isArray(gene.pfam) && gene.pfam.length > 0) {
    const values = gene.pfam.join(', ');
    tooltips.push(`[${ANNOTATION_INDICATORS.pfam.icon}] ${ANNOTATION_INDICATORS.pfam.label}: ${values}`);
  }
  
  if (gene.kegg && Array.isArray(gene.kegg) && gene.kegg.length > 0) {
    const values = gene.kegg.join(', ');
    tooltips.push(`[${ANNOTATION_INDICATORS.kegg.icon}] ${ANNOTATION_INDICATORS.kegg.label}: ${values}`);
  }
  
  if (gene.cog_id && Array.isArray(gene.cog_id) && gene.cog_id.length > 0) {
    const values = gene.cog_id.join(', ');
    tooltips.push(`[${ANNOTATION_INDICATORS.cog_id.icon}] ${ANNOTATION_INDICATORS.cog_id.label}: ${values}`);
  }
  
  if (gene.amr && Array.isArray(gene.amr) && gene.amr.length > 0) {
    const amrValues = gene.amr.map(amr => {
      const parts = [];
      if (amr.drug_class) parts.push(amr.drug_class);
      if (amr.drug_subclass) parts.push(`(${amr.drug_subclass})`);
      return parts.join(' ');
    }).filter(v => v).join(', ');
    tooltips.push(`[${ANNOTATION_INDICATORS.amr.icon}] ${ANNOTATION_INDICATORS.amr.label}: ${amrValues}`);
  }
  
  return tooltips.length > 0 ? tooltips.join('\n') : 'No annotations available';
};

/**
 * Generates an external database link for a given database type and ID
 */
export const generateExternalDbLink = (dbType: keyof typeof EXTERNAL_DB_URLS, id: string): string => {
  const baseUrl = EXTERNAL_DB_URLS[dbType];

  switch (dbType) {
    case 'PFAM': {
      return `${baseUrl}${id}`;
    }
    case 'INTERPRO': {
      return `${baseUrl}${id}`;
    }
    case 'KEGG': {
      const keggId = id.startsWith('ko:') ? id.substring(3) : id;
      return `${baseUrl}${keggId}`;
    }
    case 'COG': {
      return `${baseUrl}${id}`;
    }
    case 'COG_CATEGORY': {
      return `${baseUrl}${id}`;
    }
    case 'UNIPROT': {
      return `${baseUrl}${id}`;
    }
    case 'GO': {
      return `${baseUrl}${id}`;
    }
    default:
      return `${baseUrl}${id}`;
  }
};

/**
 * Renders external database links for a given database type and IDs
 */
export const renderExternalDbLinks = (dbType: keyof typeof EXTERNAL_DB_URLS, ids: string[] | string): React.ReactNode => {
    if (!ids || (Array.isArray(ids) && ids.length === 0)) {
        return '---';
    }

    const idArray = Array.isArray(ids) ? ids : [ids];

    return idArray.map((id, index) => {
        const trimmedId = id.trim();
        if (!trimmedId || trimmedId === '---') {
            return null;
        }

        const link = generateExternalDbLink(dbType, trimmedId);

        return (
            <React.Fragment key={`${dbType}-${trimmedId}-${index}`}>
                <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={`View ${trimmedId} in ${dbType}`}
                    style={{ color: '#007bff', textDecoration: 'none' }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.textDecoration = 'underline';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.textDecoration = 'none';
                    }}
                >
                    {trimmedId}
                </a>
                {index < idArray.length - 1 && ', '}
            </React.Fragment>
        );
    }).filter(Boolean);
};

/**
 * Generates the Bacinteractome Shiny app URL for a UniProt ID
 */
export const getBacinteractomeUniprotUrl = (uniprot_id: string, species_name: string) => 
    `${BACINTERACTOME_SHINY_APP_BASE_URL}?species=${species_name}&protein=${uniprot_id}`;

