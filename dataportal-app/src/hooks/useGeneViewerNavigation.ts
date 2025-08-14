import {useEffect, useState} from 'react';
import {GeneMeta} from '../interfaces/Gene';
import {ZOOM_LEVELS} from '../utils/common/constants';

interface UseGeneViewerNavigationProps {
    viewState: any;
    geneMeta: GeneMeta | null;
    loading: boolean;
    setLoading: (loading: boolean) => void;
}

interface UseGeneViewerNavigationReturn {
    isNavigating: boolean;
    navigationError: string | null;
}

export const useGeneViewerNavigation = ({
                                            viewState,
                                            geneMeta,
                                            loading,
                                            setLoading,
                                        }: UseGeneViewerNavigationProps): UseGeneViewerNavigationReturn => {
    const [isNavigating, setIsNavigating] = useState(false);
    const [navigationError, setNavigationError] = useState<string | null>(null);

    useEffect(() => {
        const waitForInitialization = async () => {
            if (viewState && geneMeta) {
                const linearGenomeView = viewState.session.views[0];

                if (linearGenomeView?.type === 'LinearGenomeView') {
                    console.log('Waiting for LinearGenomeView to initialize...');

                    const waitForReady = async () => {
                        const maxRetries = 2;
                        let retries = 0;

                        while (!linearGenomeView.initialized && retries < maxRetries) {
                            console.log(`Retry ${retries + 1}: LinearGenomeView not initialized yet.`);
                            await new Promise(resolve => setTimeout(resolve, 200));
                            retries++;
                        }

                        if (!linearGenomeView.initialized) {
                            console.error('LinearGenomeView failed to initialize within the timeout period.');
                            setNavigationError('Failed to initialize genome viewer');
                            return;
                        }

                        console.log('LinearGenomeView initialized:', linearGenomeView.initialized);

                        try {
                            setIsNavigating(true);
                            setLoading(true);
                            const locationString = `${geneMeta.seq_id}:${geneMeta.start_position}..${geneMeta.end_position}`;
                            console.log('Navigating to:', locationString);

                            // Perform navigation
                            linearGenomeView.navToLocString(locationString);

                            // Apply zoom with a delay
                            setTimeout(() => {
                                linearGenomeView.zoomTo(ZOOM_LEVELS.NAV);
                                console.log('Zoom applied');
                                setLoading(false);
                                setIsNavigating(false);
                            }, 200);
                        } catch (error) {
                            console.error('Error during navigation or zoom:', error);
                            setNavigationError('Failed to navigate to gene location');
                            setLoading(false);
                            setIsNavigating(false);
                        }
                    };

                    await waitForReady();
                } else {
                    console.error('LinearGenomeView not found or of incorrect type.');
                    setNavigationError('Invalid genome viewer configuration');
                }
            } else {
                console.log('viewState or geneMeta not ready.');
            }
        };

        waitForInitialization();
    }, [viewState, geneMeta, setLoading]);

    // Handle viewState changes
    useEffect(() => {
        if (viewState) {
            setLoading(true);
            const refreshTimeout = setTimeout(() => setLoading(false), 500);
            return () => clearTimeout(refreshTimeout);
        }
    }, [viewState, setLoading]);

    return {
        isNavigating,
        navigationError,
    };
}; 