import React from 'react';

interface MyCustomFeaturePanelProps {
  feature: {
    id: string;
    start: number;
    end: number;
    description?: string;
    [key: string]: any;
  };
}

const MyCustomFeaturePanel: React.FC<MyCustomFeaturePanelProps> = ({ feature }) => {
  return (
    <div style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
      <h4>Feature Details</h4>
      <p><strong>ID:</strong> {feature.id}</p>
      <p><strong>Start Position:</strong> {feature.start}</p>
      <p><strong>End Position:</strong> {feature.end}</p>
      {feature.description && <p><strong>Description:</strong> {feature.description}</p>}
      <h5>Additional Metadata</h5>
      <ul>
        {Object.entries(feature)
          .filter(([key]) => key !== 'id' && key !== 'start' && key !== 'end' && key !== 'description')
          .map(([key, value]) => (
            <li key={key}>
              <strong>{key}:</strong> {value.toString()}
            </li>
          ))}
      </ul>
    </div>
  );
};

export default MyCustomFeaturePanel;
