import { useState, useEffect, useRef } from 'react';

interface UseDebouncedLoadingProps {
    loading: boolean;
    delay?: number;
    minLoadingTime?: number;
}

export const useDebouncedLoading = ({ 
    loading, 
    delay = 300, 
    minLoadingTime = 500 
}: UseDebouncedLoadingProps) => {
    const [debouncedLoading, setDebouncedLoading] = useState(loading);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const loadingStartTimeRef = useRef<number | null>(null);

    useEffect(() => {
        // Clear any existing timeout
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }

        if (loading) {
            // Starting to load
            loadingStartTimeRef.current = Date.now();
            
            // Set loading immediately if it's been off for a while
            if (!debouncedLoading) {
                setDebouncedLoading(true);
            }
        } else {
            // Stopping loading
            const loadingStartTime = loadingStartTimeRef.current;
            const currentTime = Date.now();
            
            if (loadingStartTime && (currentTime - loadingStartTime) < minLoadingTime) {
                // Ensure minimum loading time
                const remainingTime = minLoadingTime - (currentTime - loadingStartTime);
                timeoutRef.current = setTimeout(() => {
                    setDebouncedLoading(false);
                }, remainingTime);
            } else {
                // Add delay before hiding loading state
                timeoutRef.current = setTimeout(() => {
                    setDebouncedLoading(false);
                }, delay);
            }
        }

        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, [loading, delay, minLoadingTime, debouncedLoading]);

    return debouncedLoading;
}; 