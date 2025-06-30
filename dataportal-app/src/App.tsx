import React from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Header from '@components/organisms/Header/Header';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';
import TestPage from './components/pages/TestPage';
import ErrorBoundary from "@components/atoms/ErrorBoundary";
import Footer from "@components/organisms/Footer/Footer";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App: React.FC = () => {
    return (
        <QueryClientProvider client={queryClient}>
            <div style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
                <Router basename={import.meta.env.VITE_BASENAME || '/'}>
                    <Header/>
                    <main
                        className="vf-body | vf-stack vf-stack--200"
                        style={{
                            '--vf-body-width': '80em',
                            paddingBottom: '200px',
                        } as React.CSSProperties}
                    >
                        <Routes>
                            <Route path="/" element={<HomePage/>}/>
                            <Route path="/home" element={<HomePage/>}/>
                            <Route path="/test" element={<TestPage/>}/>
                            <Route path="/genome/:strainName" element={
                                <ErrorBoundary>
                                    <GeneViewerPage/>
                                </ErrorBoundary>
                            }/>
                        </Routes>
                    </main>
                    <Footer/>
                </Router>
            </div>
        </QueryClientProvider>
    );
};

export default App;
