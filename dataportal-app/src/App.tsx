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
        if (location.pathname.startsWith('/genome/')) {
            const searchParams = new URLSearchParams(location.search);
            const locusTag = searchParams.get('locus_tag');

            if (locusTag) {
                const newParams = new URLSearchParams();
                newParams.set('locus_tag', locusTag);

                const newUrl = `${location.pathname}?${newParams.toString()}`;
                window.history.replaceState({}, '', newUrl);
            }
        }
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
    return (
        <QueryClientProvider client={queryClient}>
            <div style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
                <Router basename={import.meta.env.VITE_BASENAME || '/'}>
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
        </QueryClientProvider>
    );
};

export default App;
