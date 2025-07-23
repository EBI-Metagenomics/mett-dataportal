import {renderHook} from '@testing-library/react';
import {usePageCleanup} from './usePageCleanup';
import {useFilterStore} from '../stores/filterStore';
import {useLocation} from 'react-router-dom';

// Mock the dependencies
jest.mock('react-router-dom', () => ({
    useLocation: jest.fn(),
}));

jest.mock('../stores/filterStore', () => ({
    useFilterStore: jest.fn(),
}));

describe('usePageCleanup', () => {
    const mockSetGenomeSearchQuery = jest.fn();
    const mockSetGenomeSortField = jest.fn();
    const mockSetGenomeSortOrder = jest.fn();
    const mockSetGeneSearchQuery = jest.fn();
    const mockSetGeneSortField = jest.fn();
    const mockSetGeneSortOrder = jest.fn();
    const mockSetFacetedFilters = jest.fn();
    const mockSetFacetOperators = jest.fn();
    const mockSetSelectedGenomes = jest.fn();

    const mockFilterStore = {
        setGenomeSearchQuery: mockSetGenomeSearchQuery,
        setGenomeSortField: mockSetGenomeSortField,
        setGenomeSortOrder: mockSetGenomeSortOrder,
        setGeneSearchQuery: mockSetGeneSearchQuery,
        setGeneSortField: mockSetGeneSortField,
        setGeneSortOrder: mockSetGeneSortOrder,
        setFacetedFilters: mockSetFacetedFilters,
        setFacetOperators: mockSetFacetOperators,
        setSelectedGenomes: mockSetSelectedGenomes,
    };

    beforeEach(() => {
        jest.clearAllMocks();
        (useFilterStore as unknown as jest.Mock).mockReturnValue(mockFilterStore);
    });

    it('should clean up filter store when navigating to gene viewer page', () => {
        (useLocation as jest.Mock).mockReturnValue({
            pathname: '/genome/BU_ATCC8492VPI0062_NT5002.1',
            search: '?locus_tag=BU_ATCC8492VPI0062_00001',
        });

        renderHook(() => usePageCleanup());

        // Verify that filter store methods were called to reset state
        expect(mockSetGenomeSearchQuery).toHaveBeenCalledWith('');
        expect(mockSetGenomeSortField).toHaveBeenCalledWith('species');
        expect(mockSetGenomeSortOrder).toHaveBeenCalledWith('asc');
        expect(mockSetGeneSearchQuery).toHaveBeenCalledWith('');
        expect(mockSetGeneSortField).toHaveBeenCalledWith('locus_tag');
        expect(mockSetGeneSortOrder).toHaveBeenCalledWith('asc');
        expect(mockSetFacetedFilters).toHaveBeenCalledWith({});
        expect(mockSetFacetOperators).toHaveBeenCalledWith({});
        expect(mockSetSelectedGenomes).toHaveBeenCalledWith([{
            isolate_name: 'BU_ATCC8492VPI0062_NT5002.1',
            type_strain: false,
        }]);
    });

    it('should clean up gene viewer state when navigating back to home page with locus_tag', () => {
        (useLocation as jest.Mock).mockReturnValue({
            pathname: '/',
            search: '?tab=genes&locus_tag=BU_ATCC8492VPI0062_00001',
        });

        renderHook(() => usePageCleanup());

        // Verify that gene viewer specific state was cleaned up
        expect(mockSetGeneSearchQuery).toHaveBeenCalledWith('');
        expect(mockSetGeneSortField).toHaveBeenCalledWith('locus_tag');
        expect(mockSetGeneSortOrder).toHaveBeenCalledWith('asc');
        expect(mockSetFacetedFilters).toHaveBeenCalledWith({});
        expect(mockSetFacetOperators).toHaveBeenCalledWith({});
    });

    it('should not clean up state when navigating to home page without locus_tag', () => {
        (useLocation as jest.Mock).mockReturnValue({
            pathname: '/',
            search: '?tab=genes',
        });

        renderHook(() => usePageCleanup());

        // Verify that no cleanup was performed
        expect(mockSetGenomeSearchQuery).not.toHaveBeenCalled();
        expect(mockSetGeneSearchQuery).not.toHaveBeenCalled();
        expect(mockSetFacetedFilters).not.toHaveBeenCalled();
        expect(mockSetFacetOperators).not.toHaveBeenCalled();
    });
}); 