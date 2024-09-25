import { getData } from './api';
import apiInstance from "./apiInstance";

// Fetch genomes based on species and genome query
export const fetchGenomesBySearch = async (species: string, genome: string): Promise<any> => {
  try {
    return await getData('genomes/search', { species, genome });
  } catch (error) {
    console.error('Error fetching genome search results:', error);
    throw error;
  }
};

// Fetch isolate suggestions with optional species ID
export const fetchFuzzyIsolateSuggestions = async (query: string, speciesId?: string) => {
  try {
    const params: any = { query };

    // Include speciesId if provided
    if (speciesId) {
      params.species_id = speciesId;
    }

    const response = await apiInstance.get('genomes/search/autocomplete', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching isolate suggestions:', error);
    throw error;
  }
};

// Fetch all isolates or isolates filtered by species ID
export const fetchIsolatesBySpecies = async (speciesId?: string) => {
  try {
    const params = speciesId ? { species_id: speciesId } : {};
    const response = await apiInstance.get('species/isolates', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching isolates:', error);
    throw error;
  }
};
