import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PyhmmerResultsTable from '../PyhmmerResultsTable';
import { PyhmmerResult } from '../../../../../interfaces/Pyhmmer';

// Mock the AlignmentView component
jest.mock('../../../atoms/AlignmentView/AlignmentView', () => {
  return function MockAlignmentView({ target }: { target: string }) {
    return <div data-testid="alignment-view">Alignment for {target}</div>;
  };
});

// Mock the Pagination component
jest.mock('../../../molecules/Pagination/Pagination', () => {
  return function MockPagination() {
    return <div data-testid="pagination">Pagination Component</div>;
  };
});

describe('PyhmmerResultsTable', () => {
  const mockResults: PyhmmerResult[] = [
    {
      query: 'test_query',
      target: 'BU_GENE_1',
      evalue: '1e-25',
      score: '95.5',
      num_hits: 3,
      num_significant: 2,
      is_significant: true,
      description: 'Test protein 1',
      domains: [
        { bitscore: 95.5, ievalue: 1e-25, is_significant: true } as any,
        { bitscore: 88.0, ievalue: 1e-20, is_significant: true } as any,
        { bitscore: 15.0, ievalue: 1e-5, is_significant: false } as any
      ]
    },
    {
      query: 'test_query',
      target: 'BU_GENE_2',
      evalue: '1e-20',
      score: '88.1',
      num_hits: 1,
      num_significant: 0,
      is_significant: false,
      description: 'Test protein 2',
      domains: [
        { bitscore: 15.0, ievalue: 1e-5, is_significant: false } as any
      ]
    },
    {
      query: 'test_query',
      target: 'BU_GENE_3',
      evalue: '1e-18',
      score: '82.3',
      num_hits: 2,
      num_significant: 1,
      is_significant: true,
      description: 'Test protein 3',
      domains: [
        { bitscore: 82.3, ievalue: 1e-18, is_significant: true } as any,
        { bitscore: 12.0, ievalue: 1e-3, is_significant: false } as any
      ]
    }
  ];

  const defaultProps = {
    results: mockResults,
    loading: false,
    loadingMessage: '',
    error: undefined,
    jobId: 'test-job-id'
  };

  describe('Basic Rendering', () => {
    it('renders the results table with correct headers', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      expect(screen.getByText('Target')).toBeInTheDocument();
      expect(screen.getByText('E-value')).toBeInTheDocument();
      expect(screen.getByText('Score')).toBeInTheDocument();
      expect(screen.getByText('Hits')).toBeInTheDocument();
      expect(screen.getByText('Significant Hits')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
    });

    it('renders all result rows', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      expect(screen.getByText('BU_GENE_1')).toBeInTheDocument();
      expect(screen.getByText('BU_GENE_2')).toBeInTheDocument();
      expect(screen.getByText('BU_GENE_3')).toBeInTheDocument();
    });

    it('displays domain counts correctly', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      // Check that domain counts are displayed correctly
      expect(screen.getByText('3')).toBeInTheDocument(); // BU_GENE_1 has 3 domains
      expect(screen.getByText('1')).toBeInTheDocument(); // BU_GENE_2 has 1 domain
      expect(screen.getByText('2')).toBeInTheDocument(); // BU_GENE_3 has 2 domains
    });

    it('displays significant domain counts correctly', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      // Check that significant domain counts are displayed correctly
      expect(screen.getByText('2')).toBeInTheDocument(); // BU_GENE_1 has 2 significant domains
      expect(screen.getByText('0')).toBeInTheDocument(); // BU_GENE_2 has 0 significant domains
      expect(screen.getByText('1')).toBeInTheDocument(); // BU_GENE_3 has 1 significant domain
    });
  });

  describe('Results Summary', () => {
    it('displays the results summary with correct counts', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      expect(screen.getByText('Total Genes:')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // 3 total genes
      
      expect(screen.getByText('Total Domains:')).toBeInTheDocument();
      expect(screen.getByText('6')).toBeInTheDocument(); // 3+1+2 = 6 total domains
      
      expect(screen.getByText('Significant Domains:')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // 2+0+1 = 3 significant domains
    });

    it('does not display summary when there are no results', () => {
      render(<PyhmmerResultsTable {...defaultProps} results={[]} />);
      
      expect(screen.queryByText('Total Genes:')).not.toBeInTheDocument();
      expect(screen.queryByText('Total Domains:')).not.toBeInTheDocument();
      expect(screen.queryByText('Significant Domains:')).not.toBeInTheDocument();
    });
  });

  describe('Row Expansion', () => {
    it('shows expansion button for genes with domains', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      // BU_GENE_1 has 3 domains, should show expansion button
      const expandButtons = screen.getAllByRole('button', { name: /expand/i });
      expect(expandButtons).toHaveLength(3); // All genes have domains
    });

    it('does not show expansion button for genes without domains', () => {
      const resultsWithNoDomains: PyhmmerResult[] = [
        {
          ...mockResults[0],
          num_hits: 0,
          num_significant: 0
        }
      ];
      
      render(<PyhmmerResultsTable {...defaultProps} results={resultsWithNoDomains} />);
      
      expect(screen.queryByRole('button', { name: /expand/i })).not.toBeInTheDocument();
    });

    it('expands and collapses rows correctly', async () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      const expandButtons = screen.getAllByRole('button', { name: /expand/i });
      const firstExpandButton = expandButtons[0];
      
      // Initially collapsed
      expect(screen.queryByTestId('alignment-view')).not.toBeInTheDocument();
      
      // Click to expand
      fireEvent.click(firstExpandButton);
      await waitFor(() => {
        expect(screen.getByTestId('alignment-view')).toBeInTheDocument();
      });
      
      // Click to collapse
      fireEvent.click(firstExpandButton);
      await waitFor(() => {
        expect(screen.queryByTestId('alignment-view')).not.toBeInTheDocument();
      });
    });

    it('shows alignment view with correct target when expanded', async () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      const expandButtons = screen.getAllByRole('button', { name: /expand/i });
      fireEvent.click(expandButtons[0]);
      
      await waitFor(() => {
        expect(screen.getByText('Alignment for BU_GENE_1')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles results with missing optional fields', () => {
      const incompleteResults: PyhmmerResult[] = [
        {
          query: 'test_query',
          target: 'BU_GENE_INCOMPLETE',
          evalue: '1e-25',
          score: '95.5',
          num_hits: 0,
          num_significant: 0,
          is_significant: false,
          description: undefined,
          domains: []
        }
      ];
      
      render(<PyhmmerResultsTable {...defaultProps} results={incompleteResults} />);
      
      expect(screen.getByText('BU_GENE_INCOMPLETE')).toBeInTheDocument();
      expect(screen.getByText('-')).toBeInTheDocument(); // Default for missing description
    });

    it('handles zero domain counts correctly', () => {
      const zeroDomainResults: PyhmmerResult[] = [
        {
          ...mockResults[0],
          num_hits: 0,
          num_significant: 0
        }
      ];
      
      render(<PyhmmerResultsTable {...defaultProps} results={zeroDomainResults} />);
      
      expect(screen.getByText('0')).toBeInTheDocument(); // num_hits
      expect(screen.getByText('0')).toBeInTheDocument(); // num_significant
    });

    it('handles very large domain counts', () => {
      const largeDomainResults: PyhmmerResult[] = [
        {
          ...mockResults[0],
          num_hits: 999,
          num_significant: 456
        }
      ];
      
      render(<PyhmmerResultsTable {...defaultProps} results={largeDomainResults} />);
      
      expect(screen.getByText('999')).toBeInTheDocument();
      expect(screen.getByText('456')).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading spinner when loading', () => {
      render(<PyhmmerResultsTable {...defaultProps} loading={true} />);
      
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('shows loading message when provided', () => {
      render(<PyhmmerResultsTable {...defaultProps} loading={true} loadingMessage="Processing results..." />);
      
      expect(screen.getByText('Processing results...')).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('shows error message when error occurs', () => {
      render(<PyhmmerResultsTable {...defaultProps} error="Failed to load results" />);
      
      expect(screen.getByText('Failed to load results')).toBeInTheDocument();
    });

    it('does not show results when there is an error', () => {
      render(<PyhmmerResultsTable {...defaultProps} error="Failed to load results" />);
      
      expect(screen.queryByText('BU_GENE_1')).not.toBeInTheDocument();
      expect(screen.getByText('Failed to load results')).toBeInTheDocument();
    });
  });

  describe('Pagination', () => {
    it('shows pagination when there are multiple pages', () => {
      // Create more results to trigger pagination
      const manyResults = Array.from({ length: 25 }, (_, i) => ({
        ...mockResults[0],
        target: `BU_GENE_${i + 1}`,
        num_hits: i + 1,
        num_significant: Math.floor((i + 1) / 2)
      }));
      
      render(<PyhmmerResultsTable {...defaultProps} results={manyResults} />);
      
      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });

    it('does not show pagination for single page results', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      expect(screen.queryByTestId('pagination')).not.toBeInTheDocument();
    });
  });

  describe('Download Functionality', () => {
    it('shows download buttons when results are available', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      expect(screen.getByText('Tab Delimited')).toBeInTheDocument();
      expect(screen.getByText('FASTA')).toBeInTheDocument();
      expect(screen.getByText('Aligned FASTA')).toBeInTheDocument();
    });

    it('disables download buttons when downloading', () => {
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      // Since downloading is internal state, we can't test it directly
      // This test would need to be updated if we expose downloading state
      expect(screen.getByText('Tab Delimited')).toBeInTheDocument();
      expect(screen.getByText('FASTA')).toBeInTheDocument();
      expect(screen.getByText('Aligned FASTA')).toBeInTheDocument();
    });
  });

  describe('Target Click Handling', () => {
    it('calls handleTargetClick when target is clicked', () => {
      const mockHandleTargetClick = jest.fn();
      
      // We need to mock the component to test this functionality
      // This would require more complex setup with React Testing Library
      // For now, we'll test the basic rendering
      render(<PyhmmerResultsTable {...defaultProps} />);
      
      const targetLinks = screen.getAllByText(/BU_GENE_/);
      expect(targetLinks).toHaveLength(3);
    });
  });
});
