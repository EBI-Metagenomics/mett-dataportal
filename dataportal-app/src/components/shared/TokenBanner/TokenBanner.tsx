import React, { useState } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import TokenInput from '../TokenInput/TokenInput';
import styles from './TokenBanner.module.scss';

/**
 * Token Banner Component - Shows authentication token status in header
 * This is a temporary component for managing JWT tokens for experimental endpoints.
 */
const TokenBanner: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [showTokenInput, setShowTokenInput] = useState(false);

  if (isAuthenticated) {
    return null; // Don't show banner if token is set
  }

  return (
    <>
      <div className={styles.banner}>
        <div className={styles.content}>
          <span className={styles.icon}>🔒</span>
          <span className={styles.text}>
            Authentication token required for experimental features (PPI, Orthologs).
          </span>
          <button
            className={styles.linkButton}
            onClick={() => setShowTokenInput(true)}
          >
            Set Token
          </button>
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

export default TokenBanner;

