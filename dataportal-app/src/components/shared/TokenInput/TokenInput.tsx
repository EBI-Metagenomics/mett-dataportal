import React, { useState, useCallback } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import styles from './TokenInput.module.scss';

interface TokenInputProps {
  onClose?: () => void;
  onTokenSet?: () => void;
}

/**
 * Token Input Component - Temporary authentication token management
 * This component allows users to set a JWT token for accessing experimental/interaction endpoints.
 * This is a temporary feature that will be removed once data stabilizes (2-3 months).
 */
const TokenInput: React.FC<TokenInputProps> = ({ onClose, onTokenSet }) => {
  const { token, setAuthToken, clearAuthToken } = useAuth();
  const [inputToken, setInputToken] = useState<string>(token || '');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (!inputToken.trim()) {
        setError('Please enter a token');
        setIsSubmitting(false);
        return;
      }

      setAuthToken(inputToken.trim());
      if (onTokenSet) {
        onTokenSet();
      }
      if (onClose) {
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set token');
    } finally {
      setIsSubmitting(false);
    }
  }, [inputToken, setAuthToken, onClose, onTokenSet]);

  const handleClear = useCallback(() => {
    clearAuthToken();
    setInputToken('');
    setError(null);
    if (onClose) {
      onClose();
    }
  }, [clearAuthToken, onClose]);

  const handleCancel = useCallback(() => {
    setInputToken(token || '');
    setError(null);
    if (onClose) {
      onClose();
    }
  }, [token, onClose]);

  return (
    <div className={styles.tokenInput}>
      <div className={styles.header}>
        <h3>Authentication Token</h3>
        <p className={styles.subtitle}>
          Required for accessing experimental and interaction endpoints (PPI, Orthologs).
          <br />
          <span className={styles.temporary}>This is a temporary feature and will be removed in 2-3 months.</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputGroup}>
          <label htmlFor="token-input">JWT Token</label>
          <input
            id="token-input"
            type="text"
            value={inputToken}
            onChange={(e) => {
              setInputToken(e.target.value);
              setError(null);
            }}
            placeholder="Enter your JWT token"
            className={styles.input}
            disabled={isSubmitting}
          />
          {error && <div className={styles.error}>{error}</div>}
        </div>

        <div className={styles.actions}>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={isSubmitting || !inputToken.trim()}
          >
            {isSubmitting ? 'Setting...' : token ? 'Update Token' : 'Set Token'}
          </button>
          {token && (
            <button
              type="button"
              onClick={handleClear}
              className={styles.clearButton}
              disabled={isSubmitting}
            >
              Clear Token
            </button>
          )}
          {onClose && (
            <button
              type="button"
              onClick={handleCancel}
              className={styles.cancelButton}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {token && (
        <div className={styles.tokenStatus}>
          <span className={styles.statusIcon}>✓</span>
          <span>Token is set</span>
        </div>
      )}
    </div>
  );
};

export default TokenInput;

