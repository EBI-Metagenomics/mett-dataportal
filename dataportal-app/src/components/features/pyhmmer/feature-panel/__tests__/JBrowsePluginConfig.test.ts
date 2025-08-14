/**
 * JBrowse Plugin Configuration Tests
 * Tests the configuration objects and integration helper functions
 */

import {
    defaultJBrowsePyhmmerConfig,
    jbrowsePluginManifest,
    jbrowseConfigExample,
    JBrowseIntegrationHelpers,
    JBrowsePyhmmerConfig,
} from '../JBrowsePluginConfig';

describe('JBrowse Plugin Configuration', () => {
    describe('defaultJBrowsePyhmmerConfig', () => {
        it('has the correct structure', () => {
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('name');
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('version');
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('description');
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('featurePanel');
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('pyhmmer');
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty('integration');
        });

        it('has correct default values', () => {
            expect(defaultJBrowsePyhmmerConfig.name).toBe('PyHMMER Feature Panel');
            expect(defaultJBrowsePyhmmerConfig.version).toBe('1.0.0');
            expect(defaultJBrowsePyhmmerConfig.description).toContain('Protein domain search');
        });

        it('has correct feature panel configuration', () => {
            const { featurePanel } = defaultJBrowsePyhmmerConfig;
            expect(featurePanel.id).toBe('pyhmmer-feature-panel');
            expect(featurePanel.title).toBe('PyHMMER Search');
            expect(featurePanel.icon).toBe('🔍');
            expect(featurePanel.position).toBe('right');
            expect(featurePanel.collapsible).toBe(true);
            expect(featurePanel.defaultCollapsed).toBe(false);
        });

        it('has correct PyHMMER configuration', () => {
            const { pyhmmer } = defaultJBrowsePyhmmerConfig;
            expect(pyhmmer.defaultDatabase).toBe('bu_all');
            expect(pyhmmer.defaultThreshold).toBe('evalue');
            expect(pyhmmer.defaultThresholdValue).toBe('0.01');
            expect(pyhmmer.showAdvancedParameters).toBe(false);
            expect(pyhmmer.maxResults).toBe(50);
            expect(pyhmmer.autoExtractSequence).toBe(true);
        });

        it('has correct integration settings', () => {
            const { integration } = defaultJBrowsePyhmmerConfig;
            expect(integration.autoHighlightResults).toBe(true);
            expect(integration.showFeatureContext).toBe(true);
            expect(integration.enableSequenceExtraction).toBe(true);
            expect(integration.customStyling).toBe(true);
        });
    });

    describe('jbrowsePluginManifest', () => {
        it('has the correct structure', () => {
            expect(jbrowsePluginManifest).toHaveProperty('name');
            expect(jbrowsePluginManifest).toHaveProperty('version');
            expect(jbrowsePluginManifest).toHaveProperty('description');
            expect(jbrowsePluginManifest).toHaveProperty('author');
            expect(jbrowsePluginManifest).toHaveProperty('license');
            expect(jbrowsePluginManifest).toHaveProperty('main');
            expect(jbrowsePluginManifest).toHaveProperty('peerDependencies');
            expect(jbrowsePluginManifest).toHaveProperty('jbrowse');
            expect(jbrowsePluginManifest).toHaveProperty('featurePanels');
        });

        it('has correct plugin information', () => {
            expect(jbrowsePluginManifest.name).toBe('PyHMMER Feature Panel');
            expect(jbrowsePluginManifest.version).toBe('1.0.0');
            expect(jbrowsePluginManifest.author).toBe('METT Data Portal Team');
            expect(jbrowsePluginManifest.license).toBe('MIT');
        });

        it('has correct dependencies', () => {
            expect(jbrowsePluginManifest.peerDependencies).toHaveProperty('react');
            expect(jbrowsePluginManifest.peerDependencies).toHaveProperty('react-dom');
            expect(jbrowsePluginManifest.peerDependencies.react).toBe('^18.0.0');
            expect(jbrowsePluginManifest.peerDependencies['react-dom']).toBe('^18.0.0');
        });

        it('has correct JBrowse compatibility', () => {
            expect(jbrowsePluginManifest.jbrowse).toHaveProperty('version');
            expect(jbrowsePluginManifest.jbrowse).toHaveProperty('plugins');
            expect(jbrowsePluginManifest.jbrowse.version).toBe('>=2.0.0');
            expect(jbrowsePluginManifest.jbrowse.plugins).toContain('@jbrowse/react-linear-genome-view');
        });

        it('has correct feature panel configuration', () => {
            const featurePanels = jbrowsePluginManifest.featurePanels;
            expect(featurePanels).toHaveLength(1);
            
            const panel = featurePanels[0];
            expect(panel.id).toBe('pyhmmer-feature-panel');
            expect(panel.title).toBe('PyHMMER Search');
            expect(panel.icon).toBe('🔍');
            expect(panel.component).toBe('PyhmmerFeaturePanel');
            expect(panel.position).toBe('right');
            expect(panel.collapsible).toBe(true);
            expect(panel.defaultCollapsed).toBe(false);
        });
    });

    describe('jbrowseConfigExample', () => {
        it('has the correct structure', () => {
            expect(jbrowseConfigExample).toHaveProperty('plugins');
            expect(jbrowseConfigExample).toHaveProperty('featurePanels');
            expect(jbrowseConfigExample).toHaveProperty('pyhmmer');
        });

        it('has correct plugins configuration', () => {
            const plugins = jbrowseConfigExample.plugins;
            expect(plugins).toHaveLength(1);
            expect(plugins[0]).toHaveProperty('name');
            expect(plugins[0]).toHaveProperty('url');
            expect(plugins[0].name).toBe('PyHMMER Feature Panel');
        });

        it('has correct feature panels configuration', () => {
            const featurePanels = jbrowseConfigExample.featurePanels;
            expect(featurePanels).toHaveLength(1);
            
            const panel = featurePanels[0];
            expect(panel.id).toBe('pyhmmer-feature-panel');
            expect(panel.title).toBe('PyHMMER Search');
            expect(panel.icon).toBe('🔍');
            expect(panel.component).toBe('PyhmmerFeaturePanel');
            expect(panel.position).toBe('right');
            expect(panel.collapsible).toBe(true);
            expect(panel.defaultCollapsed).toBe(false);
        });

        it('has correct PyHMMER configuration', () => {
            const pyhmmer = jbrowseConfigExample.pyhmmer;
            expect(pyhmmer.defaultDatabase).toBe('bu_all');
            expect(pyhmmer.defaultThreshold).toBe('evalue');
            expect(pyhmmer.defaultThresholdValue).toBe('0.01');
            expect(pyhmmer.showAdvancedParameters).toBe(false);
            expect(pyhmmer.maxResults).toBe(50);
            expect(pyhmmer.autoExtractSequence).toBe(true);
        });
    });
});

