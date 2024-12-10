import React from 'react';
import Attributes from '@jbrowse/core/BaseFeatureWidget/BaseFeatureDetail/Attributes';

type Feature = {
  get: (attribute: string) => any;
  toJSON: () => Record<string, any>;
};

type FeatureDetailsProps = {
  model: {
    feature: Feature;
  };
};

const AMRFeatureDetails: React.FC<FeatureDetailsProps> = ({ model }) => {
  const { feature } = model;

  if (!feature) {
    return <div>No feature selected</div>;
  }

  // Enhanced link generation
  const generateLinks = () => {
    const links: { label: string; url: string }[] = [];
    
    const interproID = feature.get('interpro');
    const uniprotID = feature.get('uniprot');
    const geneName = feature.get('name');

    if (interproID) {
      links.push({
        label: 'InterPro',
        url: `https://www.ebi.ac.uk/interpro/entry/${interproID}`
      });
    }

    if (uniprotID) {
      links.push({
        label: 'UniProt',
        url: `https://www.uniprot.org/uniprot/${uniprotID}`
      });
    }

    // Optional: Add gene name search link
    if (geneName) {
      links.push({
        label: 'Gene Search',
        url: `https://www.ncbi.nlm.nih.gov/gene/?term=${geneName}`
      });
    }

    return links;
  };

  const externalLinks = generateLinks();

  return (
    <div>
      <Attributes attributes={feature.toJSON()} />

      {externalLinks.length > 0 && (
        <div style={{ marginTop: '15px' }}>
          <h4>External References</h4>
          <ul>
            {externalLinks.map((link, idx) => (
              <li key={idx}>
                <a 
                  href={link.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AMRFeatureDetails;