import React from 'react';
import type { NetworkLimitMode, SpeciesScope } from '../../../../hooks/useNetworkData';
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

const TOP_N_MIN = 5;
const TOP_N_MAX = 50;

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
      {/* 1. Score – first */}
      <div className={styles.controlGroup}>
        <label htmlFor="score-type">Score:</label>
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

      {/* 2. Limit by */}
      <div className={styles.controlGroup}>
        <label htmlFor="limit-mode">Limit by:</label>
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

      {/* 3. One slider only – Top N or Min score */}
      {limitMode === 'topN' ? (
        <div className={styles.controlGroup}>
          <label htmlFor="top-n">Top N: {topN}</label>
          <div className={styles.sliderWithScale}>
            <span className={styles.scaleLabel}>{TOP_N_MIN}</span>
            <input
              id="top-n"
              type="range"
              min={TOP_N_MIN}
              max={TOP_N_MAX}
              step="1"
              value={topN}
              onChange={(e) => onTopNChange(parseInt(e.target.value, 10))}
              className={styles.slider}
            />
            <span className={styles.scaleLabel}>{TOP_N_MAX}</span>
          </div>
        </div>
      ) : (
        <div className={styles.controlGroup}>
          <label htmlFor="threshold">Min score: {displayThreshold.toFixed(2)}</label>
          <div className={styles.sliderWithScale}>
            <span className={styles.scaleLabel}>0</span>
            <input
              id="threshold"
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={displayThreshold}
              onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
              className={styles.slider}
            />
            <span className={styles.scaleLabel}>1</span>
          </div>
        </div>
      )}

      {/* 4. Interactors – disabled for now */}
      <div className={styles.controlGroup}>
        <label htmlFor="species-scope">Interactors:</label>
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

      <div className={styles.controlGroup}>
        <label>
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
        <button onClick={onResetView} className={styles.resetButton} title="Reset view to fit all nodes">
          🔍 Reset View
        </button>
      )}
    </div>
  );
};

