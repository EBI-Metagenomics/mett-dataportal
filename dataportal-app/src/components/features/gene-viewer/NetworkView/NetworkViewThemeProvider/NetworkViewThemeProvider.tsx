import React, { useMemo } from 'react';
import { NETWORK_VIEW_CONSTANTS, STRING_EVIDENCE_COLORS, type StringEvidenceChannel } from '../constants';
import styles from './NetworkViewThemeProvider.module.scss';

interface NetworkViewThemeProviderProps {
  children: React.ReactNode;
}

/**
 * Injects CSS custom properties from constants so components can use them in SCSS
 * without hardcoding colors in TypeScript. Single source of truth: constants.ts
 */
export const NetworkViewThemeProvider: React.FC<NetworkViewThemeProviderProps> = ({ children }) => {
  const styleVars = useMemo(() => {
    const GT = NETWORK_VIEW_CONSTANTS.GRAPH_THEME;
    const vars: Record<string, string> = {
      '--network-edge-local': GT.EDGE.LOCAL_EDGE_COLOR,
      '--network-edge-stringdb': GT.EDGE.STRINGDB_EDGE_COLOR,
    };
    (Object.keys(STRING_EVIDENCE_COLORS) as StringEvidenceChannel[]).forEach((channel) => {
      vars[`--network-evidence-${channel}`] = STRING_EVIDENCE_COLORS[channel];
    });
    return vars as React.CSSProperties;
  }, []);

  return (
    <div className={styles.themeRoot} style={styleVars}>
      {children}
    </div>
  );
};
