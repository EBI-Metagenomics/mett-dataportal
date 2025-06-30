import React from 'react';
import { GenomeMeta } from '../../../../interfaces/Genome';
import GeneViewerLegends from '@components/molecules/GeneViewerLegends';
import styles from './GeneViewerHeader.module.scss';

interface GeneViewerHeaderProps {
  genomeMeta: GenomeMeta | null;
}

const GeneViewerHeader: React.FC<GeneViewerHeaderProps> = ({ genomeMeta }) => {
  return (
    <>
      {/* Breadcrumb Section */}
      <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
        <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
          <li className={styles.breadcrumbsItem}>
            <a href="/" className="vf-breadcrumbs__link">Home</a>
          </li>
          <span className={styles.separator}> | </span>
          <li className={styles.breadcrumbsItem}>
            <b>Genome View</b>
          </li>
        </ul>
      </nav>

      {/* Genome Metadata Section */}
      <section className={styles.infoSection}>
        <div className={styles.infoGrid}>
          {/* Left pane: Genome metadata */}
          <div className={styles.leftPane}>
            {genomeMeta ? (
              <div className="genome-meta-info">
                <h2><i>{genomeMeta.species_scientific_name}</i>: {genomeMeta.isolate_name}</h2>
                <p><strong>Assembly Name:&nbsp;</strong>
                  <a href={genomeMeta.fasta_url} target="_blank" rel="noopener noreferrer">
                    {genomeMeta.assembly_name}
                    <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                          style={{paddingLeft: '5px'}}></span>
                  </a>
                </p>
                <p><strong>Annotations:&nbsp;</strong>
                  <a href={genomeMeta.gff_url} target="_blank" rel="noopener noreferrer">
                    {genomeMeta.gff_file}
                    <span className={`icon icon-common icon-download ${styles.iconBlack}`}
                          style={{paddingLeft: '5px'}}></span>
                  </a>
                </p>
              </div>
            ) : (
              <p>Loading genome meta information...</p>
            )}
          </div>
          
          {/* Right pane: Legend */}
          <div className={styles.rightPane}>
            {genomeMeta && (
              <GeneViewerLegends showEssentiality={genomeMeta.type_strain === true}/>
            )}
          </div>
        </div>
      </section>
    </>
  );
};

export default GeneViewerHeader; 