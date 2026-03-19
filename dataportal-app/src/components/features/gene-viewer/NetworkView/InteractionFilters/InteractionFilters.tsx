import React from 'react';
import type { NetworkLimitMode, SpeciesScope } from '../../../../../hooks/useNetworkData';
import type { PPIDataSource } from '../../../../../interfaces/PPI';
import {
  NETWORK_VIEW_CONSTANTS,
  STRING_NETWORK_TYPES,
  STRING_EVIDENCE_CHANNELS,
  EVIDENCE_DISPLAY_LABELS,
  type StringNetworkType,
  type StringEvidenceChannel,
} from '../constants';
import styles from './InteractionFilters.module.scss';

const SLIDER = NETWORK_VIEW_CONSTANTS.SLIDER;
const STRING_SCORE = NETWORK_VIEW_CONSTANTS.STRING_REQUIRED_SCORE;

interface InteractionFiltersProps {
  dataSource: PPIDataSource;
  scoreType: string;
  displayThreshold: number;
  limitMode: NetworkLimitMode;
  topN: number;
  speciesScope: SpeciesScope;
  showOrthologs: boolean;
  stringNetworkType: StringNetworkType;
  stringRequiredScore: number;
  stringEvidenceChannels: StringEvidenceChannel[];
  availableScoreTypes: string[];
  onDataSourceChange: (source: PPIDataSource) => void;
  onStringRequiredScoreChange?: (score: number) => void;
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

export const InteractionFilters: React.FC<InteractionFiltersProps> = ({
  dataSource,
  scoreType,
  displayThreshold,
  limitMode,
  topN,
  speciesScope,
  showOrthologs,
  stringNetworkType,
  stringRequiredScore,
  stringEvidenceChannels,
  availableScoreTypes,
  onDataSourceChange,
  onStringRequiredScoreChange,
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
    <div className={styles.interactionFilters}>
      <div className={styles.header}>
        <h3 className={styles.title}>Interaction Filters</h3>
        {onResetView && (
          <button
            onClick={onResetView}
            className={styles.resetButton}
            title="Reset view to fit all nodes"
          >
            Reset
          </button>
        )}
      </div>

      <div className={styles.filterList}>
        {/* Source */}
        <div className={styles.filterItem}>
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

        {/* Interaction Type (STRING type) - only when STRING selected */}
        {showStringNetworkType && (
          <div className={styles.filterItem}>
            <label htmlFor="string-network-type" className={styles.filterLabel}>Interaction Type</label>
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

        {/* STRING confidence - only when STRING selected */}
        {showStringControls && !!onStringRequiredScoreChange && (
          <div className={styles.filterItem}>
            <label
              htmlFor="string-required-score"
              className={styles.filterLabel}
              title="Minimum interaction confidence (0–1000). Higher = stricter filtering."
            >
              STRING confidence
            </label>
            <div className={styles.sliderWrap}>
              <span
                className={styles.valueBox}
                style={{
                  left: `${((stringRequiredScore - STRING_SCORE.MIN) / (STRING_SCORE.MAX - STRING_SCORE.MIN)) * 100}%`,
                  transform: 'translateX(-50%)',
                }}
              >
                {stringRequiredScore}
              </span>
              <input
                id="string-required-score"
                type="range"
                min={STRING_SCORE.MIN}
                max={STRING_SCORE.MAX}
                step={STRING_SCORE.STEP}
                value={stringRequiredScore}
                onChange={(e) => onStringRequiredScoreChange(parseInt(e.target.value, 10))}
                className={styles.slider}
                style={{
                  ['--slider-fill' as string]: `${((stringRequiredScore - STRING_SCORE.MIN) / (STRING_SCORE.MAX - STRING_SCORE.MIN)) * 100}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Score */}
        <div className={styles.filterItem}>
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

        {/* Limit by */}
        <div className={styles.filterItem}>
          <label htmlFor="limit-mode" className={styles.filterLabel}>Limit by</label>
          <select
            id="limit-mode"
            value={limitMode}
            onChange={(e) => onLimitModeChange(e.target.value as NetworkLimitMode)}
            className={styles.select}
          >
            <option value="topN">Top n interactors</option>
            <option value="threshold">Score Threshold</option>
          </select>
        </div>

        {/* Top interactors / Min score slider */}
        <div className={styles.filterItem}>
          <label
            htmlFor={limitMode === 'topN' ? 'top-n' : 'threshold'}
            className={styles.filterLabel}
            title={limitMode === 'topN' ? 'Number of top interactions to display' : 'Minimum score threshold'}
          >
            {limitMode === 'topN' ? 'Top interactors' : 'Min score'}
          </label>
          <div className={styles.sliderWrap}>
            <span
              className={styles.valueBox}
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
        </div>

        {/* Interactors */}
        <div className={styles.filterItem}>
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

        {/* Refinement: Show orthologs */}
        <div className={styles.filterItem}>
          <span className={styles.filterLabel}>Refinement</span>
          <label className={styles.checkboxWrap}>
            <input
              type="checkbox"
              checked={showOrthologs}
              onChange={(e) => onOrthologToggle(e.target.checked)}
              className={styles.checkbox}
            />
            Show orthologs
          </label>
        </div>

        {/* Evidence Channels - when STRING selected */}
        {showStringEvidence && (
          <div className={styles.filterItem}>
            <span className={styles.filterLabel}>Evidence Channels</span>
            <div className={styles.evidenceList}>
              {STRING_EVIDENCE_CHANNELS.map(({ value, label }) => (
                <label key={value} className={styles.evidenceItem}>
                  <input
                    type="checkbox"
                    checked={stringEvidenceChannels.includes(value)}
                    onChange={(e) => handleEvidenceToggle(value, e.target.checked)}
                    className={styles.checkbox}
                  />
                  <span
                    className={styles.evidenceSwatch}
                    data-channel={value}
                    title={label}
                  />
                  {EVIDENCE_DISPLAY_LABELS[value] ?? label}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
