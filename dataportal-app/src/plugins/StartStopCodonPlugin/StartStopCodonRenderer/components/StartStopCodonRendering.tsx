import React from 'react';
import { Feature } from '@jbrowse/core/util';

interface StartStopCodonRenderingProps {
  features: Map<string, Feature>;
  regions: any[];
  config: any;
}

export default function StartStopCodonRendering({
  features,
  regions,
  config,
}: StartStopCodonRenderingProps) {
  const region = regions[0];
  console.log('Features passed to renderer:', [...features.values()]);
  console.log('✅ StartStopCodonRendering ReactComponent rendering...');


  return (
    <svg>
      {[...features.values()].map((feature) => {
        const start = feature.get('start');
        const end = feature.get('end');
        const strand = feature.get('strand');
        const featureId = feature.id();

        // Calculate codon regions
        const startCodon = strand === '+'
          ? { start, end: start + 3 }
          : { start: end - 3, end };
        const stopCodon = strand === '+'
          ? { start: end - 3, end }
          : { start, end: start + 3 };

        return (
          <g key={featureId}>
            {/* Start codon */}
            <rect
              x={startCodon.start - region.start}
              y={0}
              width={startCodon.end - startCodon.start}
              height={config.height}
              fill="green"
              stroke="black"
            />
            {/* Stop codon */}
            <rect
              x={stopCodon.start - region.start}
              y={0}
              width={stopCodon.end - stopCodon.start}
              height={config.height}
              fill="red"
              stroke="black"
            />
          </g>
        );
      })}
    </svg>
  );
}
