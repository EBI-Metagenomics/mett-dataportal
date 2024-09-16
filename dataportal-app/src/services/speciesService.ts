import { getData } from './api';

// Define a function to fetch species data
export const fetchSpeciesList = async (): Promise<any> => {
  try {
    return await getData('species/list/');
  } catch (error) {
    console.error('Error fetching species list:', error);
    throw error;
  }
};
