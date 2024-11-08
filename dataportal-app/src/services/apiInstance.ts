import axios from 'axios';

const baseURL = process.env.REACT_APP_API_BASE_URL;

console.log('API Base URL:', baseURL);

const apiInstance = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Add request interceptor
apiInstance.interceptors.request.use(
    (config) => {
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add response interceptor
apiInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API response error:', error);
        return Promise.reject(error);
    }
);

export default apiInstance;
