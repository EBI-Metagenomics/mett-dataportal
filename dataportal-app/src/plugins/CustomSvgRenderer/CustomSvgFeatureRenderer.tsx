import BoxRendererType, {
    RenderArgsDeserialized,
    RenderResults,
} from '@jbrowse/core/pluggableElementTypes/renderers/BoxRendererType';
import { Feature } from '@jbrowse/core/util/simpleFeature';
import React from 'react';
import { BaseLayout } from '@jbrowse/core/util/layouts/BaseLayout';

export default class CustomSvgFeatureRenderer extends BoxRendererType {
    supportsSVG = true;

    constructor(args: any) {
        super(args);
        console.log('CustomSvgFeatureRenderer instantiated');
    }

    async render(renderProps: RenderArgsDeserialized): Promise<RenderResults> {
        console.log('Rendering with CustomSvgFeatureRenderer');

        const { features, regions, bpPerPx, width, height, layout: layoutUnknown } = renderProps;

        // Explicitly cast layout to BaseLayout<Feature>
        const layout = layoutUnknown as BaseLayout<Feature>;

        // Ensure features is a Map
        if (!features || !(features instanceof Map)) {
            console.warn('No features provided or invalid features format');
            return super.render(renderProps);
        }

        // Create a React component for the rendering
        const reactElement = (
            <svg width={width as number} height={height as number}>
                {Array.from(features.values()).map((feature: Feature) => {
                    const start = feature.get('start');
                    const end = feature.get('end');
                    const color = this.getColorBasedOnEssentiality(feature.get('essentiality_solid'));

                    // Use layout to determine y-coordinate
                    const top = layout.addRect(feature.id(), start, end, 10);

                    // Calculate x-coordinates
                    const [left, right] = [
                        (start - regions[0].start) / bpPerPx,
                        (end - regions[0].start) / bpPerPx,
                    ];

                    return (
                        <rect
                            key={feature.id()}
                            x={left}
                            y={top ?? 0}
                            width={right - left}
                            height={10}
                            fill={color}
                        />
                    );
                })}
            </svg>
        );

        // Call the parent render method and return the updated result
        const parentRenderResults = await super.render(renderProps);
        return {
            ...parentRenderResults,
            reactElement,
        };
    }

    private getColorBasedOnEssentiality(essentiality: string): string {
        const colorMap: Record<string, string> = {
            essential: 'red',
            not_essential: 'blue',
            liquid: 'orange',
            solid: 'green',
        };
        return colorMap[essentiality] || 'gray';
    }
}