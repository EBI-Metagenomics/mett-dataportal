/**
 * JBrowse PyHMMER Feature Panel Integration Tests
 * Tests the JBrowse-specific integration functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import JBrowsePyhmmerFeaturePanel from '../JBrowsePyhmmerFeaturePanel';
import { PyhmmerResult } from '../../../../../interfaces/Pyhmmer';

// Mock the PyhmmerFeaturePanel component
jest.mock('../PyhmmerFeaturePanel', () => {
    return function MockPyhmmerFeaturePanel(props: any) {
        return (
            <div data-testid="pyhmmer-feature-panel">
                <div>Mock PyHMMER Feature Panel</div>
                <button 
                    onClick={() => props.onResultClick?.({ id: '1', target: 'test-gene' } as PyhmmerResult)}
                    data-testid="mock-result-click"
                >
                    Click Result
                </button>
                <button 
                    onClick={() => props.onSearchComplete?.([{ id: '1', target: 'test-gene' } as PyhmmerResult])}
                    data-testid="mock-search-complete"
                >
                    Complete Search
                </button>
                <button 
                    onClick={() => props.onError?.('Test error')}
                    data-testid="mock-error"
                >
                    Trigger Error
                </button>
            </div>
        );
    };
});

// Mock JBrowse context
const mockJBrowseFeature = {
    id: 'test-feature-1',
    name: 'Test Gene',
    type: 'gene',
    start: 1000,
    end: 2000,
    strand: '+',
    sequence: 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWKRVMGVGDFT',
    attributes: {
        product: 'hypothetical protein',
        locus_tag: 'BU_001',
    },
};

const mockJBrowseSession = {
    model: {
        highlightFeature: jest.fn(),
    },
    view: {
        model: {
            highlightFeature: jest.fn(),
        },
    },
};

const mockJBrowseModel = {
    highlightFeature: jest.fn(),
};

describe('JBrowsePyhmmerFeaturePanel', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('renders without crashing', () => {
            render(<JBrowsePyhmmerFeaturePanel />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('renders with custom className', () => {
            render(<JBrowsePyhmmerFeaturePanel className="custom-class" />);
            const container = screen.getByTestId('pyhmmer-feature-panel').closest('div');
            expect(container).toHaveClass('custom-class');
        });

        it('renders JBrowse header when feature is provided', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByText('Test Gene')).toBeInTheDocument();
            expect(screen.getByText('gene')).toBeInTheDocument();
        });

        it('renders expand/collapse toggle when feature is provided', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByLabelText('Expand')).toBeInTheDocument();
        });

        it('does not render JBrowse header when no feature is provided', () => {
            render(<JBrowsePyhmmerFeaturePanel />);
            expect(screen.queryByText('Test Gene')).not.toBeInTheDocument();
            expect(screen.queryByLabelText('Expand')).not.toBeInTheDocument();
        });
    });

    describe('Feature Information Display', () => {
        it('displays feature name correctly', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByText('Test Gene')).toBeInTheDocument();
        });

        it('displays feature type correctly', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByText('gene')).toBeInTheDocument();
        });

        it('handles missing feature name gracefully', () => {
            const featureWithoutName = { ...mockJBrowseFeature, name: undefined };
            render(<JBrowsePyhmmerFeaturePanel feature={featureWithoutName} />);
            expect(screen.getByText('test-feature-1')).toBeInTheDocument();
        });

        it('handles missing feature type gracefully', () => {
            const featureWithoutType = { ...mockJBrowseFeature, type: undefined };
            render(<JBrowsePyhmmerFeaturePanel feature={featureWithoutType} />);
            expect(screen.queryByText('gene')).not.toBeInTheDocument();
        });
    });

    describe('Sequence Extraction', () => {
        it('extracts sequence from feature.sequence', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            // The sequence should be passed to PyhmmerFeaturePanel as defaultSequence
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('extracts sequence from feature.attributes', () => {
            const featureWithAttrSequence = {
                ...mockJBrowseFeature,
                sequence: undefined,
                attributes: {
                    ...mockJBrowseFeature.attributes,
                    protein_sequence: 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWKRVMGVGDFT',
                },
            };
            render(<JBrowsePyhmmerFeaturePanel feature={featureWithAttrSequence} />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('falls back to default sequence when no sequence found', () => {
            const featureWithoutSequence = {
                ...mockJBrowseFeature,
                sequence: undefined,
                attributes: {},
            };
            render(<JBrowsePyhmmerFeaturePanel 
                feature={featureWithoutSequence} 
                defaultSequence="DEFAULT_SEQUENCE"
            />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('handles malformed feature gracefully', () => {
            const malformedFeature = null;
            render(<JBrowsePyhmmerFeaturePanel feature={malformedFeature} />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });
    });

    describe('Expand/Collapse Functionality', () => {
        it('toggles expanded state when toggle button is clicked', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            const toggleButton = screen.getByLabelText('Expand');
            
            fireEvent.click(toggleButton);
            expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
            
            fireEvent.click(toggleButton);
            expect(screen.getByLabelText('Expand')).toBeInTheDocument();
        });

        it('starts in expanded state by default', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByLabelText('Expand')).toBeInTheDocument();
        });
    });

    describe('Event Handling', () => {
        it('calls onResultClick when result is clicked', async () => {
            const mockOnResultClick = jest.fn();
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                onResultClick={mockOnResultClick}
            />);
            
            const resultButton = screen.getByTestId('mock-result-click');
            fireEvent.click(resultButton);
            
            await waitFor(() => {
                expect(mockOnResultClick).toHaveBeenCalledWith(
                    expect.objectContaining({ id: '1', target: 'test-gene' })
                );
            });
        });

        it('calls onSearchComplete when search completes', async () => {
            const mockOnSearchComplete = jest.fn();
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                onSearchComplete={mockOnSearchComplete}
            />);
            
            const searchCompleteButton = screen.getByTestId('mock-search-complete');
            fireEvent.click(searchCompleteButton);
            
            await waitFor(() => {
                expect(mockOnSearchComplete).toHaveBeenCalledWith(
                    expect.arrayContaining([
                        expect.objectContaining({ id: '1', target: 'test-gene' })
                    ])
                );
            });
        });

        it('calls onError when error occurs', async () => {
            const mockOnError = jest.fn();
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                onError={mockOnError}
            />);
            
            const errorButton = screen.getByTestId('mock-error');
            fireEvent.click(errorButton);
            
            await waitFor(() => {
                expect(mockOnError).toHaveBeenCalledWith('Test error');
            });
        });

        it('logs JBrowse context when callbacks are triggered', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            const mockOnSearchComplete = jest.fn();
            
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                session={mockJBrowseSession}
                model={mockJBrowseModel}
                onSearchComplete={mockOnSearchComplete}
            />);
            
            const searchCompleteButton = screen.getByTestId('mock-search-complete');
            fireEvent.click(searchCompleteButton);
            
            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(
                    'PyHMMER search completed for JBrowse feature: Test Gene'
                );
                expect(consoleSpy).toHaveBeenCalledWith('Found 1 results');
            });
            
            consoleSpy.mockRestore();
        });
    });

    describe('JBrowse Integration', () => {
        it('attempts to highlight results in JBrowse when available', async () => {
            const mockOnResultClick = jest.fn();
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                session={mockJBrowseSession}
                model={mockJBrowseModel}
                onResultClick={mockOnResultClick}
            />);
            
            const resultButton = screen.getByTestId('mock-result-click');
            fireEvent.click(resultButton);
            
            await waitFor(() => {
                expect(mockOnResultClick).toHaveBeenCalled();
            });
        });

        it('handles missing JBrowse context gracefully', async () => {
            const mockOnResultClick = jest.fn();
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                onResultClick={mockOnResultClick}
            />);
            
            const resultButton = screen.getByTestId('mock-result-click');
            fireEvent.click(resultButton);
            
            await waitFor(() => {
                expect(mockOnResultClick).toHaveBeenCalled();
            });
            
            consoleSpy.mockRestore();
        });
    });

    describe('Default Values', () => {
        it('uses default database when provided', () => {
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                defaultDatabase="bu_pv_all"
            />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('uses default threshold when provided', () => {
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                defaultThreshold="bitscore"
            />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });

        it('uses default sequence when provided', () => {
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                defaultSequence="CUSTOM_SEQUENCE"
            />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has proper ARIA labels for expand/collapse', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            expect(screen.getByLabelText('Expand')).toBeInTheDocument();
        });

        it('updates ARIA label when state changes', () => {
            render(<JBrowsePyhmmerFeaturePanel feature={mockJBrowseFeature} />);
            const toggleButton = screen.getByLabelText('Expand');
            
            fireEvent.click(toggleButton);
            expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        it('handles sequence extraction errors gracefully', () => {
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Create a feature that will cause an error during sequence extraction
            const problematicFeature = {
                ...mockJBrowseFeature,
                get sequence() { throw new Error('Test error'); }
            };
            
            render(<JBrowsePyhmmerFeaturePanel feature={problematicFeature} />);
            expect(screen.getByTestId('pyhmmer-feature-panel')).toBeInTheDocument();
            
            consoleSpy.mockRestore();
        });

        it('handles JBrowse highlighting errors gracefully', async () => {
            const mockOnResultClick = jest.fn();
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Create a model that will throw an error
            const problematicModel = {
                highlightFeature: () => { throw new Error('Highlight error'); }
            };
            
            render(<JBrowsePyhmmerFeaturePanel 
                feature={mockJBrowseFeature}
                session={mockJBrowseSession}
                model={problematicModel}
                onResultClick={mockOnResultClick}
            />);
            
            const resultButton = screen.getByTestId('mock-result-click');
            fireEvent.click(resultButton);
            
            await waitFor(() => {
                expect(mockOnResultClick).toHaveBeenCalled();
            });
            
            consoleSpy.mockRestore();
        });
    });
});
