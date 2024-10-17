import axios from 'axios';

const apiInstance = axios.create({
  baseURL: 'http://localhost:8000/api', // Update with your actual base URL
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add request interceptor
apiInstance.interceptors.request.use(
  (config) => {
    // You can modify the request config here (e.g., adding authorization tokens)
    return config;
  },
  (error) => {
    // Handle request errors
    return Promise.reject(error);
  }
);

// Add response interceptor
apiInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle response errors globally
    console.error('API response error:', error);
    return Promise.reject(error);
  }
);

export default apiInstance;
