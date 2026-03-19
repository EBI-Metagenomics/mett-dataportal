import React from 'react';
import type { NetworkLimitMode, SpeciesScope } from '../../../../../hooks/useNetworkData';
import type { PPIDataSource } from '../../../../../interfaces/PPI';
import {
  NETWORK_VIEW_CONSTANTS,
  STRING_NETWORK_TYPES,
  STRING_EVIDENCE_CHANNELS,
  STRING_EVIDENCE_COLORS,
  type StringNetworkType,
  type StringEvidenceChannel,
} from '../constants';
import styles from './NetworkControls.module.scss';

const SLIDER = NETWORK_VIEW_CONSTANTS.SLIDER;

interface NetworkControlsProps {
  dataSource: PPIDataSource;
  scoreType: string;
  displayThreshold: number;
  limitMode: NetworkLimitMode;
  topN: number;
  speciesScope: SpeciesScope;
  showOrthologs: boolean;
  stringNetworkType: StringNetworkType;
  stringEvidenceChannels: StringEvidenceChannel[];
  availableScoreTypes: string[];
  onDataSourceChange: (source: PPIDataSource) => void;
  onScoreTypeChange: (scoreType: string) => void;
  onThresholdChange: (threshold: number) => void;
  onLimitModeChange: (mode: NetworkLimitMode) => void;
  onTopNChange: (n: number) => void;
  onSpeciesScopeChange: (scope: SpeciesScope) => void;
  onOrthologToggle: (enabled: boolean) => void;
  onStringNetworkTypeChange?: (networkType: StringNetworkType) => void;
  onStringEvidenceChannelsChange?: (channels: StringEvidenceChannel[]) => void;
  onResetView?: () => void;
}

