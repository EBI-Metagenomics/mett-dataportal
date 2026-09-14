import React from 'react';
import {RELEASE_SELECTOR_ENABLED} from '../../../config/featureFlags';
import {useMettRelease} from '../../../hooks/useMettRelease';
import styles from './ReleaseSelector.module.scss';

const ReleaseSelector: React.FC = () => {
    const {selected, setSelected, catalog, loading} = useMettRelease();

    if (!RELEASE_SELECTOR_ENABLED || loading) {
        return null;
    }

    const currentLabel = catalog?.current_version
        ? `${catalog.current_version} — Current`
        : 'Current';
    const archived = catalog?.releases.filter((release) => !release.is_current) ?? [];
    const selectValue = selected === catalog?.current_version ? 'current' : selected;

    return (
        <div className={styles.selector} data-testid="mett-release-selector">
            <label className={styles.label} htmlFor="mett-release">
                Data Release
            </label>
            <select
                id="mett-release"
                className={styles.select}
                value={selectValue}
                onChange={(event) => setSelected(event.target.value)}
                aria-label="METT data release"
            >
                <option value="current">{currentLabel}</option>
                {archived.map((release) => (
                    <option key={release.version} value={release.version}>
                        {release.version} — {release.status}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default ReleaseSelector;
