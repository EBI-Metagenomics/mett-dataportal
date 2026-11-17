import React, { useState } from 'react';
import { GENE_SET_MAX, GENE_SET_MIN } from './geneSetRules';
import { GeneSetPaths } from './useGeneSetPaths';
import styles from './GeneSetPanel.module.scss';

interface GeneSetPanelProps {
  geneSet: GeneSetPaths;
}

export const GeneSetPanel: React.FC<GeneSetPanelProps> = ({ geneSet }) => {
  const [draft, setDraft] = useState('');
  const atCap = geneSet.genes.length >= GENE_SET_MAX;

  const addDraft = () => {
    geneSet.addGene(draft);
    setDraft('');
  };

  return (
    <section className={styles.panel}>
      <h3 className={styles.title}>Genes of interest</h3>
      <p className={styles.hint}>
        Choose {GENE_SET_MIN}–{GENE_SET_MAX} genes. Find paths uses METT interactions and the same score filter as this network. A path may pass through one intermediate gene.
      </p>
      {geneSet.genes.length > 0 && (
        <ul className={styles.chips}>
          {geneSet.genes.map((tag) => (
            <li key={tag} className={styles.chip}>
              <span>{tag}</span>
              <button type="button" onClick={() => geneSet.removeGene(tag)} aria-label={`Remove ${tag}`}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className={styles.addRow}>
        <input
          type="text"
          value={draft}
          placeholder="Locus tag"
          disabled={atCap}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              addDraft();
            }
          }}
        />
        <button type="button" onClick={addDraft} disabled={atCap || !draft.trim()}>
          Add
        </button>
      </div>
      <button
        type="button"
        className={styles.findButton}
        disabled={!geneSet.canSearch}
        onClick={() => {
          void geneSet.findPaths();
        }}
      >
        {geneSet.searching ? 'Searching…' : 'Find paths'}
      </button>
      {geneSet.error && <p className={styles.error}>{geneSet.error}</p>}
      {geneSet.notice && (
        <div className={styles.notice}>
          <p>{geneSet.notice}</p>
          <button type="button" onClick={geneSet.dismissNotice}>
            Dismiss
          </button>
        </div>
      )}
      {geneSet.pathGraph && (
        <div className={styles.pathActions}>
          <button type="button" className={styles.backButton} onClick={geneSet.backToNetwork}>
            Back to network
          </button>
          {geneSet.disconnected.length > 0 && (
            <p className={styles.partial}>
              No path within two steps: {geneSet.disconnected.join('; ')}
            </p>
          )}
          <p className={styles.legend}>
            <span className={styles.seedSwatch} /> Anchor
            <span className={styles.intermediateSwatch} /> Other genes
          </p>
        </div>
      )}
    </section>
  );
};
