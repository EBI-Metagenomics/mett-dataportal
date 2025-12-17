import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL } from "../../utils/common/constants";
import { TokenStorage } from "../../utils/auth";

export class ApiClient {
    private static instance: AxiosInstance | null = null;

    /**
     * Get the Axios instance (singleton).
     */
    public static getInstance(): AxiosInstance {
        if (!this.instance) {
            this.instance = axios.create({
                baseURL: API_BASE_URL,
                headers: {
                    "Content-Type": "application/json",
                },
                timeout: 30000, 
            });

            // Add request interceptor to include JWT token
            this.instance.interceptors.request.use(
                (config: InternalAxiosRequestConfig) => {
                    const token = TokenStorage.getToken();
                    if (token) {
                        config.headers.Authorization = `Bearer ${token}`;
                    }
                    return config;
                },
                (error) => Promise.reject(error)
            );

            // Add response interceptor to handle authentication errors
            this.instance.interceptors.response.use(
                (response) => response,
                (error) => {
                    // Handle 401 Unauthorized - token might be expired or invalid
                    if (error.response?.status === 401) {
                        // Clear invalid token
                        TokenStorage.removeToken();
                        
                        // Optionally trigger a token refresh or redirect to login
                        // For now, we'll just log and let the error propagate
                        console.warn("Authentication failed - token may be expired or invalid");
                    }
                    
                    console.error("API response error:", error);
                    return Promise.reject(error);
                }
            );
        }
        return this.instance;
    }

    /**
     * Reset the instance (useful for testing or when token changes)
     */
    public static resetInstance(): void {
        this.instance = null;
    }
}

// Export a single instance for use
export default ApiClient.getInstance();
