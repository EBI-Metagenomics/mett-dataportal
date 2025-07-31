// Mock errorHandler to avoid import.meta issues
export const handleApiError = (error: any, context?: string) => {
    console.error('Mock error handler:', error, context);
};

export const handleNetworkError = (error: any) => {
    console.error('Mock network error handler:', error);
};

export const handleValidationError = (error: any) => {
    console.error('Mock validation error handler:', error);
};

export const logError = (error: any, context?: string) => {
    console.error('Mock log error:', error, context);
}; 