import React from 'react';
import {Feature} from '@jbrowse/core/util';

interface CustomSvgFeatureRenderingProps {
    features: Map<string, Feature>;
    regions: any[];
    onFeatureClick?: (feature: any) => void;
}

export default function CustomSvgFeatureRendering({
                                                      features,
                                                      regions,
                                                      onFeatureClick,
                                                  }: CustomSvgFeatureRenderingProps) {
    const featureHeight = 15;
    const featureSpacing = 20;

    const essentialityColors: Record<string, string> = {
        essential: '#FF0000',
        not_essential: '#008000',
        unclear: '#808080',
        essential_liquid: '#FFA500',
        essential_solid: '#800080',
    };

    const regionStart = regions[0]?.start || 0;
    const regionEnd = regions[0]?.end || 0;
    const regionWidth = regionEnd - regionStart;

    return (
        <svg
            height={features.size * featureSpacing + 50}
            width={regionWidth}
        >
            <g>
                {Array.from(features.values()).map((feature, index) => {
                    const featureStart = feature.get('start');
                    const featureEnd = feature.get('end');

                    // Map the genomic coordinates to pixel coordinates
                    const x = Math.max(0, (featureStart - regionStart)); // Clip x to the visible region
                    const width = Math.max(
                        1,
                        Math.min(featureEnd, regionEnd) - Math.max(featureStart, regionStart),
                    ); // Clip width to the visible region

                    // Skip rendering if the feature is outside the region
                    if (featureEnd < regionStart || featureStart > regionEnd) {
                        return null;
                    }

                    const essentialityArray = feature.get('essentiality') || [];
                    const essentialityType =
                        essentialityArray[0]?.essentiality?.toLowerCase() || 'unclear';
                    const fillColor = essentialityColors[essentialityType] || '#000000';

                    return (
                        <g key={feature.id()}>
                            <rect
                                x={x}
                                y={index * featureSpacing}
                                width={width}
                                height={featureHeight}
                                fill={fillColor}
                                stroke="black"
                                onClick={() => {
                                    // console.log('Feature clicked:', feature.toJSON());
                                    if (onFeatureClick) {
                                        onFeatureClick(feature.toJSON());
                                    } else {
                                        const event = new CustomEvent('featureClick', {
                                            detail: {feature: feature.toJSON()},
                                        });
                                        window.dispatchEvent(event);
                                    }
                                }}
                            />
                            <text
                                x={x + 2}
                                y={index * featureSpacing + featureHeight / 2}
                                fontSize="12"
                                fill="black"
                                dominantBaseline="middle"
                                style={{fontWeight: 'bold'}}
                            >
                                {feature.get('attributes')?.locus_tag || feature.id()}
                            </text>
                        </g>
                    );
                })}
            </g>
        </svg>
    );
}
