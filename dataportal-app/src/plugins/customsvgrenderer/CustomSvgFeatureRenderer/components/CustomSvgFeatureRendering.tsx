import React from 'react'
import { Feature } from '@jbrowse/core/util'

interface CustomSvgFeatureRenderingProps {
    features: Map<string, Feature>
    regions: any[]
}

export default function CustomSvgFeatureRendering({
                                                      features,
                                                      regions,
                                                  }: CustomSvgFeatureRenderingProps) {
    console.log('✅ CustomSvgFeatureRendering features:', features)
    return (
        <svg>
            <g>
                {Array.from(features.values()).map((feature) => (
                    <rect
                        key={feature.id()}
                        x={feature.get('start')}
                        y={0}
                        width={feature.get('end') - feature.get('start')}
                        height={10}
                        fill="red"
                    />
                ))}
            </g>
        </svg>
    )
}
