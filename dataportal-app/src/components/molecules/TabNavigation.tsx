import React from 'react';

interface TabNavigationProps {
  tabs: { id: string, label: string }[];
  onTabClick: (id: string) => void;
  activeTab: string;
}

const TabNavigation: React.FC<TabNavigationProps> = ({ tabs, onTabClick, activeTab }) => {
  return (
    <div className="vf-tabs">
      <ul className="vf-tabs__list" data-vf-js-tabs>
        {tabs.map(tab => (
          <li key={tab.id} className="vf-tabs__item">
            <a className={`vf-tabs__link ${activeTab === tab.id ? 'active' : ''}`} href={`#${tab.id}`} onClick={() => onTabClick(tab.id)}>
              {tab.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TabNavigation;