describe('JBrowseIntegrationHelpers', () => {
    let originalWindow: any;

    beforeEach(() => {
        originalWindow = { ...window };
    });

    afterEach(() => {
        window = originalWindow;
    });

    describe('isInJBrowse', () => {
        it('returns false when no JBrowse context is present', () => {
            expect(JBrowseIntegrationHelpers.isInJBrowse()).toBe(false);
        });

        it('returns true when JBrowse is present on window', () => {
            (window as any).JBrowse = { session: {} };
            expect(JBrowseIntegrationHelpers.isInJBrowse()).toBe(true);
        });

        it('returns true when jbrowse is present on window', () => {
            (window as any).jbrowse = { session: {} };
            expect(JBrowseIntegrationHelpers.isInJBrowse()).toBe(true);
        });

        it('returns true when jbrowse data attribute is present', () => {
            // Mock document.querySelector
            const mockQuerySelector = jest.fn().mockReturnValue({});
            Object.defineProperty(document, 'querySelector', {
                value: mockQuerySelector,
                writable: true,
            });
            
            expect(JBrowseIntegrationHelpers.isInJBrowse()).toBe(true);
            expect(mockQuerySelector).toHaveBeenCalledWith('[data-jbrowse]');
        });
    });

    describe('getJBrowseSession', () => {
        it('returns null when no JBrowse context is present', () => {
            expect(JBrowseIntegrationHelpers.getJBrowseSession()).toBe(null);
        });

        it('returns session from JBrowse on window', () => {
            const mockSession = { model: {} };
            (window as any).JBrowse = { session: mockSession };
            expect(JBrowseIntegrationHelpers.getJBrowseSession()).toBe(mockSession);
        });

        it('returns session from jbrowse on window', () => {
            const mockSession = { model: {} };
            (window as any).jbrowse = { session: mockSession };
            expect(JBrowseIntegrationHelpers.getJBrowseSession()).toBe(mockSession);
        });

        it('returns session from __JBROWSE_SESSION__ on window', () => {
            const mockSession = { model: {} };
            (window as any).__JBROWSE_SESSION__ = mockSession;
            expect(JBrowseIntegrationHelpers.getJBrowseSession()).toBe(mockSession);
        });

        it('prioritizes JBrowse over jbrowse', () => {
            const jbrowseSession = { model: {}, priority: 'jbrowse' };
            const jbrowseLowerSession = { model: {}, priority: 'lower' };
            
            (window as any).JBrowse = { session: jbrowseSession };
            (window as any).jbrowse = { session: jbrowseLowerSession };
            
            expect(JBrowseIntegrationHelpers.getJBrowseSession()).toBe(jbrowseSession);
        });
    });

    describe('getJBrowseModel', () => {
        it('returns null when no session is available', () => {
            expect(JBrowseIntegrationHelpers.getJBrowseModel()).toBe(null);
        });

        it('returns model from session', () => {
            const mockModel = { highlightFeature: jest.fn() };
            const mockSession = { model: mockModel };
            (window as any).JBrowse = { session: mockSession };
            
            expect(JBrowseIntegrationHelpers.getJBrowseModel()).toBe(mockModel);
        });

        it('returns model from session.view.model', () => {
            const mockModel = { highlightFeature: jest.fn() };
            const mockSession = { 
                model: null,
                view: { model: mockModel }
            };
            (window as any).JBrowse = { session: mockSession };
            
            expect(JBrowseIntegrationHelpers.getJBrowseModel()).toBe(mockModel);
        });

        it('returns null when neither model path exists', () => {
            const mockSession = { 
                model: null,
                view: { model: null }
            };
            (window as any).JBrowse = { session: mockSession };
            
            expect(JBrowseIntegrationHelpers.getJBrowseModel()).toBe(null);
        });
    });

    describe('extractFeatureInfo', () => {
        it('returns null for null feature', () => {
            expect(JBrowseIntegrationHelpers.extractFeatureInfo(null)).toBe(null);
        });

        it('returns null for undefined feature', () => {
            expect(JBrowseIntegrationHelpers.extractFeatureInfo(undefined)).toBe(null);
        });

        it('extracts basic feature information', () => {
            const feature = {
                id: 'test-id',
                name: 'test-name',
                type: 'test-type',
                start: 1000,
                end: 2000,
                strand: '+',
                sequence: 'ATCG',
                attributes: { product: 'test-product' },
            };

            const result = JBrowseIntegrationHelpers.extractFeatureInfo(feature);
            
            expect(result).toEqual({
                id: 'test-id',
                name: 'test-name',
                type: 'test-type',
                start: 1000,
                end: 2000,
                strand: '+',
                sequence: 'ATCG',
                attributes: { product: 'test-product' },
            });
        });

        it('handles missing optional fields gracefully', () => {
            const feature = {
                id: 'test-id',
                // name is missing
                // type is missing
                start: 1000,
                end: 2000,
                // strand is missing
                // sequence is missing
                // attributes is missing
            };

            const result = JBrowseIntegrationHelpers.extractFeatureInfo(feature);
            
            expect(result).toEqual({
                id: 'test-id',
                name: 'test-id', // falls back to id
                type: 'Unknown Type',
                start: 1000,
                end: 2000,
                strand: undefined,
                sequence: undefined,
                attributes: {},
            });
        });

        it('handles alternative field names', () => {
            const feature = {
                uniqueID: 'test-unique-id',
                feature_type: 'test-feature-type',
                min: 1000,
                max: 2000,
                orientation: '-',
                seq: 'ATCG',
                properties: { product: 'test-product' },
            };

            const result = JBrowseIntegrationHelpers.extractFeatureInfo(feature);
            
            expect(result).toEqual({
                id: 'test-unique-id',
                name: 'test-unique-id',
                type: 'test-feature-type',
                start: 1000,
                end: 2000,
                strand: '-',
                sequence: 'ATCG',
                attributes: { product: 'test-product' },
            });
        });
    });

    describe('registerFeaturePanel', () => {
        it('successfully registers feature panel', () => {
            const mockJBrowseInstance = {
                registerFeaturePanel: jest.fn(),
            };
            
            const config: JBrowsePyhmmerConfig = {
                name: 'Test Panel',
                version: '1.0.0',
                description: 'Test description',
                featurePanel: {
                    id: 'test-panel',
                    title: 'Test Panel',
                    icon: '🔍',
                    component: 'TestComponent',
                    position: 'right',
                    collapsible: true,
                    defaultCollapsed: false,
                },
                pyhmmer: {
                    defaultDatabase: 'test_db',
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

            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            
            JBrowseIntegrationHelpers.registerFeaturePanel(mockJBrowseInstance, config);
            
            expect(mockJBrowseInstance.registerFeaturePanel).toHaveBeenCalledWith({
                id: 'test-panel',
                title: 'Test Panel',
                icon: '🔍',
                component: 'TestComponent',
                position: 'right',
                collapsible: true,
                defaultCollapsed: false,
            });
            
            expect(consoleSpy).toHaveBeenCalledWith('PyHMMER feature panel registered with JBrowse');
            
            consoleSpy.mockRestore();
        });

        it('handles missing registerFeaturePanel method gracefully', () => {
            const mockJBrowseInstance = {};
            const config = defaultJBrowsePyhmmerConfig;
            
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            JBrowseIntegrationHelpers.registerFeaturePanel(mockJBrowseInstance, config);
            
            expect(consoleSpy).toHaveBeenCalledWith(
                'Could not register PyHMMER feature panel with JBrowse:',
                expect.any(Error)
            );
            
            consoleSpy.mockRestore();
        });

        it('handles errors during registration gracefully', () => {
            const mockJBrowseInstance = {
                registerFeaturePanel: jest.fn().mockImplementation(() => {
                    throw new Error('Registration failed');
                }),
            };
            
            const config = defaultJBrowsePyhmmerConfig;
            
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            JBrowseIntegrationHelpers.registerFeaturePanel(mockJBrowseInstance, config);
            
            expect(consoleSpy).toHaveBeenCalledWith(
                'Could not register PyHMMER feature panel with JBrowse:',
                expect.any(Error)
            );
            
            consoleSpy.mockRestore();
        });
    });
});

describe('Configuration Type Safety', () => {
    it('allows valid JBrowsePyhmmerConfig objects', () => {
        const validConfig: JBrowsePyhmmerConfig = {
            name: 'Test Panel',
            version: '1.0.0',
            description: 'Test description',
            featurePanel: {
                id: 'test-panel',
                title: 'Test Panel',
                icon: '🔍',
                component: 'TestComponent',
                position: 'left',
                width: 500,
                height: 700,
                collapsible: true,
                defaultCollapsed: true,
            },
            pyhmmer: {
                defaultDatabase: 'test_db',
                defaultThreshold: 'bitscore',
                defaultThresholdValue: '100',
                showAdvancedParameters: true,
                maxResults: 100,
                autoExtractSequence: false,
            },
            integration: {
                autoHighlightResults: false,
                showFeatureContext: false,
                enableSequenceExtraction: false,
                customStyling: false,
            },
        };

        expect(validConfig.name).toBe('Test Panel');
        expect(validConfig.featurePanel.position).toBe('left');
        expect(validConfig.pyhmmer.defaultThreshold).toBe('bitscore');
    });

    it('enforces required properties', () => {
        // This should cause a TypeScript error if any required properties are missing
        const requiredProps = [
            'name', 'version', 'description', 'featurePanel', 'pyhmmer', 'integration'
        ];

        requiredProps.forEach(prop => {
            expect(defaultJBrowsePyhmmerConfig).toHaveProperty(prop);
        });
    });
});
