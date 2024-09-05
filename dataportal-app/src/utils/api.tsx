import apiInstance from './apiInstance';

// Define a type for the params to be used in GET and POST requests
type ParamsType = Record<string, any>;

// Function to handle generic GET requests
export const getData = (endpoint: string, params: ParamsType = {}): Promise<any> => {
  return apiInstance.get(endpoint, { params })
    .then(response => response.data)
    .catch(error => {
      console.error('Error fetching data:', error.message);
      throw error;
    });
};

// Function to handle generic POST requests
export const postData = (endpoint: string, data: ParamsType): Promise<any> => {
  return apiInstance.post(endpoint, data)
    .then(response => response.data)
    .catch(error => {
      console.error('Error posting data:', error.message);
      throw error;
    });
};

// Function to handle generic PUT requests
export const putData = (endpoint: string, data: ParamsType): Promise<any> => {
  return apiInstance.put(endpoint, data)
    .then(response => response.data)
    .catch(error => {
      console.error('Error putting data:', error.message);
      throw error;
    });
};

// Function to handle generic DELETE requests
export const deleteData = (endpoint: string): Promise<any> => {
  return apiInstance.delete(endpoint)
    .then(response => response.data)
    .catch(error => {
      console.error('Error deleting data:', error.message);
      throw error;
    });
};
