import { getData } from './api';
import apiInstance from "./apiInstance";

// Define a function to fetch search results
export const fetchSearchResults = async (species: string, genome: string): Promise<any> => {
  try {
    return await getData('search/results/', { species, genome });
  } catch (error) {
    console.error('Error fetching search results:', error);
    throw error;
  }
};

export const fetchFuzzyIsolateSearch = async (query: string, speciesId?: string) => {
  try {
    const params: any = { query };

    // If a speciesId is provided, include it as a filter
    if (speciesId) {
      params.species_id = speciesId;
    }

    const response = await apiInstance.get('search/autocomplete', { params });
    return response.data; // Assuming the response contains 'results'
  } catch (error) {
    console.error('Error fetching isolates:', error);
    throw error;
  }
};