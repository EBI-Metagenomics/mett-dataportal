import { getData } from './api';

// Define a function to fetch search results
export const fetchSearchResults = async (species: string, genome: string): Promise<any> => {
  try {
    return await getData('search/results/', { species, genome });
  } catch (error) {
    console.error('Error fetching search results:', error);
    throw error;
  }
};
