import React from 'react';
import styles from './NetworkControls.module.scss';

interface NetworkControlsProps {
  scoreType: string;
  displayThreshold: number;
  showOrthologs: boolean;
  availableScoreTypes: string[];
  onScoreTypeChange: (scoreType: string) => void;
  onThresholdChange: (threshold: number) => void;
  onOrthologToggle: (enabled: boolean) => void;
  onRefresh: () => void;
  onResetView?: () => void;
}

export const NetworkControls: React.FC<NetworkControlsProps> = ({
  scoreType,
  displayThreshold,
  showOrthologs,
  availableScoreTypes,
  onScoreTypeChange,
  onThresholdChange,
  onOrthologToggle,
  onRefresh,
  onResetView,
}) => {
  return (
    <div className={styles.networkControls}>
      <div className={styles.controlGroup}>
        <label htmlFor="score-type">Score Type:</label>
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

      <div className={styles.controlGroup}>
        <label htmlFor="threshold">
          Threshold: {displayThreshold.toFixed(2)}
        </label>
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

      <button onClick={onRefresh} className={styles.analyzeButton}>
        Analyse
      </button>
      
      {onResetView && (
        <button onClick={onResetView} className={styles.resetButton} title="Reset view to fit all nodes">
          🔍 Reset View
        </button>
      )}
    </div>
  );
};

