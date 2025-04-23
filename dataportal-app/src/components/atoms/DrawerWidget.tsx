import React from 'react'
import { observer } from 'mobx-react'
import { Drawer } from '@mui/material'
import BaseFeatureWidgetModel  from '@jbrowse/plugin-linear-genome-view'

interface Props {
  session: {
    visibleWidget?: string
    widgets: Map<string, BaseFeatureWidgetModel>
    hideWidget: (arg: string) => void
    renderWidget?: (widget: BaseFeatureWidgetModel) => React.ReactNode
    drawerWidth?: number
    drawerPosition?: 'left' | 'right' | 'top' | 'bottom'
  }
}

const DrawerWidget = observer(function DrawerWidget({ session }: Props) {
  const widget = session.visibleWidget
    ? session.widgets.get(session.visibleWidget)
    : undefined

  return (
    <Drawer
      anchor={session.drawerPosition ?? 'right'}
      open={Boolean(widget)}
      onClose={() => {
        if (session.visibleWidget) {
          session.hideWidget(session.visibleWidget)
        }
      }}
    >
      <div style={{ width: session.drawerWidth ?? 384 }}>
        {widget && session.renderWidget ? session.renderWidget(widget) : null}
      </div>
    </Drawer>
  )
})

export default DrawerWidget
