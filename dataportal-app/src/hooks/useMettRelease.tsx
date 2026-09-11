import React, {createContext, useCallback, useContext, useEffect, useMemo, useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {ApiService} from '../services/common/api';

export const METT_RELEASE_STORAGE_KEY = 'mett_release';

export interface MettReleaseFamily {
    family: string;
    alias: string;
    physical_index: string;
    generation: number;
    adopted_legacy: boolean;
}

export interface MettRelease {
    version: string;
    status: string;
    is_current: boolean;
    promoted_at: string | null;
    archived_at: string | null;
    families: MettReleaseFamily[];
}

export interface MettReleaseList {
    default: string;
    selected: string;
    current_version: string | null;
    releases: MettRelease[];
}

interface ReleaseContextValue {
    selected: string;
    setSelected: (version: string) => void;
    catalog: MettReleaseList | null;
    loading: boolean;
}

const ReleaseContext = createContext<ReleaseContextValue | undefined>(undefined);

async function fetchReleases(): Promise<MettReleaseList> {
    return ApiService.get<MettReleaseList>('/releases');
}

export const ReleaseProvider: React.FC<{children: React.ReactNode}> = ({children}) => {
    const queryClient = useQueryClient();
    const [selected, setSelectedState] = useState(() => {
        if (typeof window === 'undefined') {
            return 'current';
        }
        return (
            localStorage.getItem(METT_RELEASE_STORAGE_KEY) ||
            import.meta.env.VITE_METT_DEFAULT_RELEASE ||
            'current'
        );
    });

    const {data, isLoading} = useQuery({
        queryKey: ['mett-releases'],
        queryFn: fetchReleases,
        staleTime: 60 * 1000,
        retry: 1,
    });

    useEffect(() => {
        if (!data?.releases?.length) {
            return;
        }
        const known = new Set(data.releases.map((r) => r.version));
        if (selected !== 'current' && !known.has(selected)) {
            localStorage.setItem(METT_RELEASE_STORAGE_KEY, 'current');
            setSelectedState('current');
        }
    }, [data, selected]);

    const setSelected = useCallback(
        (version: string) => {
            localStorage.setItem(METT_RELEASE_STORAGE_KEY, version);
            setSelectedState(version);
            queryClient.invalidateQueries();
        },
        [queryClient]
    );

    const value = useMemo(
        () => ({
            selected,
            setSelected,
            catalog: data ?? null,
            loading: isLoading,
        }),
        [selected, setSelected, data, isLoading]
    );

    return <ReleaseContext.Provider value={value}>{children}</ReleaseContext.Provider>;
};

export const useMettRelease = (): ReleaseContextValue => {
    const ctx = useContext(ReleaseContext);
    if (!ctx) {
        throw new Error('useMettRelease must be used within ReleaseProvider');
    }
    return ctx;
};
