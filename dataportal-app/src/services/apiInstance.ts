import axios from 'axios';
import {API_BASE_URL} from "../utils/appConstants";


console.log('API Base URL:', API_BASE_URL);

const apiInstance = axios.create({
    baseURL: API_BASE_URL,
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
