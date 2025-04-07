import React from 'react'
import { observer } from 'mobx-react'

const CustomTrackContainer = observer(({ model }: { model: any }) => {
  console.log('✅ CustomTrackContainer rendered!')
  const TrackRenderingComponent = model.RenderingComponent

  return (
    <div style={{ border: '1px solid #ccc' }}>
      <div style={{ background: '#f0f0f0', padding: '4px 8px', fontWeight: 'bold' }}>
        {model.configuration?.name ?? 'Track'}
      </div>
      <TrackRenderingComponent model={model} />
    </div>
  )
})

export default CustomTrackContainer
