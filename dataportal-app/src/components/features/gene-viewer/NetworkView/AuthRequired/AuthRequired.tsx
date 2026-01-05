import React, { useState } from 'react';
import TokenInput from '../../../../shared/TokenInput/TokenInput';
import styles from './AuthRequired.module.scss';

export const AuthRequired: React.FC = () => {
  const [showTokenInput, setShowTokenInput] = useState<boolean>(false);

  return (
    <>
      <div className={styles.networkViewAuthRequired}>
        <div className={styles.authMessage}>
          <div className={styles.authIcon}>🔒</div>
          <div className={styles.authContent}>
            <h3>Authentication Required</h3>
            <p>
              A JWT token is required to access network data (PPI interactions and orthologs).
              This is a temporary requirement that will be removed once data stabilizes (2-3 months).
            </p>
            <button
              className={styles.authButton}
              onClick={() => setShowTokenInput(true)}
            >
              Set Authentication Token
            </button>
          </div>
        </div>
      </div>

      {showTokenInput && (
        <div className={styles.modalOverlay} onClick={() => setShowTokenInput(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button
              className={styles.closeButton}
              onClick={() => setShowTokenInput(false)}
              aria-label="Close"
            >
              ×
            </button>
            <TokenInput
              onClose={() => setShowTokenInput(false)}
              onTokenSet={() => setShowTokenInput(false)}
            />
          </div>
        </div>
      )}
    </>
  );
};

