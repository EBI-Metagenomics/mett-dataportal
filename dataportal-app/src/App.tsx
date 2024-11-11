import React from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import Header from './components/organisms/Header';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';
import ErrorBoundary from "@components/atoms/ErrorBoundary";

const App: React.FC = () => {
    return (
        <Router>
            <Header/>
            <main
                className="vf-body | vf-stack vf-stack--200"
                style={{'--vf-body-width': '80em'} as React.CSSProperties}
            >
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    {/* Route for gene and genome */}
                    <Route path="/gene-viewer/gene/:geneId/genome/:genomeId" element={<GeneViewerPage />} />
                    {/* Route for genome only */}
                    <Route path="/gene-viewer/genome/:genomeId" element={
                        <ErrorBoundary>
                            <GeneViewerPage />
                        </ErrorBoundary>
                    } />
                </Routes>
            </main>
            {/*<Footer />*/}
        </Router>
    );
};

export default App;
