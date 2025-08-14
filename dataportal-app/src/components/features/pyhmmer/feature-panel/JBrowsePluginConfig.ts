interface JBrowsePyhmmerConfig {
    // Plugin identification
    name: string;
    version: string;
    description: string;
    
    // Feature panel configuration
    featurePanel: {
        id: string;
        title: string;
        icon: string;
        component: string;
        position: 'left' | 'right' | 'bottom';
        width?: number;
        height?: number;
        collapsible: boolean;
        defaultCollapsed: boolean;
    };
    
    // PyHMMER configuration
    pyhmmer: {
        defaultDatabase: string;
        defaultThreshold: 'evalue' | 'bitscore';
        defaultThresholdValue: string;
        showAdvancedParameters: boolean;
        maxResults: number;
        autoExtractSequence: boolean;
    };
    
    // JBrowse integration settings
    integration: {
        autoHighlightResults: boolean;
        showFeatureContext: boolean;
        enableSequenceExtraction: boolean;
        customStyling: boolean;
    };
}

// Default configuration
export const defaultJBrowsePyhmmerConfig: JBrowsePyhmmerConfig = {
    name: 'PyHMMER Feature Panel',
    version: '1.0.0',
    description: 'Protein domain search using HMMER algorithms integrated with JBrowse',
    
    featurePanel: {
        id: 'pyhmmer-feature-panel',
        title: 'PyHMMER Search',
        icon: '🔍',
        component: 'PyhmmerFeaturePanel',
        position: 'right',
        width: 400,
        height: 600,
        collapsible: true,
        defaultCollapsed: false,
    },
    
    pyhmmer: {
        defaultDatabase: 'bu_all',
        defaultThreshold: 'evalue',
        defaultThresholdValue: '0.01',
        showAdvancedParameters: false,
        maxResults: 50,
        autoExtractSequence: true,
    },
    
    integration: {
        autoHighlightResults: true,
        showFeatureContext: true,
        enableSequenceExtraction: true,
        customStyling: true,
    },
};

// JBrowse plugin manifest
export const jbrowsePluginManifest = {
    name: 'PyHMMER Feature Panel',
    version: '1.0.0',
    description: 'Protein domain search integration for JBrowse',
    author: 'METT Data Portal Team',
    license: 'MIT',
    
    // Plugin entry point
    main: './JBrowsePyhmmerFeaturePanel',
    
    // Dependencies
    peerDependencies: {
        'react': '^18.0.0',
        'react-dom': '^18.0.0',
    },
    
    // JBrowse compatibility
    jbrowse: {
        version: '>=2.0.0',
        plugins: ['@jbrowse/react-linear-genome-view'],
    },
    
    // Feature panel registration
    featurePanels: [
        {
            id: 'pyhmmer-feature-panel',
            title: 'PyHMMER Search',
            icon: '🔍',
            component: 'PyhmmerFeaturePanel',
            position: 'right',
            width: 400,
            height: 600,
            collapsible: true,
            defaultCollapsed: false,
        },
    ],
};

// Usage example for JBrowse configuration
export const jbrowseConfigExample = {
    // Add this to your JBrowse configuration
    plugins: [
        {
            name: 'PyHMMER Feature Panel',
            url: '/path/to/pyhmmer-feature-panel',
        },
    ],
    
    // Feature panel configuration
    featurePanels: [
        {
            id: 'pyhmmer-feature-panel',
            title: 'PyHMMER Search',
            icon: '🔍',
            component: 'PyhmmerFeaturePanel',
            position: 'right',
            width: 400,
            height: 600,
            collapsible: true,
            defaultCollapsed: false,
        },
    ],
    
    // PyHMMER specific settings
    pyhmmer: {
        defaultDatabase: 'bu_all',
        defaultThreshold: 'evalue',
        defaultThresholdValue: '0.01',
        showAdvancedParameters: false,
        maxResults: 50,
        autoExtractSequence: true,
    },
};

// Integration helper functions
export const JBrowseIntegrationHelpers = {
    // Check if running in JBrowse context
    isInJBrowse: (): boolean => {
        return typeof window !== 'undefined' && 
               (window as any).JBrowse || 
               (window as any).jbrowse ||
               document.querySelector('[data-jbrowse]') !== null;
    },
    
    // Get JBrowse session if available
    getJBrowseSession: (): any => {
        if (typeof window !== 'undefined') {
            return (window as any).JBrowse?.session || 
                   (window as any).jbrowse?.session ||
                   (window as any).__JBROWSE_SESSION__;
        }
        return null;
    },
    
    // Get JBrowse model if available
    getJBrowseModel: (): any => {
        const session = JBrowseIntegrationHelpers.getJBrowseSession();
        return session?.model || session?.view?.model;
    },
    
    // Extract feature information from JBrowse context
    extractFeatureInfo: (feature: any): any => {
        if (!feature) return null;
        
        return {
            id: feature.id || feature.name || feature.uniqueID,
            name: feature.name || feature.id || 'Unknown Feature',
            type: feature.type || feature.feature_type || 'Unknown Type',
            start: feature.start || feature.min,
            end: feature.end || feature.max,
            strand: feature.strand || feature.orientation,
            sequence: feature.sequence || feature.seq || feature.translation,
            attributes: feature.attributes || feature.properties || {},
        };
    },
    
    // Register PyHMMER feature panel with JBrowse
    registerFeaturePanel: (jbrowseInstance: any, config: JBrowsePyhmmerConfig): void => {
        try {
            if (jbrowseInstance && jbrowseInstance.registerFeaturePanel) {
                jbrowseInstance.registerFeaturePanel({
                    id: config.featurePanel.id,
                    title: config.featurePanel.title,
                    icon: config.featurePanel.icon,
                    component: config.featurePanel.component,
                    position: config.featurePanel.position,
                    width: config.featurePanel.width,
                    height: config.featurePanel.height,
                    collapsible: config.featurePanel.collapsible,
                    defaultCollapsed: config.featurePanel.defaultCollapsed,
                });
                console.log('PyHMMER feature panel registered with JBrowse');
            }
        } catch (error) {
            console.warn('Could not register PyHMMER feature panel with JBrowse:', error);
        }
    },
};
