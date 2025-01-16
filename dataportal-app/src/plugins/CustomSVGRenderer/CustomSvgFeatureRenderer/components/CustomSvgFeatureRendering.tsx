import React from 'react';
import { Feature } from '@jbrowse/core/util';

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
    console.log('✅ CustomSvgFeatureRendering regions:', regions);
    console.log('✅ Features passed to CustomSvgFeatureRendering:', Array.from(features.values()));

    const featureHeight = 15;
    const featureSpacing = 20;

    const essentialityColors: Record<string, string> = {
        essential: '#FF0000',
        not_essential: '#008000',
        unclear: '#808080',
        essential_liquid: '#FFA500',
        essential_solid: '#800080',
    };

    const svgHeight = features.size * featureSpacing + 50; // Add padding
    const svgWidth = regions[0]?.end - regions[0]?.start || 1000; // Adjust width dynamically

    return (
        <svg height={svgHeight} width={svgWidth}>
            <g>
                {Array.from(features.values()).map((feature, index) => {
                    const x = feature.get('start') - regions[0].start; // Adjust to align with region
                    const y = index * featureSpacing;
                    const width = Math.max(1, feature.get('end') - feature.get('start')); // Ensure width > 0
                    const essentialityArray = feature.get('essentiality') || [];
                    const essentialityType =
                        essentialityArray[0]?.essentiality?.toLowerCase() || 'unclear';
                    const fillColor = essentialityColors[essentialityType] || '#000000';

                    console.log(`Rendering feature ${index}:`, {
                        x,
                        y,
                        width,
                        height: featureHeight,
                        essentialityType,
                        fillColor,
                    });

                    if (feature.get('end') < regions[0].start || feature.get('start') > regions[0].end) {
                        console.warn(`Feature ${feature.id()} is outside the visible region.`);
                        return null; // Skip rendering
                    }

                    return (
                        <g key={feature.id()}>
                            <rect
                                x={x}
                                y={y}
                                width={width}
                                height={featureHeight}
                                fill={fillColor}
                                stroke="black"
                                onClick={() => {
                                    console.log('Feature clicked:', feature.toJSON());
                                    if (onFeatureClick) {
                                        onFeatureClick(feature.toJSON());
                                    } else {
                                        const event = new CustomEvent('featureClick', {
                                            detail: { feature: feature.toJSON() },
                                        });
                                        window.dispatchEvent(event);
                                    }
                                }}
                            />
                            <text
                                x={x + 2}
                                y={y + featureHeight / 2}
                                fontSize="10"
                                fill="black"
                                dominantBaseline="middle"
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
