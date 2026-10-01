import React, {useEffect} from 'react';
import {BrowserRouter as Router, Route, Routes, useLocation} from 'react-router-dom';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import Header from '@components/organisms/Header/Header';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';
import ErrorBoundary from "@components/atoms/ErrorBoundary";
import Footer from "@components/organisms/Footer/Footer";
import NaturalQuerySearchPage from "@components/pages/NaturalQuerySearchPage";
import {useFeatureFlags} from "./hooks/useFeatureFlags";
import {AuthProvider} from "./hooks/useAuth";
import {ReleaseProvider} from "./hooks/useMettRelease";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            gcTime: 10 * 60 * 1000, // 10 minutes
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
});

const UrlCleanupHandler: React.FC = () => {
    const location = useLocation();

    useEffect(() => {
        // Deep-links historically carried stray homepage params. Keep locus_tag
        // and gene search/sort/facet params; drop the rest.
        if (!location.pathname.startsWith('/genome/')) {
            return;
        }

        const searchParams = new URLSearchParams(location.search);
        const locusTag = searchParams.get('locus_tag');
        if (!locusTag) {
            return;
        }

        const allowedKeys = [
            'locus_tag',
            'geneSearch',
            'geneSortField',
            'geneSortOrder',
            'facetedFilters',
            'facetOperators',
        ];
        const next = new URLSearchParams();
        allowedKeys.forEach((key) => {
            const value = searchParams.get(key);
            if (value) {
                next.set(key, value);
            }
        });

        if (next.toString() === searchParams.toString()) {
            return;
        }

        window.history.replaceState({}, '', `${location.pathname}?${next.toString()}`);
    }, [location.pathname, location.search]);

    return null;
};

const PageCleanupHandler: React.FC = () => {
    // usePageCleanup();
    return null;
};

const ConditionalNaturalQueryRoute: React.FC = () => {
    const {isFeatureEnabled} = useFeatureFlags();
    
    if (!isFeatureEnabled('natural_query')) {
        return <div>Feature not available</div>;
    }
    
    return <NaturalQuerySearchPage />;
};

const App: React.FC = () => {
    // Prefer Vite's BASE_URL (tied to build `base`) for router basename.
    // This avoids "blank page" failures when VITE_BASENAME is unset/mis-set in a deployment.
    const baseUrl = import.meta.env.BASE_URL;
    const routerBasename = (() => {
        if (!baseUrl) return '/';
        const trimmed = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
        return trimmed === '' ? '/' : trimmed;
    })();

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
            <ReleaseProvider>
            <div style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
                <Router basename={routerBasename}>
                    <UrlCleanupHandler/>
                    <PageCleanupHandler/>
                    <Header/>
                    <Routes>
                        <Route path="/" element={
                            <main
                                className="home-page vf-body | vf-stack vf-stack--200"
                                style={{
                                    '--vf-body-width': '80%',
                                    paddingBottom: '200px',
                                } as React.CSSProperties}
                            >
                                <HomePage/>
                            </main>
                        }/>
                        <Route path="/home" element={
                            <main
                                className="home-page vf-body | vf-stack vf-stack--200"
                                style={{
                                    '--vf-body-width': '80%',
                                    paddingBottom: '200px',
                                } as React.CSSProperties}
                            >
                                <HomePage/>
                            </main>
                        }/>
                        <Route path="/genome/:strainName" element={
                            <main
                                className="gene-viewer-page vf-body | vf-stack vf-stack--200"
                                style={{
                                    '--vf-body-width': '95%',
                                    paddingBottom: '200px',
                                } as React.CSSProperties}
                            >
                                <ErrorBoundary>
                                    <GeneViewerPage/>
                                </ErrorBoundary>
                            </main>
                        }/>
                        <Route path="/natural-query" element={
                            <main
                                className="vf-body | vf-stack vf-stack--200"
                                style={{
                                    '--vf-body-width': '80em',
                                    paddingBottom: '200px',
                                } as React.CSSProperties}
                            >
                                <ConditionalNaturalQueryRoute />
                            </main>
                        } />
                    </Routes>
                    <Footer/>
                </Router>
            </div>
            </ReleaseProvider>
            </AuthProvider>
        </QueryClientProvider>
    );
};

export default App;
