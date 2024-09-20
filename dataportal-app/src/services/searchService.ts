import { getData } from './api';
import apiInstance from "./apiInstance";

export const fetchSearchGenomes = async (species: string, genome: string): Promise<any> => {
  try {
    return await getData('search/genome/', { species, genome });
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
    return response.data;
  } catch (error) {
    console.error('Error fetching isolates:', error);
    throw error;
  }
};