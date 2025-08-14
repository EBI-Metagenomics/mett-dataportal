import {useEffect, useState} from 'react';
import {FeatureFlags, FeatureService} from '../services/common/featureService';

export const useFeatureFlags = () => {
    const [features, setFeatures] = useState<FeatureFlags | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadFeatures = async () => {
            try {
                setLoading(true);
                setError(null);
                const featureFlags = await FeatureService.getFeatures();
                setFeatures(featureFlags);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load feature flags');
                // Set default features on error
                setFeatures({
                    pyhmmer_search: false,
                    feedback: false,
                    natural_query: false
                });
            } finally {
                setLoading(false);
            }
        };

        loadFeatures();
    }, []);

    const isFeatureEnabled = (feature: keyof FeatureFlags): boolean => {
        // For natural_query, if it's not in the response, it means it's disabled
        if (feature === 'natural_query') {
            return features?.[feature] === true;
        }
        return features?.[feature] || false;
    };

    return {
        features,
        loading,
        error,
        isFeatureEnabled
    };
}; 