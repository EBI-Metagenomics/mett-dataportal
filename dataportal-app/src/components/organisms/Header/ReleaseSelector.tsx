import React from 'react';
import {useMettRelease} from '../../../hooks/useMettRelease';
import styles from './ReleaseSelector.module.scss';

const ReleaseSelector: React.FC = () => {
    const {selected, setSelected, catalog, loading} = useMettRelease();

    if (loading || !catalog || catalog.releases.length === 0) {
        return null;
    }

    const currentLabel = catalog.current_version
        ? `Current (${catalog.current_version})`
        : 'Current';

    return (
        <div className={styles.selector} data-testid="mett-release-selector">
            <label className="vf-form__label" htmlFor="mett-release">
                Data release
            </label>
            <select
                id="mett-release"
                className="vf-form__select"
                value={selected}
                onChange={(event) => setSelected(event.target.value)}
                aria-label="METT data release"
            >
                <option value="current">{currentLabel}</option>
                {catalog.releases.map((release) => (
                    <option key={release.version} value={release.version}>
                        {release.version} — {release.status}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default ReleaseSelector;
