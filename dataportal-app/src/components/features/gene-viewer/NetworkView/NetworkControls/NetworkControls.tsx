import React from 'react';
import type { NetworkLimitMode, SpeciesScope } from '../../../../../hooks/useNetworkData';
import type { PPIDataSource } from '../../../../../interfaces/PPI';
import { NETWORK_VIEW_CONSTANTS, STRING_NETWORK_TYPES, type StringNetworkType } from '../constants';
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
  availableScoreTypes: string[];
  onDataSourceChange: (source: PPIDataSource) => void;
  onScoreTypeChange: (scoreType: string) => void;
  onThresholdChange: (threshold: number) => void;
  onLimitModeChange: (mode: NetworkLimitMode) => void;
  onTopNChange: (n: number) => void;
  onSpeciesScopeChange: (scope: SpeciesScope) => void;
  onOrthologToggle: (enabled: boolean) => void;
  onStringNetworkTypeChange?: (networkType: StringNetworkType) => void;
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
  availableScoreTypes,
  onDataSourceChange,
  onScoreTypeChange,
  onThresholdChange,
  onLimitModeChange,
  onTopNChange,
  onSpeciesScopeChange,
  onOrthologToggle,
  onStringNetworkTypeChange,
  onResetView,
}) => {
  const showStringNetworkType = (dataSource === 'stringdb' || dataSource === 'both') && !!onStringNetworkTypeChange;

  return (
    <div className={styles.networkControls}>
      {/* Row 1: all labels – same baseline */}
      <label htmlFor="data-source" className={styles.rowLabel}>Source:</label>
      <label htmlFor="score-type" className={styles.rowLabel}>Score:</label>
      {showStringNetworkType && (
        <label htmlFor="string-network-type" className={styles.rowLabel}>STRING type:</label>
      )}
      <label htmlFor="limit-mode" className={styles.rowLabel}>Limit by:</label>
      <label htmlFor={limitMode === 'topN' ? 'top-n' : 'threshold'} className={styles.rowLabel}>
        {limitMode === 'topN' ? 'Number of top interactions to display' : 'Min score'}
      </label>
      <label htmlFor="species-scope" className={`${styles.rowLabel} ${styles.groupStart}`}>Interactors:</label>
      <span className={styles.rowLabel}>Show Orthologs</span>
      <span className={styles.rowLabelSpacer} />

      {/* Row 2: all controls – same baseline */}
      <div className={styles.controlCell}>
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
      <div className={styles.controlCell}>
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
        <div className={styles.controlCell}>
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
      <div className={styles.controlCell}>
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

      {/* Slider column: track on row 2, ticks/labels on rows 3–4 */}
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

      <div className={`${styles.controlCell} ${styles.groupStart}`}>
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
      <div className={styles.controlCell}>
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
        <div className={styles.controlCell}>
          <button onClick={onResetView} className={styles.resetButton} title="Reset view to fit all nodes">
            🔍 Reset View
          </button>
        </div>
      )}
    </div>
  );
};

