import React from 'react'
import {Feature} from '@jbrowse/core/util'


interface CustomSvgRenderingProps {
    features: Feature[]
    regions: any[]
}

export default function CustomSvgRendering({features, regions}: CustomSvgRenderingProps) {
    return (
        <g>
            {features.map((feature) => (
                <rect
                    key={feature.id()}
                    x={feature.get('start')}
                    y={0}
                    width={feature.get('end') - feature.get('start')}
                    height={10}
                    fill="blue"
                />
            ))}
        </g>
    )
}
