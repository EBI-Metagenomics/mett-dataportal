import React from 'react'
import { observer } from 'mobx-react'
import { Drawer, IconButton } from '@mui/material'
import BaseFeatureWidgetModel  from '@jbrowse/plugin-linear-genome-view'
import CloseIcon from '@mui/icons-material/Close'

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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', borderBottom: '1px solid #eee' }}>
          <span style={{ fontWeight: 600 }}>Feature Details</span>
          <IconButton
            aria-label="close"
            size="small"
            onClick={() => {
              if (session.visibleWidget) {
                session.hideWidget(session.visibleWidget)
              }
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </div>
        <div>
          {widget && session.renderWidget ? session.renderWidget(widget) : null}
        </div>
      </div>
    </Drawer>
  )
})

export default DrawerWidget