export const NetworkControls: React.FC<NetworkControlsProps> = ({
  dataSource,
  scoreType,
  displayThreshold,
  limitMode,
  topN,
  speciesScope,
  showOrthologs,
  stringNetworkType,
  stringEvidenceChannels,
  availableScoreTypes,
  onDataSourceChange,
  onScoreTypeChange,
  onThresholdChange,
  onLimitModeChange,
  onTopNChange,
  onSpeciesScopeChange,
  onOrthologToggle,
  onStringNetworkTypeChange,
  onStringEvidenceChannelsChange,
  onResetView,
}) => {
  const showStringControls = (dataSource === 'stringdb' || dataSource === 'both');
  const showStringNetworkType = showStringControls && !!onStringNetworkTypeChange;
  const showStringEvidence = showStringControls && !!onStringEvidenceChannelsChange;

  const handleEvidenceToggle = (channel: StringEvidenceChannel, checked: boolean) => {
    if (!onStringEvidenceChannelsChange) return;
    const next = checked
      ? [...stringEvidenceChannels, channel]
      : stringEvidenceChannels.filter((c) => c !== channel);
    onStringEvidenceChannelsChange(next);
  };

  return (
    <div className={styles.networkControls}>
      {/* Row 1: Source & scoring */}
      <div className={styles.filterRow}>
        <div className={styles.filterGroup}>
          <label htmlFor="data-source" className={styles.filterLabel}>Source</label>
          <select
            id="data-source"
            value={dataSource}
            onChange={(e) => onDataSourceChange(e.target.value as PPIDataSource)}
            className={styles.select}
          >
            <option value="local">Local (ES)</option>
            <option value="stringdb">STRING DB</option>
            <option value="both">Local (ES) + STRING DB</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label htmlFor="score-type" className={styles.filterLabel}>Score</label>
          <select
            id="score-type"
            value={scoreType}
            onChange={(e) => onScoreTypeChange(e.target.value)}
            className={styles.select}
          >
            {availableScoreTypes.map((type) => (
              <option key={type} value={type}>
                {type.replace('_score', '').replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        {showStringNetworkType && (
          <div className={styles.filterGroup}>
            <label htmlFor="string-network-type" className={styles.filterLabel}>STRING type</label>
            <select
              id="string-network-type"
              value={stringNetworkType}
              onChange={(e) => onStringNetworkTypeChange?.(e.target.value as StringNetworkType)}
              className={styles.select}
              title="Physical: direct interactions. Functional: physical + indirect associations."
            >
              {STRING_NETWORK_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Row 2: Limits (Limit by, slider, Interactors) */}
      <div className={styles.filterRow}>
        <div className={styles.filterGroup}>
          <label htmlFor="limit-mode" className={styles.filterLabel}>Limit by</label>
          <select
            id="limit-mode"
            value={limitMode}
            onChange={(e) => onLimitModeChange(e.target.value as NetworkLimitMode)}
            className={styles.select}
          >
            <option value="topN">Top n Interactors</option>
            <option value="threshold">Score Threshold</option>
          </select>
        </div>
        <div className={`${styles.filterGroup} ${styles.sliderGroup}`}>
          <label htmlFor={limitMode === 'topN' ? 'top-n' : 'threshold'} className={styles.filterLabel} title={limitMode === 'topN' ? 'Number of top interactions to display' : 'Minimum score threshold'}>
            {limitMode === 'topN' ? 'Top N' : 'Min score'}
          </label>
          <div className={styles.sliderColumn}>
            <div className={styles.sliderTrackWrap}>
              <span
                className={styles.valueBoxCurrent}
                style={{
                  left: limitMode === 'topN'
                    ? `${((topN - SLIDER.TOP_N_MIN) / (SLIDER.TOP_N_MAX - SLIDER.TOP_N_MIN)) * 100}%`
                    : `${displayThreshold * 100}%`,
                  transform: 'translateX(-50%)',
                }}
              >
                {limitMode === 'topN' ? topN : displayThreshold.toFixed(2)}
              </span>
              {limitMode === 'topN' ? (
                <input
                  id="top-n"
                  type="range"
                  min={SLIDER.TOP_N_MIN}
                  max={SLIDER.TOP_N_MAX}
                  step="1"
                  value={topN}
                  onChange={(e) => onTopNChange(parseInt(e.target.value, 10))}
                  className={styles.slider}
                  style={{ ['--slider-fill' as string]: `${((topN - SLIDER.TOP_N_MIN) / (SLIDER.TOP_N_MAX - SLIDER.TOP_N_MIN)) * 100}%` }}
                />
              ) : (
                <input
                  id="threshold"
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={displayThreshold}
                  onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
                  className={styles.slider}
                  style={{ ['--slider-fill' as string]: `${displayThreshold * 100}%` }}
                />
              )}
            </div>
            <div className={styles.tickMarks}>
              {limitMode === 'topN'
                ? SLIDER.TOP_N_TICK_VALUES.map((n: number) => (
                    <span key={n} className={styles.tick} style={{ left: `${((n - SLIDER.TOP_N_MIN) / (SLIDER.TOP_N_MAX - SLIDER.TOP_N_MIN)) * 100}%` }} />
                  ))
                : SLIDER.THRESHOLD_TICK_VALUES.map((v: number) => (
                    <span key={v} className={styles.tick} style={{ left: `${v * 100}%` }} />
                  ))}
            </div>
            <div className={styles.tickLabels}>
              {limitMode === 'topN'
                ? SLIDER.TOP_N_TICK_VALUES.map((n: number) => (
                    <span key={n} className={styles.tickLabel} style={{ left: `${((n - SLIDER.TOP_N_MIN) / (SLIDER.TOP_N_MAX - SLIDER.TOP_N_MIN)) * 100}%` }}>
                      {n}
                    </span>
                  ))
                : SLIDER.THRESHOLD_TICK_VALUES.map((v: number) => (
                    <span key={v} className={styles.tickLabel} style={{ left: `${v * 100}%` }}>
                      {v === 0 ? '0' : v === 1 ? '1' : v.toFixed(2)}
                    </span>
                  ))}
            </div>
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label htmlFor="species-scope" className={styles.filterLabel}>Interactors</label>
          <select
            id="species-scope"
            value={speciesScope}
            onChange={(e) => onSpeciesScopeChange(e.target.value as SpeciesScope)}
            className={styles.select}
            disabled
            title="Coming soon"
          >
            <option value="current">Current species only</option>
            <option value="all">All species</option>
          </select>
        </div>
      </div>

      {/* Row 3: Actions */}
      <div className={styles.filterRow}>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Display</label>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={showOrthologs}
              onChange={(e) => onOrthologToggle(e.target.checked)}
              className={styles.checkbox}
            />
            Show Orthologs
          </label>
        </div>
        {onResetView && (
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>&nbsp;</label>
            <button onClick={onResetView} className={styles.resetButton} title="Reset view to fit all nodes">
              🔍 Reset View
            </button>
          </div>
        )}
      </div>

      {/* STRING evidence channel filters – color swatch on each checkbox (no separate legend row) */}
      {showStringEvidence && (
        <div className={styles.evidenceRow}>
          <span className={styles.evidenceLabel}>STRING evidence</span>
          <div className={styles.evidenceCheckboxes}>
            {STRING_EVIDENCE_CHANNELS.map(({ value, label }) => (
              <label key={value} className={styles.evidenceCheckbox}>
                <input
                  type="checkbox"
                  checked={stringEvidenceChannels.includes(value)}
                  onChange={(e) => handleEvidenceToggle(value, e.target.checked)}
                  className={styles.checkbox}
                />
                <span
                  className={styles.evidenceColorSwatch}
                  style={{ backgroundColor: STRING_EVIDENCE_COLORS[value] }}
                  title={label}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

