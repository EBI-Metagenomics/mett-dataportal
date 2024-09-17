import { getData } from './api';
import apiInstance from "./apiInstance";

// Define a function to fetch species data
export const fetchSpeciesList = async (): Promise<any> => {
  try {
    return await getData('species/list');
  } catch (error) {
    console.error('Error fetching species list:', error);
    throw error;
  }
};

export const fetchIsolateList = async (speciesId?: string) => {
  const url = speciesId
    ? `/api/isolates?species=${speciesId}` // Fetch isolates by species
    : '/api/isolates'; // Fetch all isolates
  const response = await apiInstance.get(url);
  return response.data;
};
