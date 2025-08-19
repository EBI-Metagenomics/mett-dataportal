export interface JBrowsePyhmmerConfig {
    // Plugin configuration
    pluginName: string;
    pluginVersion: string;
    pluginDescription: string;

    // Feature panel configuration
    featurePanel: {
        id: string;
        title: string;
        icon: string;
        position: 'left' | 'right' | 'top' | 'bottom';
        width: number;
        height: number;
        collapsible: boolean;
        defaultCollapsed: boolean;
    };

    // PyHMMER configuration
    pyhmmer: {
        defaultDatabase: string;
        defaultThreshold: 'evalue' | 'bitscore';
        showAdvancedParameters: boolean;
        maxResults: number;
        autoSearch: boolean;
    };

    // JBrowse integration
    jbrowse: {
        minVersion: string;
        maxVersion: string;
        requiredPlugins: string[];
        optionalPlugins: string[];
    };
}

// Default configuration
export const defaultJBrowsePyhmmerConfig: JBrowsePyhmmerConfig = {
    pluginName: 'PyHMMER Feature Panel',
    pluginVersion: '1.0.0',
    pluginDescription: 'Protein domain search integration for JBrowse',

    featurePanel: {
        id: 'pyhmmer-feature-panel',
        title: 'PyHMMER Search',
        icon: '🔍',
        position: 'right',
        width: 400,
        height: 600,
        collapsible: true,
        defaultCollapsed: false
    },

    pyhmmer: {
        defaultDatabase: 'bu_all',
        defaultThreshold: 'evalue',
        showAdvancedParameters: false,
        maxResults: 50,
        autoSearch: true
    },

    jbrowse: {
        minVersion: '2.0.0',
        maxVersion: '3.0.0',
        requiredPlugins: ['LinearGenomeViewPlugin'],
        optionalPlugins: ['CircularViewPlugin', 'DotplotViewPlugin']
    }
};

// JBrowse integration helpers
export class JBrowseIntegrationHelpers {
    /**
     * Check if running in JBrowse context
     */
    static isInJBrowse(): boolean {
        return typeof window !== 'undefined' &&
            (window as any).JBrowse !== undefined;
    }

    /**
     * Get JBrowse session if available
     */
    static getJBrowseSession(): any {
        if (this.isInJBrowse()) {
            return (window as any).JBrowse?.session;
        }
        return null;
    }

    /**
     * Get JBrowse model if available
     */
    static getJBrowseModel(): any {
        if (this.isInJBrowse()) {
            return (window as any).JBrowse?.model;
        }
        return null;
    }

    /**
     * Register feature panel with JBrowse
     */
    static registerFeaturePanel(session: any, config: JBrowsePyhmmerConfig): boolean {
        try {
            if (session && session.addFeaturePanel) {
                session.addFeaturePanel(config.featurePanel);
                return true;
            }
            return false;
        } catch (error) {
            console.warn('Failed to register feature panel:', error);
            return false;
        }
    }

    /**
     * Check JBrowse version compatibility
     */
    static checkVersionCompatibility(): boolean {
        if (!this.isInJBrowse()) {
            return false;
        }

        const jbrowseVersion = (window as any).JBrowse?.version;
        if (!jbrowseVersion) {
            return false;
        }

        const version = jbrowseVersion.split('.').map(Number);
        const minVersion = defaultJBrowsePyhmmerConfig.jbrowse.minVersion.split('.').map(Number);

        for (let i = 0; i < Math.min(version.length, minVersion.length); i++) {
            if (version[i] < minVersion[i]) return false;
            if (version[i] > minVersion[i]) return true;
        }

        return version.length >= minVersion.length;
    }
}

// Plugin manifest for JBrowse
export const jbrowsePluginManifest = {
    name: defaultJBrowsePyhmmerConfig.pluginName,
    version: defaultJBrowsePyhmmerConfig.pluginVersion,
    description: defaultJBrowsePyhmmerConfig.pluginDescription,
    main: './PyhmmerIntegration',
    dependencies: {
        '@jbrowse/core': '^2.0.0',
        '@jbrowse/react-linear-genome-view': '^2.0.0'
    },
    peerDependencies: {
        react: '^17.0.0 || ^18.0.0',
        'react-dom': '^17.0.0 || ^18.0.0'
    }
};
