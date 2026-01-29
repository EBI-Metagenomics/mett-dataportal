import React from 'react'
import styles from './GeneViewerTabNavigation.module.scss'

export interface GeneViewerTab {
  id: string
  label: string
}

interface GeneViewerTabNavigationProps {
  tabs: GeneViewerTab[]
  activeTab: string
  onTabClick: (tabId: string) => void
}

const GeneViewerTabNavigation: React.FC<GeneViewerTabNavigationProps> = ({
  tabs,
  activeTab,
  onTabClick,
}) => (
  <div className={styles.tabsContainer}>
    {tabs.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onTabClick(tab.id)}
        className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
        type="button"
      >
        {tab.label}
      </button>
    ))}
  </div>
)

export default GeneViewerTabNavigation

