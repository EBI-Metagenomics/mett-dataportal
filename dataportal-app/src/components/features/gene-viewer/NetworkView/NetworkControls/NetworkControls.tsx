import React from 'react';
import type { NetworkLimitMode, SpeciesScope } from '../../../../../hooks/useNetworkData';
import styles from './NetworkControls.module.scss';

interface NetworkControlsProps {
  scoreType: string;
  displayThreshold: number;
  limitMode: NetworkLimitMode;
  topN: number;
  speciesScope: SpeciesScope;
  showOrthologs: boolean;
  availableScoreTypes: string[];
  onScoreTypeChange: (scoreType: string) => void;
  onThresholdChange: (threshold: number) => void;
  onLimitModeChange: (mode: NetworkLimitMode) => void;
  onTopNChange: (n: number) => void;
  onSpeciesScopeChange: (scope: SpeciesScope) => void;
  onOrthologToggle: (enabled: boolean) => void;
  onResetView?: () => void;
}

const TOP_N_MIN = 1;
const TOP_N_MAX = 50;
const TOP_N_TICK_VALUES = [1, 10, 20, 30, 40, 50];

const THRESHOLD_TICK_VALUES = [0, 0.25, 0.5, 0.75, 1];

export const NetworkControls: React.FC<NetworkControlsProps> = ({
  scoreType,
  displayThreshold,
  limitMode,
  topN,
  speciesScope,
  showOrthologs,
  availableScoreTypes,
  onScoreTypeChange,
  onThresholdChange,
  onLimitModeChange,
  onTopNChange,
  onSpeciesScopeChange,
  onOrthologToggle,
  onResetView,
}) => {
  return (
    <div className={styles.networkControls}>
      {/* Row 1: all labels – same baseline */}
      <label htmlFor="score-type" className={styles.rowLabel}>Score:</label>
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
                ? `${((topN - TOP_N_MIN) / (TOP_N_MAX - TOP_N_MIN)) * 100}%`
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
              min={TOP_N_MIN}
              max={TOP_N_MAX}
              step="1"
              value={topN}
              onChange={(e) => onTopNChange(parseInt(e.target.value, 10))}
              className={styles.slider}
              style={{ ['--slider-fill' as string]: `${((topN - TOP_N_MIN) / (TOP_N_MAX - TOP_N_MIN)) * 100}%` }}
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
            ? TOP_N_TICK_VALUES.map((n) => (
                <span key={n} className={styles.tick} style={{ left: `${((n - TOP_N_MIN) / (TOP_N_MAX - TOP_N_MIN)) * 100}%` }} />
              ))
            : THRESHOLD_TICK_VALUES.map((v) => (
                <span key={v} className={styles.tick} style={{ left: `${v * 100}%` }} />
              ))}
        </div>
        <div className={styles.tickLabels}>
          {limitMode === 'topN'
            ? TOP_N_TICK_VALUES.map((n) => (
                <span key={n} className={styles.tickLabel} style={{ left: `${((n - TOP_N_MIN) / (TOP_N_MAX - TOP_N_MIN)) * 100}%` }}>
                  {n}
                </span>
              ))
            : THRESHOLD_TICK_VALUES.map((v) => (
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

